#!/usr/bin/env python3
"""Validate Host Adapter descriptors and the shared v1 conformance matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SCENARIOS = {
    "descriptor-valid",
    "api-version-compatible",
    "required-capability-missing",
    "optional-capability-missing",
    "request-correlation",
    "structured-error",
    "event-envelope",
    "session-identity-binding",
    "per-call-authorization",
    "session-storage-isolation",
    "consent-revocation",
    "message-size-limit",
    "request-timeout",
    "close-idempotent",
}


class HostAdapterContractError(ValueError):
    """Raised when a Host Adapter contract artifact is invalid."""


def _load_json(path: str) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HostAdapterContractError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HostAdapterContractError(f"{path} must contain a JSON object")
    return value


def validate_host_descriptor(descriptor: dict[str, Any]) -> None:
    schema = _load_json("contracts/host-adapter-v1.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(descriptor),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.absolute_path) or "$"
        raise HostAdapterContractError(f"Host descriptor violation at {where}: {error.message}")

    registry = _load_json("contracts/platform-capabilities-v1.json")["capabilities"]
    unknown = set(descriptor["capabilities"]) - set(registry)
    if unknown:
        raise HostAdapterContractError(f"Host advertises unknown capabilities: {', '.join(sorted(unknown))}")


def validate_conformance_matrix(matrix: dict[str, Any] | None = None) -> None:
    if matrix is None:
        matrix = _load_json("contracts/host-adapter-conformance-v1.json")
    if matrix.get("schemaVersion") != 1 or matrix.get("platformApiVersion") != "1.0.0":
        raise HostAdapterContractError("unsupported Host Adapter conformance matrix version")
    scenarios = matrix.get("requiredScenarios")
    if not isinstance(scenarios, list):
        raise HostAdapterContractError("requiredScenarios must be an array")
    ids = [item.get("id") for item in scenarios if isinstance(item, dict)]
    if len(ids) != len(scenarios) or len(ids) != len(set(ids)):
        raise HostAdapterContractError("conformance scenario IDs must be objects with unique IDs")
    missing = REQUIRED_SCENARIOS - set(ids)
    if missing:
        raise HostAdapterContractError(f"conformance matrix is missing scenarios: {', '.join(sorted(missing))}")


def main() -> int:
    validate_conformance_matrix()
    for name in ("android", "browser"):
        descriptor = _load_json(f"contracts/examples/host/{name}.json")
        validate_host_descriptor(descriptor)
    print("Host Adapter v1 descriptors and conformance matrix validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
