# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P1 IN PROGRESS - module package, lifecycle, and Platform API v1 contracts implemented

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
- Module installation records distinguish durable installation state, in-flight operations, and transient runtime state; activation and rollback preserve the previously active version until the commit boundary.
- Platform API v1 uses transport-neutral JSON request/response/event envelopes, explicit compatibility negotiation, and a capability-to-method allowlist with per-call authorization.

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
| Platform API v1 | Message schema, capability registry, method parameter validation, and authorization tests added |
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
**P1-03 - Define Platform API v1 protocol and capability negotiation.**

- Added `contracts/platform-api-v1.schema.json` for transport-neutral request, response, and event envelopes plus the bootstrap negotiation request.
- Added `contracts/platform-capabilities-v1.json` as the method allowlist, including parameter schemas and per-capability authorization policy.
- Defined Platform API version `1.0.0` separately from wire protocol version, manifest schema version, module version, and Android Host version.
- Added compatibility-range evaluation, required/optional capability negotiation, and per-call authorization checks in `scripts/validate_platform_api.py`.
- Defined UUID correlation IDs, structured error codes, event envelopes, timeout/cancellation semantics, and the Host/transport boundary.
- Added positive and negative protocol, method-parameter, compatibility, and permission tests.

## Verification
- P1-01 remote CI: PASS - [run #6](https://github.com/dimkabuki/plat/actions/runs/42375628514), commit `8e1ac5db56e04251e2eb8cbbbefbb54af942f740`.
- P1-02 remote CI: PASS - [run #7](https://github.com/dimkabuki/plat/actions/runs/42378150930), commit `7dbdce3b6f1ee5f2a7a4f1dae1c7db6ca10ec403`; metadata validation and the complete unittest suite succeeded.
- Local P1-03 test suite: PASS - 61 tests across package, lifecycle, and Platform API contracts.
- Local metadata validation: PASS - all 23 required files present.
- Platform API JSON Schema and capability registry validation: PASS.
- Python bytecode compilation: PASS - scripts and tests compile.
- P1-03 remote CI: pending for the commit containing this state.
- Android build: not applicable; Android project does not exist.
- Release workflow: not executed; no Android project or signing configuration exists.
- Recovery validation: PASS - repository-only recovery report completed; a separate run in another provider/account was not performed.
- Git history note: `d321e2313d4a136ab5e2121888675b1e3ab90df5` remains a separate commit object outside `main` ancestry. Its `STATE.md` and `ROADMAP.md` contents match the corresponding committed mainline state; no history rewrite or cherry-pick was required.

## Known Risks and Open Questions
- Platform API v1 contract is defined; concrete Host transport bindings and conformance implementations remain to be built.
- WebView isolation model and secure native bridge design remain open.
- Publisher signatures, trusted-key distribution, and key rotation are not implemented.
- Android background update behavior and installation/activation semantics remain open.
- Android release signing and key custody remain open.
- Local storage ownership and backup/migration behavior remain open.
- Browser/PWA capability mapping remains open.
- Repository license has not been selected.

## Next Increment
**P1-04 - Define Host Adapter conformance requirements.**

Acceptance criteria:
1. Define the minimum Host Adapter surface required to load a module and expose the negotiated Platform API.
2. Specify host identity/version reporting, supported capability discovery, lifecycle callbacks, and failure behavior.
3. Define a conformance suite that can run against both Android and Browser/PWA adapters.
4. Keep Host-specific transport and APIs behind the adapter boundary.

Do not begin Android Host implementation until the P1 contracts and security boundaries have been reviewed.
