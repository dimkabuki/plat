from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_host_adapter import (  # noqa: E402
    HostAdapterContractError,
    _load_json,
    validate_conformance_matrix,
    validate_host_descriptor,
)


class HostAdapterContractTests(unittest.TestCase):
    def test_conformance_matrix_contains_all_required_scenarios(self) -> None:
        validate_conformance_matrix()

    def test_android_descriptor_is_valid(self) -> None:
        validate_host_descriptor(_load_json("contracts/examples/host/android.json"))

    def test_browser_descriptor_is_valid(self) -> None:
        validate_host_descriptor(_load_json("contracts/examples/host/browser.json"))

    def test_rejects_host_advertising_unknown_capability(self) -> None:
        descriptor = _load_json("contracts/examples/host/android.json")
        descriptor["capabilities"].append("filesystem.root")
        with self.assertRaisesRegex(HostAdapterContractError, "unknown capabilities"):
            validate_host_descriptor(descriptor)

    def test_rejects_duplicate_capabilities(self) -> None:
        descriptor = _load_json("contracts/examples/host/android.json")
        descriptor["capabilities"].append("storage.kv")
        with self.assertRaises(HostAdapterContractError):
            validate_host_descriptor(descriptor)

    def test_rejects_unsupported_platform_api_version_format(self) -> None:
        descriptor = _load_json("contracts/examples/host/android.json")
        descriptor["platformApiVersion"] = "1.0"
        with self.assertRaises(HostAdapterContractError):
            validate_host_descriptor(descriptor)

    def test_rejects_unbounded_message_size(self) -> None:
        descriptor = _load_json("contracts/examples/host/android.json")
        descriptor["limits"]["maxMessageBytes"] = 50_000_000
        with self.assertRaises(HostAdapterContractError):
            validate_host_descriptor(descriptor)

    def test_rejects_unsupported_transport(self) -> None:
        descriptor = _load_json("contracts/examples/host/browser.json")
        descriptor["transport"] = "unrestricted-js-bridge"
        with self.assertRaises(HostAdapterContractError):
            validate_host_descriptor(descriptor)

    def test_rejects_missing_required_conformance_scenario(self) -> None:
        matrix = _load_json("contracts/host-adapter-conformance-v1.json")
        matrix["requiredScenarios"] = [item for item in matrix["requiredScenarios"] if item["id"] != "session-identity-binding"]
        with self.assertRaisesRegex(HostAdapterContractError, "missing scenarios"):
            validate_conformance_matrix(matrix)


if __name__ == "__main__":
    unittest.main()
