# ADR-0002: Portable Module Contract

- Status: Accepted
- Date: 2026-11-07

## Context
Modules should be reusable across Android and future Hosts. The platform should not prescribe whether a module is written in Svelte, vanilla TypeScript, another UI framework, or Rust compiled to WebAssembly.

## Decision
Define a Host-independent Module Contract and Platform API. The package boundary targets standard web runtime assets. Each Host implements the same logical API through a Host Adapter.

The Android Host is first. Browser/PWA is the first portability experiment. Chrome Extension remains exploratory because extension policies and execution environments may restrict independent remote code loading.

## Consequences
- The Host validates the package contract, not the module's source framework.
- Framework-specific details stay inside the module package.
- A module can rely only on capabilities advertised by the Host.
- Feature parity is not assumed; modules handle missing optional capabilities.
- Shared contracts are versioned and owned by the platform repository.
