# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P1 IN PROGRESS - Android WebView security boundary defined; compatibility and migration policy remains

## Project Summary
PLAT is an experimental modular application platform. Android is the first Host; modules are independently distributed web applications using a Host-independent contract. The repository is also the source of truth for development continuity across agents and sessions.

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
- Repository documentation is the durable source of truth.
- Module Manifest v1 uses a versioned JSON Schema, SemVer module versions, stable reverse-domain IDs, Platform API compatibility bounds, and required/optional capability declarations.
- Module ZIP archives contain `module.json` and web assets at the archive root; the v1 package validator enforces path, entry, compression, and size constraints.
- Module installation records distinguish durable installation state, in-flight operations, and transient runtime state; activation and rollback preserve the previously active version until the commit boundary.
- Platform API v1 uses transport-neutral JSON request/response/event envelopes, explicit compatibility negotiation, and a capability-to-method allowlist with per-call authorization.
- Host Adapter v1 defines a common host descriptor, module-session semantics, transport boundary, resource limits, and a shared Android/Browser conformance matrix.
- Android WebView v1 uses per-module HTTPS origins, WebViewAssetLoader, exact-origin WebMessageListener binding, a session handshake, strict navigation/content policy, and fail-closed behavior when the transport feature is unavailable.

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
| WebView security boundary v1 | Policy, bridge envelope, reference session model, and security conformance vectors added; Android runtime enforcement not implemented |
| CI | Metadata validation, module contract tests, and Host/security contract validation configured |
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
**P1-05 - Specify WebView security boundaries and bridge protocol.**

- Selected a per-module HTTPS origin derived from the stable module ID and served only from the verified package root through WebViewAssetLoader.
- Defined an exact-origin, main-frame-only WebMessageListener binding with fail-closed behavior when the feature is unavailable.
- Added a versioned bridge envelope schema, handshake/session lifecycle, UTF-8 byte limits, message direction rules, and teardown semantics.
- Defined strict WebView settings, navigation policy, CSP, response headers, and per-call capability authorization requirements.
- Added a Python reference session model and conformance scenarios for origin spoofing, stale sessions, malformed/oversized messages, module identity spoofing, and cross-module storage access.
- Added ADR-0005. The reference model validates the contract; no Android WebView implementation exists yet.

## Verification
- P1-04 remote CI: PASS - [run #9](https://github.com/dimkabuki/plat/actions/runs/42379205738), commit `6c493bf9dbbf01031a1cdbf54440c8a1f8ef0cd0`.
- P1-05 local Python test suite: pending; repository cannot be cloned in the execution environment. Contract tests will run in remote CI.
- Android WebView/runtime conformance: not yet executable; the Android adapter does not exist.
- Android build: not applicable; Android project does not exist.
- Recovery validation: PASS - repository-only recovery report completed; a separate run in another provider/account was not performed.

## Known Risks and Open Questions
- The P1-05 security policy is a specification and reference model, not runtime enforcement. Android device/WebView conformance remains mandatory.
- Publisher signatures, trusted-key distribution, and key rotation are not implemented.
- The Browser/PWA origin and sandbox binding remains to be specified.
- External navigation and broader network access require separate reviewed capabilities.
- Android background update behavior and installation/activation semantics remain open.
- Android release signing and key custody remain open.
- Local storage ownership, data migration, backup, and removal semantics remain open.
- Repository license has not been selected.

## Next Increment
**P1-06 - Define compatibility and migration policy.**

Acceptance criteria:
1. Define which version boundaries are independent and which changes require a major, minor, or patch increment for each contract.
2. Specify Host/API compatibility evaluation, supported version windows, and behavior for unknown future versions.
3. Define durable module-record and package migration rules, including rollback and crash-safe migration.
4. Define data migration ownership, backup/restore expectations, and behavior when an update cannot migrate data.
5. Add machine-readable policy examples and automated positive/negative tests.
6. Review compatibility policy against the accepted ADRs before starting Android implementation.

Do not begin Android Host implementation until the compatibility/migration policy has been reviewed.
