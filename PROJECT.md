# Project Definition

## Product summary
PLAT is an experimental, educational modular application platform. A user installs one relatively stable Host application, then discovers, installs, launches, and updates independent modules without reinstalling the Host.

The initial Host is Android. Modules are portable web applications packaged independently from the Host. A module may use any framework or compiler that produces assets compatible with the supported web runtime.

The project also experiments with repository-driven AI-assisted development: any compatible agent should recover the engineering context from GitHub and continue in small increments.

## Product goals
1. Provide a small Android Host with a distinctive, minimal Tile Terminal interface.
2. Install and update web modules independently of the Host.
3. Keep modules independent in implementation, release cadence, UI framework, and local data.
4. Define a stable, versioned Module Contract and Host-independent Platform API.
5. Keep Host-specific functionality behind Host Adapters.
6. Make portability testable through a future browser/PWA Host.
7. Explore Dashboard tiles as an optional presentation surface.
8. Preserve development continuity through committed project state and documentation.

## Non-goals for the initial release
- Executing arbitrary native APKs as embedded modules.
- Direct module-to-module communication.
- A public third-party marketplace or multi-tenant registry.
- A backend service operated by the project.
- Identical feature parity across every Host.
- Building the Dashboard before module installation and lifecycle are reliable.
- A production-grade plugin ecosystem with external contributors.

## Accepted direction
- Android is the primary Host.
- Android modules run in a WebView-based web runtime.
- Modules are independent web bundles distributed separately from the Host.
- The module package boundary is framework-agnostic.
- Svelte/vanilla web modules and Rust/WASM are planned experiments.
- Host-specific APIs are exposed through a versioned Platform API.
- Modules do not communicate directly; future messaging is mediated by the Host.
- Browser/PWA is the first portability experiment after Android fundamentals.
- Chrome Extension is exploratory and has no promise of identical dynamic-update behavior.
- The selected visual direction is Tile Terminal: a compact, tile-oriented GUI with terminal-inspired information density, not a fake command-line interface.

## Initial technical direction

| Area | Direction |
|---|---|
| Android Host | Kotlin |
| Android module runtime | Android WebView |
| Host UI | Svelte + Vite, bundled into the Android application |
| Styling | Custom CSS and design tokens |
| Module SDK | TypeScript |
| Module runtime target | Web platform standards |
| Rust experiments | WebAssembly, Canvas, or WebGL |
| Module package | Versioned ZIP archive with a manifest |
| Initial update source | GitHub Releases |
| Background work | WorkManager when needed |
| Local metadata | SQLite/Room is a candidate; final choice is open |
| Host API transport | Message-based protocol; exact wire format is open |

These are implementation directions, not claims that components exist.

## Repository boundaries
- `dimkabuki/plat` owns the Platform Host, canonical contracts, Platform API specification, shared SDK specifications, architecture decisions, and project state.
- A separate demo-module repository will own the sample module implementation and release artifacts. It has not been created yet.
- Other repositories consume a released or versioned copy of shared contracts; they must not silently fork them.

## Operating constraints
- Optimize for learning, clarity, and short feedback loops rather than premature production infrastructure.
- Security boundaries on the phone remain important even though this is experimental.
- Only the repository owner and AI agents are expected to contribute initially.
- Development uses small increments, direct pushes to `main`, CI on each push, and explicit versioned releases.
- No long-lived agent state may exist only in chat history.
- No license has been selected. Public visibility is not an open-source license.
