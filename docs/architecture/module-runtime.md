# Module Runtime

## Package boundary
A module is delivered as a versioned archive containing a manifest and static web assets. The exact schema and required files will be finalized in P1.

Conceptual package:

```text
module.zip
├── module.json
├── index.html
├── assets/
│   ├── app.js
│   └── app.css
└── wasm/
    └── engine.wasm
```

## Framework independence
The Host consumes the package contract, not the source framework. Candidate implementations include:
- vanilla JavaScript or TypeScript;
- Svelte;
- React, Vue, Solid, or other frameworks compiling to supported web assets;
- Rust compiled to WebAssembly, with DOM, Canvas, or WebGL integration.

This is not unrestricted native-code execution. WebAssembly executes within the browser runtime and remains subject to browser security boundaries.

## Lifecycle
Initial state vocabulary (not a finalized state machine):
- discovered;
- available;
- downloading;
- verifying;
- installed;
- update available;
- updating;
- running;
- disabled;
- failed or incompatible.

P1 must define valid transitions, persistence, cancellation, activation, and rollback semantics.

## Runtime isolation
Each module must execute in a context that does not expose the Platform UI or another module's DOM and JavaScript state.

Native functionality is mediated by a restricted, versioned API. Do not add an unrestricted JavaScript bridge or expose arbitrary file, intent, or process access.

The Android WebView isolation model, origin strategy, message channel, and content-security policy remain open design work.

## Module-owned UI
A module owns its full-screen application UI. The Platform owns outer navigation and lifecycle. Dashboard/tile integration is optional and will use a separate constrained contribution contract.

## Updates
A module version is downloaded and validated separately from the Host. A new version must be staged and checked before replacing the active version. Failed installation must not corrupt the currently active version.

GitHub Releases are the initial distribution source. The module repository's release artifact and manifest become the data consumed by the Host.
