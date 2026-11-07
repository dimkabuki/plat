from __future__ import annotations

import json
import sys
import unittest
import uuid
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_platform_api import (
    PlatformApiError,
    authorize_method,
    evaluate_api_compatibility,
    negotiate_capabilities,
    validate_message,
    validate_registry,
)  # noqa: E402

REQUEST_ID = str(uuid.UUID("12345678-1234-4234-9234-123456789abc"))


class PlatformApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((ROOT / "contracts" / "platform-api-v1.schema.json").read_text(encoding="utf-8"))

    def request(self, method: str = "storage.kv.get", params: dict | None = None) -> dict:
        return {"protocolVersion": 1, "type": "request", "id": REQUEST_ID, "method": method, "params": params or {}}

    def test_schema_and_registry_are_valid(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        validate_registry()

    def test_accepts_request_envelope(self) -> None:
        self.assertEqual(validate_message(self.request("storage.kv.get", {"key": "count"})), "request")

    def test_accepts_success_response(self) -> None:
        message = {"protocolVersion": 1, "type": "response", "id": REQUEST_ID, "result": {"value": 2}}
        self.assertEqual(validate_message(message), "response")

    def test_accepts_error_response(self) -> None:
        message = {"protocolVersion": 1, "type": "response", "id": REQUEST_ID, "error": {"code": "NOT_FOUND", "message": "Key does not exist", "retryable": False}}
        self.assertEqual(validate_message(message), "response")

    def test_rejects_response_with_result_and_error(self) -> None:
        message = {"protocolVersion": 1, "type": "response", "id": REQUEST_ID, "result": {}, "error": {"code": "NOT_FOUND", "message": "missing", "retryable": False}}
        with self.assertRaises(PlatformApiError):
            validate_message(message)

    def test_accepts_event_envelope(self) -> None:
        message = {"protocolVersion": 1, "type": "event", "eventId": REQUEST_ID, "event": "runtime.lifecycle.changed", "payload": {"state": "running"}}
        self.assertEqual(validate_message(message), "event")

    def test_rejects_unsupported_protocol_version(self) -> None:
        message = self.request()
        message["protocolVersion"] = 2
        with self.assertRaisesRegex(PlatformApiError, "protocolVersion"):
            validate_message(message)

    def test_rejects_unknown_envelope_fields(self) -> None:
        message = self.request()
        message["moduleId"] = "dev.plat.example.counter"
        with self.assertRaises(PlatformApiError):
            validate_message(message)

    def test_rejects_invalid_correlation_id(self) -> None:
        message = self.request()
        message["id"] = "not-a-uuid"
        with self.assertRaises(PlatformApiError):
            validate_message(message)

    def test_rejects_unknown_method(self) -> None:
        with self.assertRaisesRegex(PlatformApiError, "unknown Platform API method"):
            validate_message(self.request("storage.kv.drop", {"key": "x"}))

    def test_validates_method_parameters(self) -> None:
        with self.assertRaisesRegex(PlatformApiError, "params"):
            validate_message(self.request("storage.kv.get", {}))

    def test_validates_negotiate_request_shape(self) -> None:
        params = {
            "module": {"id": "dev.plat.example.counter", "manifestSchemaVersion": 1},
            "api": {"minVersion": "1.0.0"},
            "capabilities": {"required": ["storage.kv"], "optional": ["notifications.local"]},
        }
        self.assertEqual(validate_message(self.request("platform.negotiate", params)), "request")

    def test_api_compatibility_accepts_host_inside_declared_range(self) -> None:
        self.assertTrue(evaluate_api_compatibility("1.2.0", "1.0.0", "1.9.0"))

    def test_api_compatibility_rejects_host_below_minimum(self) -> None:
        self.assertFalse(evaluate_api_compatibility("1.0.0", "1.1.0"))

    def test_api_compatibility_rejects_host_at_exclusive_maximum(self) -> None:
        self.assertFalse(evaluate_api_compatibility("1.9.0", "1.0.0", "1.9.0"))

    def test_api_compatibility_rejects_major_version_mismatch(self) -> None:
        self.assertFalse(evaluate_api_compatibility("2.0.0", "1.0.0"))

    def test_api_compatibility_rejects_invalid_range(self) -> None:
        with self.assertRaisesRegex(PlatformApiError, "must exceed"):
            evaluate_api_compatibility("1.2.0", "1.0.0", "1.0.0")

    def test_negotiation_grants_automatic_and_approved_capabilities(self) -> None:
        declared = {"required": ["storage.kv"], "optional": ["notifications.local"]}
        result = negotiate_capabilities(declared, {"storage.kv", "notifications.local"}, {"notifications.local"})
        self.assertTrue(result["compatible"])
        self.assertEqual(result["grantedCapabilities"], ["notifications.local", "storage.kv"])
        self.assertEqual(result["unavailableOptionalCapabilities"], [])

    def test_missing_required_host_capability_blocks_compatibility(self) -> None:
        result = negotiate_capabilities({"required": ["storage.kv"], "optional": []}, set(), set())
        self.assertFalse(result["compatible"])
        self.assertEqual(result["missingRequiredCapabilities"], ["storage.kv"])

    def test_missing_optional_consent_does_not_block_compatibility(self) -> None:
        declared = {"required": ["storage.kv"], "optional": ["notifications.local"]}
        result = negotiate_capabilities(declared, {"storage.kv", "notifications.local"}, set())
        self.assertTrue(result["compatible"])
        self.assertEqual(result["unavailableOptionalCapabilities"], ["notifications.local"])

    def test_rejects_capability_not_in_registry(self) -> None:
        with self.assertRaisesRegex(PlatformApiError, "unknown capability"):
            negotiate_capabilities({"required": ["filesystem.all"], "optional": []}, set(), set())

    def test_rejects_required_and_optional_overlap(self) -> None:
        declared = {"required": ["storage.kv"], "optional": ["storage.kv"]}
        with self.assertRaisesRegex(PlatformApiError, "both required and optional"):
            negotiate_capabilities(declared, {"storage.kv"}, set())

    def test_authorization_requires_manifest_declaration(self) -> None:
        declared = {"required": [], "optional": []}
        with self.assertRaisesRegex(PlatformApiError, "not declared"):
            authorize_method("storage.kv.get", declared, {"storage.kv"}, set())

    def test_authorization_requires_host_capability(self) -> None:
        declared = {"required": ["storage.kv"], "optional": []}
        with self.assertRaisesRegex(PlatformApiError, "unavailable"):
            authorize_method("storage.kv.get", declared, set(), set())

    def test_authorization_requires_user_consent(self) -> None:
        declared = {"required": [], "optional": ["notifications.local"]}
        with self.assertRaisesRegex(PlatformApiError, "permission denied"):
            authorize_method("notifications.local.cancel", declared, {"notifications.local"}, set())

    def test_authorization_allows_declared_supported_and_approved_method(self) -> None:
        declared = {"required": [], "optional": ["notifications.local"]}
        capability = authorize_method("notifications.local.cancel", declared, {"notifications.local"}, {"notifications.local"})
        self.assertEqual(capability, "notifications.local")


if __name__ == "__main__":
    unittest.main()
