# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P1 IN PROGRESS - Module Manifest v1 and package validation implemented

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
- Module Manifest v1 uses a versioned JSON Schema, SemVer module versions, stable reverse-domain IDs, Platform API compatibility bounds, and required/optional capability declarations.
- Module ZIP archives contain `module.json` and web assets at the archive root; the v1 package validator enforces path, entry, compression, and size constraints.

## Implementation Status

| Area | Status |
|---|---|
| Product and architecture direction | Agreed at concept level |
| Repository metadata | Bootstrapped |
| Agent instructions and recovery prompt | Added; recovery prompt validated |
| Architecture baseline and ADRs | Added |
| Module Manifest v1 | JSON Schema and valid example defined |
| Module package validation | Reference ZIP validator and automated tests added |
| CI | Metadata validation and module contract tests configured |
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
**P1-01 - Define Module Manifest v1 and package layout.**

- Added `contracts/module-manifest.schema.json` using JSON Schema 2020-12.
- Added a valid counter-module package fixture.
- Defined module identity/version semantics, API compatibility bounds, capability declarations, ZIP root layout, release asset naming, and v1 archive safety limits.
- Added a reference package validator using the pinned `jsonschema` development dependency.
- Added tests for valid packages and invalid/hostile manifests and ZIP structures.
- Extended CI to install the development validator and run the test suite.
- Updated the checkpoint workflow so state and roadmap changes are committed together with implementation.

## Verification
- Previous remote CI: PASS - [run #5](https://github.com/dimkabuki/plat/actions/runs/42372637525), commit `ce9adfad6566adbed4329b1f01bc1990384b78f1`.
- Local P1-01 tests: PASS - 15 unit tests.
- Local metadata validation: PASS - all 16 required continuity and contract files present.
- Local schema/example JSON parsing: PASS.
- Local package CLI: PASS - the counter example archive validated as `dev.plat.example.counter@1.0.0`.
- Python bytecode compilation: PASS - validator and tests compile.
- Dependency installation: PASS - pinned `jsonschema==4.26.0` is available.
- Environment note: global `pip check` reports an unrelated pre-existing conflict: `moviepy` requires Pillow below 12, while the shared environment has Pillow 12.3.0. The project dependency is installed and the project tests pass.
- P1-01 remote CI: pending for the commit containing this state.
- Android build: not applicable; Android project does not exist.
- Release workflow: not executed; no Android project or signing configuration exists.
- Recovery validation: PASS - repository-only recovery report completed; a separate run in another provider/account was not performed.
- Git history note: `d321e2313d4a136ab5e2121888675b1e3ab90df5` remains a separate commit object outside `main` ancestry. Its `STATE.md` and `ROADMAP.md` contents match the corresponding committed mainline state; no history rewrite or cherry-pick was required.

## Known Risks and Open Questions
- Platform API method and capability registry remains to be finalized.
- Module lifecycle and installation-state transitions remain to be specified.
- WebView isolation model and secure native bridge design remain open.
- Publisher signatures, trusted-key distribution, and key rotation are not implemented.
- Android background update behavior and installation/activation semantics remain open.
- Android release signing and key custody remain open.
- Local storage ownership and backup/migration behavior remain open.
- Browser/PWA capability mapping remains open.
- Repository license has not been selected.

## Next Increment
**P1-02 - Define module lifecycle and installation states.**

Acceptance criteria:
1. Define state meanings and allowed transitions from discovery through installation, activation, update, disablement, failure, and removal.
2. Specify cancellation, retry, staging, atomic activation, and rollback behavior.
3. Define persisted versus transient state and which component owns each transition.
4. Include transition invariants and failure cases suitable for later executable tests.

Do not begin Android Host implementation until the P1 contracts and security boundaries have been reviewed.
