# Roadmap

Roadmap items are intentions, not claims of implementation. \`STATE.md\` is authoritative for current progress and the next increment.

## P0 - Repository bootstrap
- [x] Define product direction and initial architecture.
- [x] Choose Tile Terminal as the platform visual direction.
- [x] Define repository-driven development continuity.
- [x] Add agent instructions, state, roadmap, ADRs, and recovery prompt.
- [x] Add initial CI and Android release workflow scaffolding.
- [x] Verify the first CI run.
- [x] Validate the recovery prompt in a repository-only session.

## P1 - Architecture and contracts
- [x] Finalize the Module Manifest schema.
- [x] Define module package layout and release asset naming.
- [x] Specify module lifecycle and installation states.
- [ ] Define Platform API namespaces, versioning, and capability negotiation.
- [ ] Define Host Adapter conformance requirements.
- [ ] Specify security boundaries and WebView bridge protocol.
- [ ] Define compatibility and migration policy.

## P2 - Android Host foundation
- [ ] Create the Android Kotlin project and build configuration.
- [ ] Bundle the Svelte/Vite Platform UI in the APK.
- [ ] Implement the initial Tile Terminal shell.
- [ ] Add a local module fixture and launch it in WebView.
- [ ] Implement a minimal, restricted Host-to-module API bridge.
- [ ] Add lifecycle handling and module-local storage isolation.

## P3 - Module management
- [ ] Implement module catalogue and local registry.
- [ ] Install a module ZIP from a local test source.
- [ ] Validate manifest, paths, package structure, and compatibility.
- [ ] Add GitHub Releases as an update source.
- [ ] Verify package integrity before activation.
- [ ] Add safe version activation and rollback.
- [ ] Display update availability and changelog.

## P4 - SDK and independent module experiments
- [ ] Publish a TypeScript SDK and browser mock Host.
- [ ] Create the separate demo-module repository.
- [ ] Implement a Svelte module.
- [ ] Implement a Rust/WebAssembly Canvas experiment.
- [ ] Verify both modules run without Host changes.
- [ ] Test independent module releases and updates.

## P5 - Dashboard
- [ ] Define the optional Dashboard contribution contract.
- [ ] Implement tile layout, sizing, and placement.
- [ ] Add module-provided tile views.
- [ ] Preserve module isolation and lifecycle rules in Dashboard mode.

## P6 - Browser/PWA Host
- [ ] Implement a browser/PWA Host Adapter.
- [ ] Reuse the same module packages and Platform API contract.
- [ ] Document unsupported or degraded capabilities.
- [ ] Run Host conformance tests.

## P7 - Chrome Extension experiment
- [ ] Evaluate Manifest V3 execution and sandbox constraints.
- [ ] Decide whether bundled modules or sandboxed content are viable.
- [ ] Implement only if the portability model remains useful.
- [ ] Document capability and update differences from Android/PWA.

## Release milestones
No product release milestone is scheduled. Do not create a version tag until the Android Host has a reproducible release build and signing strategy.
