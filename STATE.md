# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P1 IN PROGRESS - module package and installation lifecycle contracts implemented

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
- Work proceeds in small increments on \`main\`, with CI on every push and explicit releases.
- Repository documentation is the durable source of project state.
- Module Manifest v1 uses a versioned JSON Schema, SemVer module versions, stable reverse-domain IDs, Platform API compatibility bounds, and required/optional capability declarations.
- Module ZIP archives contain \`module.json\` and web assets at the archive root; the v1 package validator enforces path, entry, compression, and size constraints.
- Module installation records distinguish durable installation state, in-flight operations, and transient runtime state; activation and rollback preserve the previously active version until the commit boundary.

## Implementation Status

| Area | Status |
|---|---|
| Product and architecture direction | Agreed at concept level |
| Repository metadata | Bootstrapped |
| Agent instructions and recovery prompt | Added; recovery prompt validated |
| Architecture baseline and ADRs | Added |
| Module Manifest v1 | JSON Schema and valid example defined |
| Module package validation | Reference ZIP validator and automated tests added |
| Module lifecycle | Durable record schema, reference state machine, and crash-recovery tests added |
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
**P1-02 - Define module lifecycle and installation states.**

- Added \`contracts/module-record.schema.json\` for durable module installation records and operation journals.
- Defined catalogue compatibility separately from installation state and transient runtime state.
- Defined install/update transitions (\`downloading -> verifying -> staging -> activating\`), removal, disablement, rollback, cancellation, failure, retry, and restart reconciliation.
- Added \`scripts/module_lifecycle.py\` as an executable reference state machine, including SemVer update ordering, JSON record restoration, and atomic activation boundaries.
- Added lifecycle tests for update preservation, rollback, runtime-stop preconditions, cancellation, failure/retry, and interrupted-operation recovery after serialization round-trip.
- Updated required-file validation; the existing CI unittest discovery automatically includes lifecycle tests.

## Verification
- P1-01 remote CI: PASS - [run #6](https://github.com/dimkabuki/plat/actions/runs/42375628514), commit \`8e1ac5db56e04251e2eb8cbbbefbb54af942f740\`.
- CI steps observed: Python setup, dependency installation, continuity validation, and all module package contract tests succeeded.
- Local test suite after P1-02: PASS - 35 unit tests.
- Local schema/example JSON parsing: PASS.
- Local package CLI: PASS - the counter example archive validated as \`dev.plat.example.counter@1.0.0\`.
- Local metadata validation: PASS - all 19 required continuity, contract, script, and test files present.
- Python bytecode compilation: PASS - scripts and tests compile.
- P1-02 remote CI: pending for the commit containing this state.
- Android build: not applicable; Android project does not exist.
- Release workflow: not executed; no Android project or signing configuration exists.
- Recovery validation: PASS - repository-only recovery report completed; a separate run in another provider/account was not performed.
- Git history note: \`d321e2313d4a136ab5e2121888675b1e3ab90df5\` remains a separate commit object outside \`main\` ancestry. Its \`STATE.md\` and \`ROADMAP.md\` contents match the corresponding committed mainline state; no history rewrite or cherry-pick was required.

## Known Risks and Open Questions
- Platform API protocol, method envelope, and capability registry remain to be finalized.
- WebView isolation model and secure native bridge design remain open.
- Publisher signatures, trusted-key distribution, and key rotation are not implemented.
- Android background update behavior and installation/activation semantics remain open.
- Android release signing and key custody remain open.
- Local storage ownership and backup/migration behavior remain open.
- Browser/PWA capability mapping remains open.
- Repository license has not been selected.

## Next Increment
**P1-03 - Define Platform API v1 protocol and capability negotiation.**

Acceptance criteria:
1. Define request/response/event envelopes, IDs, method naming, and structured error codes.
2. Define protocol version negotiation independently from the Android Host version and module release version.
3. Define how required and optional manifest capabilities map to Host-advertised and Host-enforced permissions.
4. Add JSON Schemas and tests for valid and invalid protocol messages.
5. Keep transport binding separate from the logical protocol so Android WebView and Browser/PWA can implement the same contract.

Do not begin Android Host implementation until the P1 contracts and security boundaries have been reviewed.
