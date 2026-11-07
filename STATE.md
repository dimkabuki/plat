# Project State

Last updated: 2026-11-07

## Current Phase
P0 - Repository bootstrap

## Overall Status
BOOTSTRAP COMPLETE - CI passed; fresh-session recovery test pending

## Project Summary
PLAT is an experimental modular application platform. Android is the first Host; modules are independently distributed web applications using a Host-independent contract. The repository is also the source of truth for development continuity across AI agents and sessions.

## Completed Decisions
- Android is the primary Host.
- Android modules run in a WebView-based web runtime.
- Modules are portable web bundles, not embedded native APKs.
- The module package boundary is framework-agnostic.
- Svelte/vanilla web modules and Rust/WASM are planned experiments.
- Host-specific APIs are exposed through a versioned Platform API.
- Direct module-to-module communication is out of scope; future messaging is mediated by the Host.
- Browser/PWA is the first portability experiment after Android.
- Chrome Extension remains exploratory.
- Platform visual direction: Tile Terminal.
- Two repositories are planned: platform and separate demo module.
- Work proceeds in small increments on `main`, with CI on every push and explicit releases.
- Repository documentation is the durable source of project state.

## Implementation Status

| Area | Status |
|---|---|
| Product and architecture direction | Agreed at concept level |
| Repository metadata | Bootstrapped |
| Agent instructions and recovery prompt | Added |
| Architecture baseline and ADRs | Added |
| CI | Initial documentation validation passed |
| Release workflow | Scaffolded; Android build and signing are not implemented |
| Android Host | Not started |
| Platform UI | Not started |
| Module Runtime | Not started |
| Module Registry and updater | Not started |
| Module SDK | Not started |
| Demo module repository | Not created |
| Dashboard | Not started |
| Browser/PWA Host | Not started |

## Last Completed Increment
**Bootstrap repository metadata and workflow configuration.**

- Added project context, roadmap, current state, architecture baseline, ADRs, and the reusable session recovery prompt.
- Added documentation validation script and CI workflow.
- Added Android APK release workflow scaffold.
- Committed directly to `main`.

## Verification
- GitHub access: confirmed for authenticated account `dimkabuki` with admin, maintain, and push permissions.
- Default branch: `main`; direct push is allowed.
- CI: PASS - [run #1](https://github.com/dimkabuki/plat/actions/runs/42365919577), commit `277608c3608b4f4118a0f5f72c78cfa1f589d0cb`.
- CI steps observed: checkout and continuity-document validation succeeded.
- Android build: not applicable; Android project does not exist.
- Release workflow: not executed; no Android project or signing configuration exists.

## Known Risks and Open Questions
- Exact Module Manifest schema and compatibility rules.
- Exact Platform API protocol and version negotiation.
- WebView isolation model and secure native bridge design.
- Module package signing and trust/key rotation.
- Android background update behavior and installation/activation semantics.
- Android release signing and key custody.
- Local storage ownership and backup/migration behavior.
- Browser/PWA capability mapping.
- Whether GitHub Issues should be enabled for increment tracking.
- Repository license has not been selected.

## Next Increment
**N001 - Validate fresh-session context recovery.**

Acceptance criteria:
1. Start a new agent session without relying on this conversation.
2. Give it the repository URL and the prompt in `docs/agent/recover-context.md`.
3. The agent identifies the product, architecture direction, current phase, implemented versus unimplemented areas, latest CI result, and the next increment.
4. Review discrepancies and correct repository documentation if needed.

Do not begin Android implementation until this recovery test has been reviewed.
