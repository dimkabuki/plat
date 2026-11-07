from __future__ import annotations

import json
import sys
import unittest
import uuid
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_webview_security import (  # noqa: E402
    WebViewBridgeSession,
    WebViewSecurityError,
    _load_json,
    validate_bridge_message,
    validate_conformance_matrix,
    validate_security_policy,
)

ORIGIN = "https://m-" + ("a" * 48) + ".modules.plat.invalid"
OTHER_ORIGIN = "https://m-" + ("b" * 48) + ".modules.plat.invalid"
HELLO_ID = "12345678-1234-4234-9234-123456789abc"
SESSION_ID = "22345678-1234-4234-9234-123456789abc"
REQUEST_ID = "32345678-1234-4234-9234-123456789abc"


class WebViewSecurityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = WebViewBridgeSession(
            "dev.plat.example.counter",
            "1.0.0",
            ORIGIN,
            session_id=SESSION_ID,
        )

    def hello(self) -> dict:
        return {"bridgeVersion": 1, "type": "hello", "helloId": HELLO_ID, "protocolVersion": 1}

    def request(self, params: dict | None = None) -> dict:
        return {
            "protocolVersion": 1,
            "type": "request",
            "id": REQUEST_ID,
            "method": "storage.kv.get",
            "params": params or {"key": "count"},
        }

    def bridge_request(self, *, session_id: str = SESSION_ID, params: dict | None = None) -> dict:
        return {
            "bridgeVersion": 1,
            "type": "message",
            "sessionId": session_id,
            "message": self.request(params),
        }

    def activate(self) -> None:
        ack = self.session.receive(self.hello(), source_origin=ORIGIN, is_main_frame=True)
        self.assertEqual(ack["type"], "helloAck")
        self.assertEqual(ack["sessionId"], SESSION_ID)

    def test_bridge_schema_and_security_policy_are_valid(self) -> None:
        Draft202012Validator.check_schema(_load_json("contracts/webview-bridge-v1.schema.json"))
        validate_security_policy()
        validate_conformance_matrix()

    def test_policy_origin_pattern_matches_the_module_origin(self) -> None:
        pattern = _load_json("contracts/webview-security-v1.json")["origin"]["hostPattern"]
        self.assertRegex(ORIGIN.removeprefix("https://"), pattern)
        self.assertNotRegex((ORIGIN + ".attacker.example").removeprefix("https://"), pattern)

    def test_handshake_binds_host_generated_session(self) -> None:
        ack = self.session.receive(self.hello(), source_origin=ORIGIN, is_main_frame=True)
        self.assertEqual(self.session.state, "active")
        self.assertEqual(ack["helloId"], HELLO_ID)
        self.assertEqual(ack["sessionId"], SESSION_ID)
        self.assertEqual(ack["maxMessageBytes"], 65536)

    def test_rejects_api_request_before_handshake(self) -> None:
        with self.assertRaisesRegex(WebViewSecurityError, "first module message must be hello"):
            self.session.receive(self.bridge_request(), source_origin=ORIGIN, is_main_frame=True)

    def test_rejects_spoofed_origin(self) -> None:
        with self.assertRaisesRegex(WebViewSecurityError, "source origin"):
            self.session.receive(self.hello(), source_origin=OTHER_ORIGIN, is_main_frame=True)

    def test_rejects_lookalike_origin(self) -> None:
        with self.assertRaises(WebViewSecurityError):
            self.session.receive(self.hello(), source_origin=ORIGIN + ".attacker.example", is_main_frame=True)

    def test_rejects_subframe_messages(self) -> None:
        with self.assertRaisesRegex(WebViewSecurityError, "subframes"):
            self.session.receive(self.hello(), source_origin=ORIGIN, is_main_frame=False)

    def test_accepts_platform_request_after_handshake(self) -> None:
        self.activate()
        self.assertEqual(
            self.session.receive(self.bridge_request(), source_origin=ORIGIN, is_main_frame=True),
            self.request(),
        )

    def test_rejects_stale_session_id(self) -> None:
        self.activate()
        with self.assertRaisesRegex(WebViewSecurityError, "stale or mismatched"):
            self.session.receive(
                self.bridge_request(session_id=str(uuid.uuid4())),
                source_origin=ORIGIN,
                is_main_frame=True,
            )

    def test_rejects_malformed_json(self) -> None:
        with self.assertRaisesRegex(WebViewSecurityError, "malformed bridge JSON"):
            self.session.receive("{", source_origin=ORIGIN, is_main_frame=True)

    def test_rejects_duplicate_json_keys(self) -> None:
        raw = (
            '{"bridgeVersion":1,"type":"hello","helloId":"' + HELLO_ID
            + '","helloId":"' + HELLO_ID + '","protocolVersion":1}'
        )
        with self.assertRaisesRegex(WebViewSecurityError, "duplicate JSON key"):
            self.session.receive(raw, source_origin=ORIGIN, is_main_frame=True)

    def test_rejects_message_over_byte_limit_before_parsing(self) -> None:
        with self.assertRaisesRegex(WebViewSecurityError, "65536 UTF-8 bytes"):
            self.session.receive(" " * 65537, source_origin=ORIGIN, is_main_frame=True)

    def test_counts_utf8_bytes_not_characters(self) -> None:
        raw = '{"padding":"' + ("é" * 33000) + '"}'
        with self.assertRaisesRegex(WebViewSecurityError, "65536 UTF-8 bytes"):
            validate_bridge_message(raw, direction="module-to-host")

    def test_rejects_response_sent_from_module(self) -> None:
        self.activate()
        response = {
            "protocolVersion": 1,
            "type": "response",
            "id": REQUEST_ID,
            "result": {"value": 1},
        }
        wrapper = {"bridgeVersion": 1, "type": "message", "sessionId": SESSION_ID, "message": response}
        with self.assertRaisesRegex(WebViewSecurityError, "request messages only"):
            self.session.receive(wrapper, source_origin=ORIGIN, is_main_frame=True)

    def test_rejects_client_selected_storage_namespace(self) -> None:
        self.activate()
        params = {"key": "count", "moduleId": "dev.attacker.other"}
        with self.assertRaisesRegex(WebViewSecurityError, "invalid Platform API message"):
            self.session.receive(
                self.bridge_request(params=params),
                source_origin=ORIGIN,
                is_main_frame=True,
            )

    def test_host_outbound_response_is_wrapped_with_active_session(self) -> None:
        self.activate()
        response = {
            "protocolVersion": 1,
            "type": "response",
            "id": REQUEST_ID,
            "result": {"value": 3},
        }
        wrapper = self.session.wrap_host_message(response)
        self.assertEqual(wrapper["sessionId"], SESSION_ID)
        self.assertEqual(wrapper["message"], response)

    def test_close_is_idempotent_and_rejects_late_messages(self) -> None:
        self.activate()
        self.session.close()
        self.session.close()
        with self.assertRaisesRegex(WebViewSecurityError, "closed"):
            self.session.receive(self.bridge_request(), source_origin=ORIGIN, is_main_frame=True)

    def test_rejects_non_uuidv4_session_ids(self) -> None:
        with self.assertRaisesRegex(WebViewSecurityError, "UUIDv4"):
            WebViewBridgeSession(
                "dev.plat.example.counter",
                "1.0.0",
                ORIGIN,
                session_id="12345678-1234-1234-9234-123456789abc",
            )


if __name__ == "__main__":
    unittest.main()
