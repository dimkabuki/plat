# ADR-0001: Android Host and Web Module Runtime

- Status: Accepted
- Date: 2026-11-07

## Context
The product should let users install one relatively stable Android application and add or update smaller modules independently. Modules should feel like separate applications while sharing a single Host.

A fully native APK-per-module design would introduce separate Android package installation and update flows and would not provide a consistent embedded UI/runtime.

## Decision
Use a native Kotlin Android Host with a WebView-based runtime for modules.

The Host owns platform lifecycle, module management, updates, navigation, storage boundaries, and native capability mediation. A module is a web application package loaded by the Host.

## Consequences
- Module updates do not require a Host APK update.
- Modules can use different web frameworks and build tools.
- Native capabilities must be exposed through a carefully restricted Host API.
- WebView isolation and bridge security are critical design areas.
- Modules are not standalone Android packages and do not own independent Android processes or permissions.
