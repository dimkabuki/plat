#!/usr/bin/env python3
"""Validate the Android WebView security and bridge v1 contracts."""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

from validate_platform_api import PlatformApiError, validate_message

ROOT = Path(__file__).resolve().parents[1]
MAX_MESSAGE_BYTES = 65536
REQUEST_TIMEOUT_MS = 15000
MODULE_ORIGIN_RE = re.compile(r"^https://m-[0-9a-f]{48}\.modules\.plat\.invalid$")
REQUIRED_SCENARIOS = {
    "origin-per-module",
    "origin-spoofed",
    "subframe-message",
    "handshake-required",
    "stale-session",
    "malformed-json",
    "message-size-limit",
    "direction-confusion",
    "module-id-spoofing",
    "cross-module-storage",
    "javascript-interface-absent",
    "unsupported-transport-feature",
    "navigation-restricted",
    "file-and-content-access-disabled",
    "remote-code-blocked",
    "capability-rechecked",
    "session-teardown",
}


class WebViewSecurityError(ValueError):
    """Raised when a WebView bridge message violates the v1 contract."""


def _load_json(path: str) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WebViewSecurityError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WebViewSecurityError(f"{path} must contain a JSON object")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WebViewSecurityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise WebViewSecurityError(f"non-JSON numeric constant is not allowed: {value}")


def _parse_message(raw: str | bytes | dict[str, Any]) -> tuple[dict[str, Any], int]:
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WebViewSecurityError("bridge message must be UTF-8") from exc
    elif isinstance(raw, str):
        text = raw
    elif isinstance(raw, dict):
        try:
            text = json.dumps(raw, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise WebViewSecurityError(f"bridge message is not JSON serializable: {exc}") from exc
    else:
        raise WebViewSecurityError("bridge message must be UTF-8 JSON")

    size = len(text.encode("utf-8"))
    if size > MAX_MESSAGE_BYTES:
        raise WebViewSecurityError(f"bridge message exceeds {MAX_MESSAGE_BYTES} UTF-8 bytes")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise WebViewSecurityError(f"malformed bridge JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise WebViewSecurityError("bridge message must contain a JSON object")
    return value, size


def _validate_schema(value: dict[str, Any]) -> None:
    schema = _load_json("contracts/webview-bridge-v1.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.absolute_path) or "$"
        raise WebViewSecurityError(f"bridge schema violation at {where}: {error.message}")


def validate_bridge_message(
    raw: str | bytes | dict[str, Any],
    *,
    direction: str,
    expected_session_id: str | None = None,
) -> dict[str, Any]:
    if direction not in {"module-to-host", "host-to-module"}:
        raise WebViewSecurityError(f"unsupported bridge direction: {direction}")
    value, _ = _parse_message(raw)
    _validate_schema(value)
    message_type = value["type"]

    if message_type == "hello":
        if direction != "module-to-host":
            raise WebViewSecurityError("hello is valid only from module to Host")
        return value
    if message_type == "helloAck":
        if direction != "host-to-module":
            raise WebViewSecurityError("helloAck is valid only from Host to module")
        return value

    if expected_session_id is None:
        raise WebViewSecurityError("an active Host session is required")
    if value["sessionId"] != expected_session_id:
        raise WebViewSecurityError("stale or mismatched bridge session")

    try:
        api_type = validate_message(value["message"])
    except PlatformApiError as exc:
        raise WebViewSecurityError(f"invalid Platform API message: {exc}") from exc

    if direction == "module-to-host" and api_type != "request":
        raise WebViewSecurityError("module may send request messages only")
    if direction == "host-to-module" and api_type not in {"response", "event"}:
        raise WebViewSecurityError("Host may send response or event messages only")
    return value


def _validate_module_origin(origin: str) -> str:
    if not isinstance(origin, str) or not MODULE_ORIGIN_RE.fullmatch(origin):
        raise WebViewSecurityError("module origin must match the exact reserved HTTPS origin format")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
        raise WebViewSecurityError("module origin must be a bare HTTPS origin")
    if parsed.username is not None or parsed.password is not None or parsed.port is not None:
        raise WebViewSecurityError("module origin must not contain credentials or an explicit port")
    return origin


class WebViewBridgeSession:
    """Reference model for origin-bound handshake, session IDs, and teardown.

    This is a contract test model, not an Android WebView implementation.
    """

    def __init__(
        self,
        module_id: str,
        module_version: str,
        module_origin: str,
        *,
        session_id: str | None = None,
    ) -> None:
        self.module_id = module_id
        self.module_version = module_version
        self.expected_origin = _validate_module_origin(module_origin)
        self.session_id = session_id or str(uuid.uuid4())
        try:
            parsed_session = uuid.UUID(self.session_id)
        except (ValueError, AttributeError) as exc:
            raise WebViewSecurityError("session ID must be a UUID") from exc
        if parsed_session.version != 4:
            raise WebViewSecurityError("session ID must be a Host-generated UUIDv4")
        self.state = "pending"
        self.hello_id: str | None = None

    def receive(
        self,
        raw_message: str | bytes | dict[str, Any],
        *,
        source_origin: str,
        is_main_frame: bool,
    ) -> dict[str, Any]:
        if self.state == "closed":
            raise WebViewSecurityError("bridge session is closed")
        if not is_main_frame:
            raise WebViewSecurityError("messages from subframes are not accepted")
        if source_origin != self.expected_origin:
            raise WebViewSecurityError("message source origin does not match the active module origin")

        if self.state == "pending":
            pending_value, _ = _parse_message(raw_message)
            _validate_schema(pending_value)
            if pending_value.get("type") != "hello":
                raise WebViewSecurityError("the first module message must be hello")
            value = validate_bridge_message(pending_value, direction="module-to-host")
            self.hello_id = value["helloId"]
            self.state = "active"
            return {
                "bridgeVersion": 1,
                "type": "helloAck",
                "helloId": self.hello_id,
                "sessionId": self.session_id,
                "maxMessageBytes": MAX_MESSAGE_BYTES,
                "requestTimeoutMs": REQUEST_TIMEOUT_MS,
            }

        value = validate_bridge_message(
            raw_message,
            direction="module-to-host",
            expected_session_id=self.session_id,
        )
        if value["type"] != "message":
            raise WebViewSecurityError("hello is valid only once at the start of a session")
        return value["message"]

    def wrap_host_message(self, message: dict[str, Any]) -> dict[str, Any]:
        if self.state != "active":
            raise WebViewSecurityError("bridge session is not active")
        value = {
            "bridgeVersion": 1,
            "type": "message",
            "sessionId": self.session_id,
            "message": message,
        }
        return validate_bridge_message(
            value,
            direction="host-to-module",
            expected_session_id=self.session_id,
        )

    def close(self) -> None:
        self.state = "closed"


def validate_security_policy() -> None:
    policy = _load_json("contracts/webview-security-v1.json")
    if policy.get("schemaVersion") != 1 or policy.get("platformApiVersion") != "1.0.0":
        raise WebViewSecurityError("unsupported WebView security policy version")
    origin = policy.get("origin", {})
    if origin.get("scheme") != "https" or origin.get("assetLoader") != "androidx.webkit.WebViewAssetLoader":
        raise WebViewSecurityError("module content must use HTTPS WebViewAssetLoader origins")
    if origin.get("hostPattern") != r"^m-[0-9a-f]{48}\.modules\.plat\.invalid$":
        raise WebViewSecurityError("module origin must be unique and hash-derived")
    transport = policy.get("transport", {})
    if transport.get("implementation") != "androidx.webkit.WebViewCompat.addWebMessageListener":
        raise WebViewSecurityError("WebMessageListener is the required bridge transport")
    if transport.get("mainFrameOnly") is not True or transport.get("javascriptInterface") is not False:
        raise WebViewSecurityError("bridge must be main-frame-only and must not expose a JavaScript interface")
    if transport.get("fallbackWhenUnsupported") != "refuse module launch; do not fall back to addJavascriptInterface or an unrestricted postMessage receiver":
        raise WebViewSecurityError("unsupported bridge feature must fail closed")
    limits = policy.get("limits", {})
    if limits.get("maxMessageBytes") != MAX_MESSAGE_BYTES or limits.get("requestTimeoutMs") != REQUEST_TIMEOUT_MS:
        raise WebViewSecurityError("WebView bridge limits do not match the v1 transport schema")
    settings = policy.get("webViewSettings", {})
    required_false = (
        "allowFileAccess", "allowContentAccess", "allowFileAccessFromFileURLs",
        "allowUniversalAccessFromFileURLs", "supportMultipleWindows",
        "thirdPartyCookies", "allowJavaScriptInterface",
    )
    if any(settings.get(key) is not False for key in required_false):
        raise WebViewSecurityError("unsafe WebView setting must remain disabled")
    if settings.get("mixedContentMode") != "never-allow" or settings.get("safeBrowsingEnabled") is not True:
        raise WebViewSecurityError("mixed content must be blocked and Safe Browsing enabled")
    csp = policy.get("contentSecurityPolicy", "")
    for directive in ("default-src 'self'", "script-src 'self'", "connect-src 'self'", "frame-src 'none'", "object-src 'none'", "worker-src 'none'"):
        if directive not in csp:
            raise WebViewSecurityError(f"missing CSP directive: {directive}")
    if "'unsafe-eval'" in csp or "https:" in csp:
        raise WebViewSecurityError("CSP must not allow eval or unrestricted remote resources")


def validate_conformance_matrix() -> None:
    matrix = _load_json("contracts/webview-security-conformance-v1.json")
    if matrix.get("schemaVersion") != 1 or matrix.get("bridgeContractVersion") != "1.0.0":
        raise WebViewSecurityError("unsupported WebView security conformance matrix version")
    scenarios = matrix.get("requiredScenarios")
    if not isinstance(scenarios, list):
        raise WebViewSecurityError("requiredScenarios must be an array")
    ids = [item.get("id") for item in scenarios if isinstance(item, dict)]
    if len(ids) != len(scenarios) or len(ids) != len(set(ids)):
        raise WebViewSecurityError("security scenario IDs must be objects with unique IDs")
    missing = REQUIRED_SCENARIOS - set(ids)
    if missing:
        raise WebViewSecurityError(f"security matrix is missing scenarios: {', '.join(sorted(missing))}")


def main() -> int:
    try:
        bridge_schema = _load_json("contracts/webview-bridge-v1.schema.json")
        Draft202012Validator.check_schema(bridge_schema)
        validate_security_policy()
        validate_conformance_matrix()
    except WebViewSecurityError as exc:
        print(f"Invalid WebView security contract: {exc}", file=sys.stderr)
        return 1
    print("WebView security v1 policy, bridge schema, and conformance matrix validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
