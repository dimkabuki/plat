#!/usr/bin/env python3
"""Validate Platform API v1 messages and capability authorization."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


class PlatformApiError(ValueError):
    """Raised when a Platform API message or authorization is invalid."""


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    return json.loads((ROOT / "contracts" / "platform-api-v1.schema.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, Any]:
    return json.loads((ROOT / "contracts" / "platform-capabilities-v1.json").read_text(encoding="utf-8"))


def _validate(schema: dict[str, Any], value: Any, label: str) -> None:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise PlatformApiError(f"{label} violation at {location}: {error.message}")


def validate_message(message: dict[str, Any]) -> str:
    schema = _load_schema()
    _validate(schema, message, "message")
    message_type = message["type"]
    if message_type == "request":
        method = message["method"]
        if method == "platform.negotiate":
            return message_type
        method_definition = _method_registry().get(method)
        if method_definition is None:
            raise PlatformApiError(f"unknown Platform API method: {method}")
        _validate(method_definition["params"], message["params"], f"{method} params")
    return message_type


def _method_registry() -> dict[str, dict[str, Any]]:
    registry = _load_registry()
    methods: dict[str, dict[str, Any]] = {}
    for capability, definition in registry["capabilities"].items():
        for method, method_definition in definition["methods"].items():
            if method_definition["requiredCapability"] != capability:
                raise RuntimeError(f"capability mapping mismatch for {method}")
            Draft202012Validator.check_schema(method_definition["params"])
            if method in methods:
                raise RuntimeError(f"duplicate Platform API method: {method}")
            methods[method] = method_definition
    return methods


def _capability_status(
    declared: dict[str, list[str]], host_capabilities: set[str], approved_capabilities: set[str]
) -> tuple[set[str], set[str], set[str]]:
    registry = _load_registry()["capabilities"]
    required = set(declared["required"])
    optional = set(declared["optional"])
    if required & optional:
        raise PlatformApiError("a capability cannot be both required and optional")
    unknown = (required | optional) - set(registry)
    if unknown:
        raise PlatformApiError(f"unknown capability: {', '.join(sorted(unknown))}")

    granted: set[str] = set()
    unavailable_required: set[str] = set()
    unavailable_optional: set[str] = set()
    for capability in required | optional:
        definition = registry[capability]
        available = capability in host_capabilities
        approved = definition["permission"] == "automatic" or capability in approved_capabilities
        if available and approved:
            granted.add(capability)
        elif capability in required:
            unavailable_required.add(capability)
        else:
            unavailable_optional.add(capability)
    return granted, unavailable_required, unavailable_optional


def _parse_api_version(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() or (len(part) > 1 and part.startswith("0")) for part in parts):
        raise PlatformApiError(f"invalid stable Platform API version: {value!r}")
    return tuple(int(part) for part in parts)


def evaluate_api_compatibility(
    host_api_version: str, minimum: str, maximum_exclusive: str | None = None
) -> bool:
    """Check a Host API version against a module's declared compatibility range."""
    host = _parse_api_version(host_api_version)
    lower = _parse_api_version(minimum)
    if host[0] != lower[0] or host < lower:
        return False
    if maximum_exclusive is not None:
        upper = _parse_api_version(maximum_exclusive)
        if upper[0] != lower[0] or upper <= lower:
            raise PlatformApiError("maxVersionExclusive must exceed minVersion and use the same major version")
        if host >= upper:
            return False
    return True


def negotiate_capabilities(
    declared: dict[str, list[str]],
    host_capabilities: set[str],
    approved_capabilities: set[str],
) -> dict[str, Any]:
    """Return capability grants. Required gaps make the negotiation incompatible."""
    granted, missing_required, unavailable_optional = _capability_status(
        declared, host_capabilities, approved_capabilities
    )
    return {
        "compatible": not missing_required,
        "grantedCapabilities": sorted(granted),
        "missingRequiredCapabilities": sorted(missing_required),
        "unavailableOptionalCapabilities": sorted(unavailable_optional),
    }


def authorize_method(
    method: str,
    declared: dict[str, list[str]],
    host_capabilities: set[str],
    approved_capabilities: set[str],
) -> str:
    """Enforce declaration, Host support, and consent on every method call."""
    method_definition = _method_registry().get(method)
    if method_definition is None:
        raise PlatformApiError(f"unknown Platform API method: {method}")
    capability = method_definition["requiredCapability"]
    required = set(declared["required"])
    optional = set(declared["optional"])
    if capability not in required | optional:
        raise PlatformApiError(f"capability not declared by module: {capability}")
    if capability not in host_capabilities:
        raise PlatformApiError(f"capability unavailable on this Host: {capability}")
    permission = _load_registry()["capabilities"][capability]["permission"]
    if permission == "user-consent" and capability not in approved_capabilities:
        raise PlatformApiError(f"permission denied for capability: {capability}")
    return capability


def validate_registry() -> None:
    registry = _load_registry()
    if registry.get("schemaVersion") != 1 or registry.get("platformApiVersion") != "1.0.0":
        raise PlatformApiError("unsupported capability registry version")
    if not registry.get("capabilities"):
        raise PlatformApiError("capability registry must not be empty")
    _method_registry()
    for capability, definition in registry["capabilities"].items():
        if definition.get("permission") not in {"automatic", "user-consent"}:
            raise PlatformApiError(f"invalid permission policy for capability: {capability}")


def main() -> int:
    Draft202012Validator.check_schema(_load_schema())
    validate_registry()
    print("Platform API v1 schema and capability registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
