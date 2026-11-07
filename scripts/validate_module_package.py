#!/usr/bin/env python3
"""Validate a PLAT v1 module ZIP against its schema and archive rules."""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
import unicodedata
import zipfile
import zlib
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_ENTRIES = 1000
MAX_TOTAL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_FILE_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_COMPRESSION_RATIO = 100
SUPPORTED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
API_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


class ModulePackageError(ValueError):
    """Raised when a module archive violates the v1 package contract."""


@lru_cache(maxsize=1)
def _manifest_validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[1] / "contracts" / "module-manifest.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
        raise RuntimeError(f"cannot load a valid module manifest schema at {schema_path}: {exc}") from exc
    return Draft202012Validator(schema)


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ModulePackageError(f"manifest contains duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json_object(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ModulePackageError("module.json must be UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except json.JSONDecodeError as exc:
        raise ModulePackageError(f"module.json is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ModulePackageError("module.json must contain a JSON object")
    return value


def _validate_manifest_path(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise ModulePackageError(f"{where} must be a non-empty relative package path of at most 240 characters")
    if "\\" in value or "\x00" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ModulePackageError(f"{where} must be a POSIX-relative path")
    if unicodedata.normalize("NFC", value) != value:
        raise ModulePackageError(f"{where} must use Unicode NFC normalization")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or any(":" in part for part in parts):
        raise ModulePackageError(f"{where} contains an unsafe path segment")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value):
        raise ModulePackageError(f"{where} contains unsupported path characters")
    return value


def _parse_api_version(value: str, where: str) -> tuple[int, int, int]:
    match = API_VERSION_RE.fullmatch(value)
    if not match:
        raise ModulePackageError(f"{where} must be a stable x.y.z version string")
    return tuple(int(part) for part in match.groups())


def validate_manifest(manifest: dict[str, Any]) -> None:
    errors = sorted(
        _manifest_validator().iter_errors(manifest),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise ModulePackageError(f"manifest schema violation at {location}: {error.message}")

    _validate_manifest_path(manifest["entry"], "entry")
    platform_api = manifest["platformApi"]
    minimum = _parse_api_version(platform_api["minVersion"], "platformApi.minVersion")
    maximum_value = platform_api.get("maxVersionExclusive")
    if maximum_value is not None:
        maximum = _parse_api_version(maximum_value, "platformApi.maxVersionExclusive")
        if maximum[0] != minimum[0] or maximum <= minimum:
            raise ModulePackageError("platformApi.maxVersionExclusive must be greater than minVersion and use the same major version")

    required = set(manifest["capabilities"]["required"])
    optional = set(manifest["capabilities"]["optional"])
    overlap = required & optional
    if overlap:
        raise ModulePackageError(f"capability cannot be both required and optional: {', '.join(sorted(overlap))}")


def _safe_archive_name(info: zipfile.ZipInfo) -> tuple[str, str, bool]:
    raw = info.filename
    if not raw or "\x00" in raw or "\\" in raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ModulePackageError(f"unsafe archive path: {raw!r}")
    if unicodedata.normalize("NFC", raw) != raw:
        raise ModulePackageError(f"archive path must use Unicode NFC normalization: {raw!r}")

    is_directory = info.is_dir()
    path_value = raw[:-1] if is_directory and raw.endswith("/") else raw
    parts = path_value.split("/")
    if not path_value or any(part in {"", ".", ".."} for part in parts) or any(":" in part for part in parts):
        raise ModulePackageError(f"unsafe archive path segment: {raw!r}")
    if len(raw.encode("utf-8")) > 240:
        raise ModulePackageError(f"archive path exceeds 240 UTF-8 bytes: {raw!r}")

    mode = (info.external_attr >> 16) & 0xFFFF
    kind = stat.S_IFMT(mode)
    if kind == stat.S_IFLNK:
        raise ModulePackageError(f"symbolic links are not allowed: {raw!r}")
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise ModulePackageError(f"special filesystem entries are not allowed: {raw!r}")
    if is_directory and (kind == stat.S_IFREG or info.file_size != 0):
        raise ModulePackageError(f"invalid directory entry: {raw!r}")
    if not is_directory and kind == stat.S_IFDIR:
        raise ModulePackageError(f"file entry has directory mode: {raw!r}")

    return path_value, path_value.casefold(), is_directory


def validate_module_package(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ModulePackageError(f"package does not exist or is not a regular file: {path}")
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ModulePackageError("archive exceeds the 50 MiB compressed-size limit")

    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ModulePackageError(f"package is not a readable ZIP archive: {exc}") from exc

    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ModulePackageError(f"archive contains more than {MAX_ENTRIES} entries")
        if not infos:
            raise ModulePackageError("archive is empty")

        files: set[str] = set()
        canonical_names: set[str] = set()
        canonical_prefixes: dict[str, str] = {}
        manifest_bytes: bytes | None = None
        total_size = 0

        for info in infos:
            name, canonical, is_directory = _safe_archive_name(info)
            if canonical in canonical_names:
                raise ModulePackageError(f"duplicate archive path (case-insensitive): {name}")
            canonical_names.add(canonical)
            segments = name.split("/")
            for index in range(1, len(segments) + 1):
                original_prefix = "/".join(segments[:index])
                canonical_prefix = original_prefix.casefold()
                previous_prefix = canonical_prefixes.setdefault(canonical_prefix, original_prefix)
                if previous_prefix != original_prefix:
                    raise ModulePackageError(
                        f"archive paths use case-ambiguous directory names: {previous_prefix!r} and {original_prefix!r}"
                    )

            if info.flag_bits & 0x1:
                raise ModulePackageError(f"encrypted archive entries are not supported: {name}")
            if info.compress_type not in SUPPORTED_COMPRESSION:
                raise ModulePackageError(f"unsupported compression method for {name}")
            if info.file_size > MAX_FILE_UNCOMPRESSED_BYTES:
                raise ModulePackageError(f"archive entry exceeds the 50 MiB uncompressed-size limit: {name}")
            if name == "module.json" and info.file_size > MAX_MANIFEST_BYTES:
                raise ModulePackageError("module.json exceeds the 64 KiB limit")
            total_size += info.file_size
            if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise ModulePackageError("archive exceeds the 100 MiB total uncompressed-size limit")
            if info.file_size and not info.compress_size:
                raise ModulePackageError(f"invalid compressed size for {name}")
            if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                raise ModulePackageError(f"compression ratio exceeds {MAX_COMPRESSION_RATIO}:1 for {name}")
            if is_directory:
                continue

            files.add(name)
            content = bytearray()
            try:
                with archive.open(info, "r") as entry:
                    while chunk := entry.read(64 * 1024):
                        content.extend(chunk)
                        if len(content) > MAX_FILE_UNCOMPRESSED_BYTES:
                            raise ModulePackageError(f"archive entry expands beyond the size limit: {name}")
            except (OSError, RuntimeError, zipfile.BadZipFile, EOFError, zlib.error) as exc:
                raise ModulePackageError(f"cannot read archive entry {name}: {exc}") from exc
            if len(content) != info.file_size:
                raise ModulePackageError(f"archive entry size does not match its directory record: {name}")
            if name == "module.json":
                manifest_bytes = bytes(content)

        for file_name in files:
            parents = PurePosixPath(file_name).parents
            if any(parent.as_posix() in files for parent in parents if parent.as_posix() != "."):
                raise ModulePackageError(f"file path is also used as a directory: {file_name}")

        if manifest_bytes is None:
            raise ModulePackageError("archive must contain module.json at its root")
        manifest = _parse_json_object(manifest_bytes)
        validate_manifest(manifest)
        if manifest["entry"] not in files:
            raise ModulePackageError(f"entry file does not exist in archive: {manifest['entry']}")
        return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="path to a module ZIP archive")
    args = parser.parse_args()
    try:
        manifest = validate_module_package(args.package)
    except ModulePackageError as exc:
        print(f"Invalid module package: {exc}", file=sys.stderr)
        return 1
    print(f"Valid PLAT module package: {manifest['id']}@{manifest['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
