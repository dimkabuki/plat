# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P1 IN PROGRESS - WebView security contract implemented; CI revalidation pending after first bug fix

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
| CI | Metadata validation, module contract tests, Host Adapter validation, and WebView security validation configured |
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

- Added the Host descriptor schema, Android and Browser/PWA examples, logical session contract, and the shared conformance matrix.
- Added descriptor and matrix validation with automated tests.
- The latest P1-04 CI run passed.

## Active Increment
**P1-05 - Specify WebView security boundaries and bridge protocol.**

- Selected per-module HTTPS origins served from the verified package root through WebViewAssetLoader.
- Defined exact-origin, main-frame-only WebMessageListener binding with fail-closed behavior when unavailable.
- Added a versioned bridge envelope schema, handshake/session lifecycle, UTF-8 byte limits, message direction rules, and teardown semantics.
- Defined WebView settings, navigation policy, CSP, response headers, and per-call capability authorization requirements.
- Added a Python reference session model, security conformance vectors, validator, and tests.
- The first CI attempt found a regex-escaping defect in the validator and an incorrect pre-handshake error path. This commit fixes both and adds an explicit origin-pattern regression test. Android runtime enforcement remains unimplemented.

## Verification
- P1-04 remote CI: PASS - [run #9](https://github.com/dimkabuki/plat/actions/runs/42379205738), commit `6c493bf9dbbf01031a1cdbf54440c8a1f8ef0cd0`.
- P1-05 initial remote CI: FAIL - [run #10](https://github.com/dimkabuki/plat/actions/runs/42404668941), commit `e8f0deaa1d434c15d2e85314a88baaa9135533ee`. The WebView security validation step failed; the unit-test step was skipped.
- Bug fix commit: this commit corrects the validator regex and handshake validation order; its remote CI result must be checked before starting P1-06.
- Local Python tests: not run because this environment cannot resolve github.com for a repository checkout.
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

Do not begin P1-06 until the CI run for the P1-05 bug-fix commit succeeds.
