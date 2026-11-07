# Architecture Overview

## System model
PLAT separates module code from the Host that provides its execution environment and capabilities. A module is a portable web application package. A Host discovers, installs, launches, updates, and exposes APIs to modules.

```text
                  MODULE PACKAGE
                        |
                 Module Contract
                        |
                   Platform API
                        |
          +-------------+-------------+
          |             |             |
      Android Host   Browser/PWA   Other Host
          |             |             |
        WebView       Browser       Future
```

## Initial Android Host
The Android Host is a Kotlin application. Its responsibilities are:
- platform shell and navigation;
- module catalogue and installed-module registry;
- module download, validation, installation, activation, and rollback;
- WebView lifecycle and containment;
- capability negotiation and native API mediation;
- update scheduling and user-visible update controls;
- module-specific storage isolation.

The Platform UI is planned as a Svelte/Vite application bundled into the Android APK. It is not remotely updated as a module.

## Module runtime
Modules execute as web content in a WebView or compatible browser runtime. Their implementation framework is an internal choice, provided the resulting package uses supported web standards.

Candidate implementations include vanilla JavaScript/TypeScript, Svelte, and Rust compiled to WebAssembly. Canvas and WebGL are rendering options where supported by the Host.

Module Manifest v1 and its ZIP package boundary are specified in `contracts/` and `docs/architecture/module-runtime.md`.

## Host portability
Android is first. Browser/PWA is the first planned portability test. Chrome Extension is exploratory because extension execution and remote-code policies differ from a normal browser host.

A shared contract does not guarantee feature parity. Each Host advertises its capabilities; modules must handle missing optional capabilities.

## Data and communication
- Modules do not have direct access to other modules.
- Each module receives an isolated storage namespace.
- Future module messaging, if implemented, is mediated by a Host service.
- The Host owns update state and the installed-module registry.

## Current boundaries
This is an architecture baseline, not a completed product implementation. Lifecycle semantics, Platform API framing, Host Adapter conformance, and WebView security details remain P1 work.
