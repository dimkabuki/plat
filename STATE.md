# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P1 IN PROGRESS - module package, lifecycle, Platform API, and Host Adapter contracts implemented

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
- Host Adapter v1 defines a common host descriptor, module-session semantics, transport boundary, resource limits, and a shared Android/Browser conformance matrix.

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
| Host Adapter v1 | Host descriptor schema, Android/Browser examples, and shared conformance vectors added |
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
**P1-04 - Define Host Adapter conformance requirements.**

- Added `contracts/host-adapter-v1.schema.json` for Host identity, runtime kind, transport, API version, capabilities, and enforced resource limits.
- Added Android and Browser/PWA descriptor examples with deliberately different capability sets.
- Defined the logical Host Adapter and module-session surface, including identity binding, request/response correlation, event subscriptions, timeouts, and idempotent close.
- Added `contracts/host-adapter-conformance-v1.json` with 14 required scenarios shared by future Android and Browser/PWA adapters.
- Added descriptor and conformance-matrix validation plus automated positive/negative tests. The tests validate contract artifacts, not actual runtime adapters; neither adapter exists yet.

## Verification
- P1-02 remote CI: PASS - [run #7](https://github.com/dimkabuki/plat/actions/runs/42378150930), commit `7dbdce3b6f1ee5f2a7a4f1dae1c7db6ca10ec403`.
- P1-03 remote CI: PASS - [run #8](https://github.com/dimkabuki/plat/actions/runs/42378905498), commit `6a9ec2894c8471c3ed0b8185fde69e3bd2466bb4`.
- Local P1-04 test suite: PASS - 70 tests across package, lifecycle, Platform API, and Host Adapter contracts.
- Local metadata validation: PASS - all 30 required files present.
- Host descriptor schema and conformance matrix validation: PASS - Android and Browser descriptors validate; all 14 required scenario IDs are present.
- Python bytecode compilation: PASS - scripts and tests compile.
- P1-04 remote CI: pending for the commit containing this state.
- Android and Browser/PWA runtime conformance: not yet executable; adapters do not exist.
- Android build: not applicable; Android project does not exist.
- Recovery validation: PASS - repository-only recovery report completed; a separate run in another provider/account was not performed.

## Known Risks and Open Questions
- Host Adapter and Platform API contracts are defined; concrete Host transport bindings and conformance implementations remain to be built.
- WebView isolation model and secure native bridge design remain open.
- Publisher signatures, trusted-key distribution, and key rotation are not implemented.
- Android background update behavior and installation/activation semantics remain open.
- Android release signing and key custody remain open.
- Local storage ownership and backup/migration behavior remain open.
- Browser/PWA capability mapping remains open.
- Repository license has not been selected.

## Next Increment
**P1-05 - Specify WebView security boundaries and bridge protocol.**

Acceptance criteria:
1. Select an origin/asset-loading model and define the trusted origin for module content.
2. Specify the transport endpoint, sender/origin validation, handshake, message limits, and session teardown.
3. Define navigation, external intent, file/content access, mixed-content, and remote-script policies.
4. Define the exact native API allowlist and ensure every bridge call passes Platform API capability authorization.
5. Include security-focused test cases for spoofed origins, stale sessions, malformed messages, and cross-module access.

Do not begin Android Host implementation until the P1 security boundaries and bridge contract have been reviewed.
