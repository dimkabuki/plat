# Project State

Last updated: 2026-11-07

## Current Phase
P1 - Architecture and contracts

## Overall Status
P0 COMPLETE - repository bootstrap and recovery prompt validated; P1 ready

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
| Agent instructions and recovery prompt | Added; recovery prompt validated |
| Architecture baseline and ADRs | Added |
| CI | Documentation validation passed |
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
**N001 - Validate repository-only context recovery.**

- Ran the read-only recovery procedure using `docs/agent/recover-context.md`.
- Recovered the product direction, architecture, implementation status, CI evidence, and next increment from repository contents.
- Confirmed that the repository contains enough information to continue without the original project discussion.
- No product implementation was started.

## Verification
- Recovery validation: PASS - the repository-only recovery report covered the required project, architecture, implementation, verification, and next-step information. A separate run in another provider/account was not performed.
- CI: PASS - [run #3](https://github.com/dimkabuki/plat/actions/runs/42371180805), commit `e938381365ddd7fd242589497835bb87aa8a42bc`.
- CI steps observed: checkout and continuity-document validation succeeded.
- Android build: not applicable; Android project does not exist.
- Release workflow: not executed; no Android project or signing configuration exists.
- Git history: `d321e2313d4a136ab5e2121888675b1e3ab90df5` is a separate commit object whose parent is `277608c3608b4f4118a0f5f72c78cfa1f589d0cb`. Its `STATE.md` and `ROADMAP.md` contents match the current `main` tree; it is not in `main` ancestry. The current `main` commit `e938381365ddd7fd242589497835bb87aa8a42bc` contains those changes along with README and recovery-prompt updates. No history rewrite or cherry-pick is required; the separate commit is left untouched.
- This housekeeping commit still requires its own remote CI run.

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
**P1-01 - Define Module Manifest v1 and package layout.**

Acceptance criteria:
1. Specify the manifest schema, required and optional fields, and schema versioning.
2. Define module identity, module version, entry point, asset layout, and package directory structure.
3. Define how the manifest expresses Platform API compatibility and requested capabilities.
4. Document package validation requirements and representative valid/invalid examples.
5. Review the contract against the accepted architecture decisions before implementation begins.

Do not begin Android Host implementation until the module contract has been reviewed.
