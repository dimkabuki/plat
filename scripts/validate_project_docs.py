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
    "docs/architecture/security.md",
    "docs/workflows/development.md",
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
        print("Missing required project documents:")
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
    sys.exit(main())
