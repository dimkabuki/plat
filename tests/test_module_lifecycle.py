from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from module_lifecycle import LifecycleError, ModuleRecord  # noqa: E402


class ModuleLifecycleTests(unittest.TestCase):
    def test_initial_install_commits_only_after_activation(self) -> None:
        record = ModuleRecord("dev.plat.example.counter")
        record.begin_install("1.0.0")
        for expected in ("verifying", "staging", "activating"):
            record.advance()
            self.assertEqual(record.operation.phase, expected)
            self.assertIsNone(record.active_version)
        record.commit_activation()
        self.assertEqual(record.active_version, "1.0.0")
        self.assertIsNone(record.previous_version)
        self.assertIsNone(record.operation)

    def test_operation_id_is_stable_across_phase_changes(self) -> None:
        record = ModuleRecord("dev.plat.example.counter")
        record.begin_install("1.0.0")
        operation_id = record.operation.operation_id
        record.advance()
        self.assertEqual(record.operation.operation_id, operation_id)
        self.assertEqual(record.to_dict()["operation"]["operationId"], operation_id)

    def test_update_preserves_active_version_until_atomic_commit(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        for _ in range(3):
            record.advance()
            self.assertEqual(record.active_version, "1.0.0")
        record.commit_activation()
        self.assertEqual(record.active_version, "1.1.0")
        self.assertEqual(record.previous_version, "1.0.0")

    def test_rejects_non_monotonic_update(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.2.0")
        with self.assertRaisesRegex(LifecycleError, "newer"):
            record.begin_update("1.1.9")

    def test_semver_prerelease_precedence_is_respected(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0-rc.2")
        record.begin_update("1.0.0-rc.10")
        self.assertEqual(record.operation.target_version, "1.0.0-rc.10")

    def test_failed_update_keeps_active_version_and_can_retry(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("2.0.0")
        record.advance()
        record.fail("download_failed")
        self.assertEqual(record.active_version, "1.0.0")
        self.assertIsNone(record.operation)
        self.assertEqual(record.last_failure.error_code, "download_failed")
        record.retry()
        self.assertEqual(record.operation.phase, "downloading")
        self.assertEqual(record.operation.target_version, "2.0.0")

    def test_install_can_be_cancelled_before_activation(self) -> None:
        record = ModuleRecord("dev.plat.example.counter")
        record.begin_install("1.0.0")
        record.advance()
        record.cancel()
        self.assertIsNone(record.active_version)
        self.assertIsNone(record.operation)

    def test_activation_waits_until_runtime_is_stopped(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        record.advance()
        record.advance()
        with self.assertRaisesRegex(LifecycleError, "runtime must be stopped"):
            record.advance(runtime_running=True)
        self.assertEqual(record.operation.phase, "staging")
        record.advance(runtime_running=False)
        self.assertEqual(record.operation.phase, "activating")

    def test_activation_cannot_be_cancelled(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        for _ in range(3):
            record.advance()
        with self.assertRaisesRegex(LifecycleError, "before activation"):
            record.cancel()

    def test_restart_finalizes_when_pointer_already_references_target(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        for _ in range(3):
            record.advance()
        record = ModuleRecord.from_dict(json.loads(json.dumps(record.to_dict())))
        result = record.recover_after_restart(active_pointer_version="1.1.0")
        self.assertEqual(result, "finalized_activation")
        self.assertEqual(record.active_version, "1.1.0")
        self.assertEqual(record.previous_version, "1.0.0")

    def test_restart_restores_source_when_pointer_was_not_switched(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        for _ in range(3):
            record.advance()
        record = ModuleRecord.from_dict(json.loads(json.dumps(record.to_dict())))
        result = record.recover_after_restart(active_pointer_version="1.0.0")
        self.assertEqual(result, "restored_source")
        self.assertEqual(record.active_version, "1.0.0")
        self.assertEqual(record.last_failure.error_code, "activation_interrupted")

    def test_restart_fails_closed_for_unknown_active_pointer(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        for _ in range(3):
            record.advance()
        restored = ModuleRecord.from_dict(json.loads(json.dumps(record.to_dict())))
        with self.assertRaisesRegex(LifecycleError, "neither activation source nor target"):
            restored.recover_after_restart(active_pointer_version="0.8.0")

    def test_failed_removal_can_be_retried(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_remove(runtime_running=False)
        record.fail("storage_busy")
        self.assertEqual(record.active_version, "1.0.0")
        record.retry()
        self.assertEqual(record.operation.kind, "remove")
        self.assertEqual(record.operation.phase, "removing")

    def test_restart_discards_pre_activation_staging(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        record.begin_update("1.1.0")
        record.advance()
        record = ModuleRecord.from_dict(json.loads(json.dumps(record.to_dict())))
        result = record.recover_after_restart(active_pointer_version="1.0.0")
        self.assertEqual(result, "discard_staging")
        self.assertEqual(record.active_version, "1.0.0")
        self.assertEqual(record.last_failure.error_code, "operation_interrupted")

    def test_disabled_state_is_persistent_and_independent_of_running_state(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0")
        with self.assertRaisesRegex(LifecycleError, "must be stopped"):
            record.set_disabled(True, runtime_running=True)
        record.set_disabled(True, runtime_running=False)
        self.assertTrue(record.to_dict()["disabled"])
        record.set_disabled(False, runtime_running=False)
        self.assertFalse(record.disabled)

    def test_removal_requires_stopped_runtime_and_clears_record(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="1.0.0", previous_version="0.9.0")
        with self.assertRaisesRegex(LifecycleError, "must be stopped"):
            record.begin_remove(runtime_running=True)
        record.begin_remove(runtime_running=False)
        self.assertEqual(record.active_version, "1.0.0")
        record.commit_removal()
        self.assertIsNone(record.active_version)
        self.assertIsNone(record.previous_version)
        self.assertFalse(record.disabled)

    def test_rollback_swaps_to_previous_known_good_version(self) -> None:
        record = ModuleRecord("dev.plat.example.counter", active_version="2.0.0", previous_version="1.0.0")
        with self.assertRaisesRegex(LifecycleError, "stopped before rollback"):
            record.begin_rollback(runtime_running=True)
        record.begin_rollback(runtime_running=False)
        record.commit_activation()
        self.assertEqual(record.active_version, "1.0.0")
        self.assertEqual(record.previous_version, "2.0.0")

    def test_rejects_concurrent_lifecycle_operations(self) -> None:
        record = ModuleRecord("dev.plat.example.counter")
        record.begin_install("1.0.0")
        with self.assertRaisesRegex(LifecycleError, "already in progress"):
            record.begin_install("1.1.0")

    def test_rejects_invalid_persisted_operation(self) -> None:
        payload = ModuleRecord("dev.plat.example.counter").to_dict()
        payload["operation"] = {
            "operationId": "not-an-operation-id",
            "kind": "install",
            "phase": "downloading",
            "sourceVersion": None,
            "targetVersion": "1.0.0",
        }
        with self.assertRaisesRegex(LifecycleError, "operation ID"):
            ModuleRecord.from_dict(payload)

    def test_rejects_invalid_record_shape(self) -> None:
        schema = json.loads((ROOT / "contracts" / "module-record.schema.json").read_text(encoding="utf-8"))
        record = ModuleRecord("dev.plat.example.counter").to_dict()
        Draft202012Validator(schema).validate(record)
        record_with_operation = ModuleRecord("dev.plat.example.counter")
        record_with_operation.begin_install("1.0.0")
        Draft202012Validator(schema).validate(record_with_operation.to_dict())
        record["unexpected"] = True
        from jsonschema.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(record)


if __name__ == "__main__":
    unittest.main()
