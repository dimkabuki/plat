from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_module_package import ModulePackageError, validate_module_package  # noqa: E402

VALID_MANIFEST = {
    "schemaVersion": 1,
    "id": "dev.plat.example.counter",
    "name": "Counter",
    "version": "1.0.0",
    "entry": "index.html",
    "platformApi": {"minVersion": "1.0.0"},
    "capabilities": {"required": [], "optional": ["storage.kv"]},
}


class ModulePackageValidationTests(unittest.TestCase):
    def make_package(self, entries: list[tuple[str, bytes, int | None]]) -> Path:
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content, mode in entries:
                info = zipfile.ZipInfo(name)
                info.compress_type = zipfile.ZIP_DEFLATED
                if mode is not None:
                    info.external_attr = mode << 16
                archive.writestr(info, content)
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def package(self, manifest: dict | bytes | str | None = None, extra: list[tuple[str, bytes, int | None]] | None = None) -> Path:
        if manifest is None:
            manifest_bytes = json.dumps(VALID_MANIFEST).encode("utf-8")
        elif isinstance(manifest, dict):
            manifest_bytes = json.dumps(manifest).encode("utf-8")
        elif isinstance(manifest, str):
            manifest_bytes = manifest.encode("utf-8")
        else:
            manifest_bytes = manifest
        entries = [("module.json", manifest_bytes, None), ("index.html", b"<!doctype html>", None)]
        if extra:
            entries.extend(extra)
        return self.make_package(entries)

    def test_accepts_valid_module_package(self) -> None:
        manifest = validate_module_package(self.package())
        self.assertEqual(manifest["id"], VALID_MANIFEST["id"])

    def test_accepts_committed_counter_example(self) -> None:
        fixture = ROOT / "contracts" / "examples" / "counter"
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(fixture / "module.json", "module.json")
            archive.write(fixture / "index.html", "index.html")
        self.addCleanup(path.unlink, missing_ok=True)
        manifest = validate_module_package(path)
        self.assertEqual(manifest["id"], "dev.plat.example.counter")

    def test_rejects_unsupported_manifest_version(self) -> None:
        manifest = dict(VALID_MANIFEST, schemaVersion=2)
        with self.assertRaisesRegex(ModulePackageError, "schemaVersion"):
            validate_module_package(self.package(manifest))

    def test_rejects_unknown_manifest_fields(self) -> None:
        manifest = dict(VALID_MANIFEST, permissions=["filesystem.all"])
        with self.assertRaisesRegex(ModulePackageError, "Additional properties are not allowed"):
            validate_module_package(self.package(manifest))

    def test_rejects_duplicate_json_keys(self) -> None:
        raw = '{"schemaVersion":1,"id":"dev.plat.counter","id":"dev.plat.other"}'
        with self.assertRaisesRegex(ModulePackageError, "duplicate JSON key"):
            validate_module_package(self.package(raw))

    def test_rejects_capability_declared_as_required_and_optional(self) -> None:
        manifest = dict(VALID_MANIFEST)
        manifest["capabilities"] = {"required": ["storage.kv"], "optional": ["storage.kv"]}
        with self.assertRaisesRegex(ModulePackageError, "both required and optional"):
            validate_module_package(self.package(manifest))

    def test_rejects_api_maximum_not_above_minimum(self) -> None:
        manifest = dict(VALID_MANIFEST)
        manifest["platformApi"] = {"minVersion": "1.2.0", "maxVersionExclusive": "1.2.0"}
        with self.assertRaisesRegex(ModulePackageError, "maxVersionExclusive"):
            validate_module_package(self.package(manifest))

    def test_rejects_missing_entry_file(self) -> None:
        manifest = dict(VALID_MANIFEST, entry="app/index.html")
        with self.assertRaisesRegex(ModulePackageError, "entry file does not exist"):
            validate_module_package(self.package(manifest))

    def test_rejects_path_traversal(self) -> None:
        with self.assertRaisesRegex(ModulePackageError, "unsafe archive path"):
            validate_module_package(self.package(extra=[("../outside.txt", b"x", None)]))

    def test_rejects_case_insensitive_duplicate_paths(self) -> None:
        with self.assertRaisesRegex(ModulePackageError, "duplicate archive path"):
            validate_module_package(self.package(extra=[("assets/Icon.png", b"a", None), ("assets/icon.png", b"b", None)]))

    def test_rejects_case_ambiguous_directory_names(self) -> None:
        with self.assertRaisesRegex(ModulePackageError, "case-ambiguous directory"):
            validate_module_package(self.package(extra=[("Assets/a.png", b"a", None), ("assets/b.png", b"b", None)]))

    def test_rejects_excessive_compression_ratio(self) -> None:
        with self.assertRaisesRegex(ModulePackageError, "compression ratio"):
            validate_module_package(self.package(extra=[("assets/repeated.txt", b"A" * 20_000, None)]))

    def test_rejects_symbolic_links(self) -> None:
        symlink_mode = 0o120777
        with self.assertRaisesRegex(ModulePackageError, "symbolic links"):
            validate_module_package(self.package(extra=[("assets/link", b"target", symlink_mode)]))

    def test_rejects_file_used_as_parent_directory(self) -> None:
        with self.assertRaisesRegex(ModulePackageError, "also used as a directory"):
            validate_module_package(self.package(extra=[("assets", b"file", None), ("assets/app.js", b"code", None)]))

    def test_rejects_non_utf8_manifest(self) -> None:
        with self.assertRaisesRegex(ModulePackageError, "must be UTF-8"):
            validate_module_package(self.package(b"\xff"))


if __name__ == "__main__":
    unittest.main()
