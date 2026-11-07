#!/usr/bin/env python3
"""Reference state machine for the PLAT module installation lifecycle.

This is a contract model, not the Android storage or runtime implementation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4


class LifecycleError(ValueError):
    """Raised when a lifecycle command violates the contract."""


OperationKind = Literal["install", "update", "rollback", "remove"]
OperationPhase = Literal["downloading", "verifying", "staging", "activating", "removing"]

_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_ERROR_CODE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


def _parse_semver(version: str) -> tuple[tuple[int, int, int], tuple[str, ...] | None]:
    match = _SEMVER.fullmatch(version)
    if not match:
        raise LifecycleError(f"invalid SemVer version: {version!r}")
    core = tuple(int(part) for part in match.groups()[:3])
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else None
    return core, prerelease


def _compare_semver(left: str, right: str) -> int:
    left_core, left_pre = _parse_semver(left)
    right_core, right_pre = _parse_semver(right)
    if left_core != right_core:
        return (left_core > right_core) - (left_core < right_core)
    if left_pre is None:
        return 0 if right_pre is None else 1
    if right_pre is None:
        return -1
    for left_part, right_part in zip(left_pre, right_pre):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            return (int(left_part) > int(right_part)) - (int(left_part) < int(right_part))
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return (left_part > right_part) - (left_part < right_part)
    return (len(left_pre) > len(right_pre)) - (len(left_pre) < len(right_pre))


@dataclass(frozen=True)
class Operation:
    operation_id: str
    kind: OperationKind
    phase: OperationPhase
    source_version: str | None
    target_version: str | None


@dataclass(frozen=True)
class Failure:
    kind: OperationKind
    phase: OperationPhase
    error_code: str
    target_version: str | None


@dataclass
class ModuleRecord:
    """Durable module record; runtime process state is deliberately not stored here."""

    module_id: str
    active_version: str | None = None
    previous_version: str | None = None
    disabled: bool = False
    operation: Operation | None = None
    last_failure: Failure | None = None

    def _ensure_idle(self) -> None:
        if self.operation is not None:
            raise LifecycleError("another lifecycle operation is already in progress")

    def _begin(self, kind: OperationKind, phase: OperationPhase, target: str | None) -> None:
        self._ensure_idle()
        self.operation = Operation(uuid4().hex, kind, phase, self.active_version, target)
        self.last_failure = None

    def begin_install(self, target_version: str) -> None:
        self._ensure_idle()
        if self.active_version is not None:
            raise LifecycleError("install requires a module that is not installed")
        _parse_semver(target_version)
        self._begin("install", "downloading", target_version)

    def begin_update(self, target_version: str) -> None:
        self._ensure_idle()
        if self.active_version is None:
            raise LifecycleError("update requires an installed module")
        _parse_semver(target_version)
        if _compare_semver(target_version, self.active_version) <= 0:
            raise LifecycleError("update target must be newer than the active version")
        self._begin("update", "downloading", target_version)

    def begin_rollback(self, *, runtime_running: bool = False) -> None:
        self._ensure_idle()
        if runtime_running:
            raise LifecycleError("module runtime must be stopped before rollback activation")
        if self.active_version is None or self.previous_version is None:
            raise LifecycleError("rollback requires both active and previous known-good versions")
        self._begin("rollback", "activating", self.previous_version)

    def begin_remove(self, *, runtime_running: bool) -> None:
        self._ensure_idle()
        if self.active_version is None:
            raise LifecycleError("remove requires an installed module")
        if runtime_running:
            raise LifecycleError("module runtime must be stopped before removal")
        self._begin("remove", "removing", None)

    def advance(self, *, runtime_running: bool = False) -> None:
        self._ensure_active_operation()
        next_phase: dict[OperationPhase, OperationPhase] = {
            "downloading": "verifying",
            "verifying": "staging",
            "staging": "activating",
        }
        operation = self.operation
        if operation is None or operation.kind not in {"install", "update"}:
            raise LifecycleError("only install and update operations use download/verify/stage phases")
        if operation.phase not in next_phase:
            raise LifecycleError(f"cannot advance operation from phase {operation.phase}")
        if operation.phase == "staging" and runtime_running:
            raise LifecycleError("module runtime must be stopped before activation")
        self.operation = Operation(
            operation.operation_id,
            operation.kind,
            next_phase[operation.phase],
            operation.source_version,
            operation.target_version,
        )

    def commit_activation(self) -> None:
        self._ensure_active_operation()
        operation = self.operation
        if operation is None or operation.phase != "activating" or operation.kind not in {"install", "update", "rollback"}:
            raise LifecycleError("activation can only commit from the activating phase")
        if operation.target_version is None:
            raise LifecycleError("activation target version is missing")
        self.previous_version = operation.source_version
        self.active_version = operation.target_version
        self.operation = None
        self.last_failure = None

    def commit_removal(self) -> None:
        self._ensure_active_operation()
        operation = self.operation
        if operation is None or operation.kind != "remove" or operation.phase != "removing":
            raise LifecycleError("removal can only commit from the removing phase")
        self.active_version = None
        self.previous_version = None
        self.disabled = False
        self.operation = None
        self.last_failure = None

    def cancel(self) -> None:
        self._ensure_active_operation()
        operation = self.operation
        if operation is None or operation.kind not in {"install", "update"} or operation.phase not in {"downloading", "verifying", "staging"}:
            raise LifecycleError("operation can only be cancelled before activation begins")
        self.operation = None
        self.last_failure = None

    def fail(self, error_code: str) -> None:
        self._ensure_active_operation()
        if not _ERROR_CODE.fullmatch(error_code):
            raise LifecycleError("failure error_code must be a stable lowercase identifier")
        operation = self.operation
        if operation is None:
            raise LifecycleError("there is no active operation to fail")
        self.last_failure = Failure(operation.kind, operation.phase, error_code, operation.target_version)
        self.operation = None

    def retry(self) -> None:
        self._ensure_idle()
        failure = self.last_failure
        if failure is None:
            raise LifecycleError("there is no failed operation to retry")
        if failure.kind == "install":
            if failure.target_version is None:
                raise LifecycleError("failed install has no target version")
            self.begin_install(failure.target_version)
        elif failure.kind == "update":
            if failure.target_version is None:
                raise LifecycleError("failed update has no target version")
            self.begin_update(failure.target_version)
        elif failure.kind == "rollback":
            self.begin_rollback(runtime_running=False)
        else:
            self.begin_remove(runtime_running=False)

    def set_disabled(self, disabled: bool, *, runtime_running: bool) -> None:
        self._ensure_idle()
        if self.active_version is None:
            raise LifecycleError("disable/enable requires an installed module")
        if runtime_running:
            raise LifecycleError("module runtime must be stopped before changing disabled state")
        self.disabled = disabled

    def recover_after_restart(self, *, active_pointer_version: str | None) -> str:
        """Reconcile the journal with the authoritative active-version pointer.

        Returns a storage-adapter instruction: clean staging, resume removal,
        finalize activation, or report that no recovery is needed.
        """
        operation = self.operation
        if operation is None:
            if active_pointer_version != self.active_version:
                raise LifecycleError("active-version pointer does not match the durable module record")
            return "no_recovery"

        if operation.kind == "remove":
            if active_pointer_version != self.active_version:
                raise LifecycleError("active-version pointer changed during removal")
            return "resume_removal"

        if operation.phase == "activating":
            if self.active_version != operation.source_version:
                raise LifecycleError("durable active version does not match the activation source")
            if active_pointer_version == operation.target_version:
                self.commit_activation()
                return "finalized_activation"
            if active_pointer_version == operation.source_version:
                failed = operation
                self.operation = None
                self.last_failure = Failure(failed.kind, failed.phase, "activation_interrupted", failed.target_version)
                return "restored_source"
            raise LifecycleError("active-version pointer matches neither activation source nor target")

        if self.active_version != operation.source_version or active_pointer_version != operation.source_version:
            raise LifecycleError("active-version pointer changed before activation")
        failed = operation
        self.operation = None
        self.last_failure = Failure(failed.kind, failed.phase, "operation_interrupted", failed.target_version)
        return "discard_staging"

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "ModuleRecord":
        """Restore a durable record after validating its structural invariants."""
        if value.get("recordVersion") != 1:
            raise LifecycleError("unsupported module record version")
        module_id = value.get("moduleId")
        active = value.get("activeVersion")
        previous = value.get("previousVersion")
        disabled = value.get("disabled")
        if not isinstance(module_id, str) or not isinstance(disabled, bool):
            raise LifecycleError("module record has invalid identity or disabled state")
        for version in (active, previous):
            if version is not None:
                if not isinstance(version, str):
                    raise LifecycleError("module record version values must be strings or null")
                _parse_semver(version)

        operation_value = value.get("operation")
        operation = None
        if operation_value is not None:
            if not isinstance(operation_value, dict):
                raise LifecycleError("module record operation must be an object or null")
            try:
                operation = Operation(
                    str(operation_value["operationId"]),
                    operation_value["kind"],
                    operation_value["phase"],
                    operation_value["sourceVersion"],
                    operation_value["targetVersion"],
                )
            except (KeyError, TypeError) as exc:
                raise LifecycleError("module record operation is incomplete") from exc
            if not re.fullmatch(r"[a-f0-9]{32}", operation.operation_id):
                raise LifecycleError("module record operation ID is invalid")
            if operation.kind not in {"install", "update", "rollback", "remove"}:
                raise LifecycleError("module record operation kind is invalid")
            if operation.phase not in {"downloading", "verifying", "staging", "activating", "removing"}:
                raise LifecycleError("module record operation phase is invalid")
            for version in (operation.source_version, operation.target_version):
                if version is not None:
                    _parse_semver(version)

        failure_value = value.get("lastFailure")
        failure = None
        if failure_value is not None:
            if not isinstance(failure_value, dict):
                raise LifecycleError("module record lastFailure must be an object or null")
            try:
                failure = Failure(
                    failure_value["kind"],
                    failure_value["phase"],
                    failure_value["errorCode"],
                    failure_value["targetVersion"],
                )
            except (KeyError, TypeError) as exc:
                raise LifecycleError("module record failure is incomplete") from exc
            if failure.kind not in {"install", "update", "rollback", "remove"}:
                raise LifecycleError("module record failure kind is invalid")
            if failure.phase not in {"downloading", "verifying", "staging", "activating", "removing"}:
                raise LifecycleError("module record failure phase is invalid")
            if not isinstance(failure.error_code, str) or not _ERROR_CODE.fullmatch(failure.error_code):
                raise LifecycleError("module record failure error code is invalid")
            if failure.target_version is not None:
                _parse_semver(failure.target_version)

        return cls(module_id, active, previous, disabled, operation, failure)

    def _ensure_active_operation(self) -> None:
        if self.operation is None:
            raise LifecycleError("there is no lifecycle operation in progress")

    def to_dict(self) -> dict[str, object]:
        operation = None if self.operation is None else {
            "operationId": self.operation.operation_id,
            "kind": self.operation.kind,
            "phase": self.operation.phase,
            "sourceVersion": self.operation.source_version,
            "targetVersion": self.operation.target_version,
        }
        failure = None if self.last_failure is None else {
            "kind": self.last_failure.kind,
            "phase": self.last_failure.phase,
            "errorCode": self.last_failure.error_code,
            "targetVersion": self.last_failure.target_version,
        }
        return {
            "recordVersion": 1,
            "moduleId": self.module_id,
            "activeVersion": self.active_version,
            "previousVersion": self.previous_version,
            "disabled": self.disabled,
            "operation": operation,
            "lastFailure": failure,
        }
