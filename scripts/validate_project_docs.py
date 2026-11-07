#!/usr/bin/env python3
"""Validate the repository's minimum project-continuity documents."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "PROJECT.md",
    "STATE.md",
    "ROADMAP.md",
    "docs/agent/recover-context.md",
    "docs/architecture/overview.md",
    "docs/architecture/module-runtime.md",
    "docs/architecture/platform-api.md",
    "docs/architecture/host-adapter.md",
    "docs/architecture/security.md",
    "docs/architecture/security.md",
    "docs/workflows/development.md",
    "docs/decisions/ADR-0005-webview-security-boundary.md",
    "contracts/module-manifest.schema.json",
    "contracts/module-record.schema.json",
    "contracts/platform-api-v1.schema.json",
    "contracts/platform-capabilities-v1.json",
    "contracts/host-adapter-v1.schema.json",
    "contracts/host-adapter-conformance-v1.json",
    "contracts/webview-bridge-v1.schema.json",
    "contracts/webview-security-v1.json",
    "contracts/webview-security-conformance-v1.json",
    "contracts/examples/host/android.json",
    "contracts/examples/host/browser.json",
    "contracts/examples/counter/module.json",
    "scripts/validate_module_package.py",
    "scripts/module_lifecycle.py",
    "scripts/validate_platform_api.py",
    "scripts/validate_host_adapter.py",
    "scripts/validate_webview_security.py",
    "tests/test_validate_module_package.py",
    "tests/test_module_lifecycle.py",
    "tests/test_platform_api_contract.py",
    "tests/test_host_adapter_contract.py",
    "tests/test_webview_security_contract.py",
    "requirements-dev.txt",
)

STATE_REQUIRED_HEADINGS = (
    "## Current Phase",
    "## Overall Status",
    "## Implementation Status",
    "## Verification",
    "## Next Increment",
)


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        print("Missing required project documents or contract files:")
        for path in missing:
            print(f"  - {path}")
        return 1

    state = (ROOT / "STATE.md").read_text(encoding="utf-8")
    missing_headings = [heading for heading in STATE_REQUIRED_HEADINGS if heading not in state]
    if missing_headings:
        print("STATE.md is missing required sections:")
        for heading in missing_headings:
            print(f"  - {heading}")
        return 1

    print(f"Project metadata validation passed ({len(REQUIRED_FILES)} required files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
