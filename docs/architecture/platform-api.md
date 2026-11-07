# Platform API

## Purpose
The Platform API is the stable boundary between a module and its Host. Modules call this API without knowing whether the implementation is Android, Browser/PWA, or another future Host. This repository owns the canonical specification.

## Initial namespaces

| Namespace | Intended responsibility | Status |
|---|---|---|
| `runtime` | Host info, API version, capabilities, lifecycle | Planned |
| `ui` | Title, close/navigation requests, theme hints | Planned |
| `storage` | Module-scoped storage | Planned |
| `notifications` | User-visible notifications | Planned |
| `device` | Optional device features such as haptics | Planned |
| `messaging` | Future Host-mediated module messaging | Reserved; not implemented |

Do not implement the entire API before a real module requires it. Add capabilities incrementally.

## Capability negotiation
A module declares required and optional capabilities in its manifest. The Host reports which capabilities it supports.

A missing optional capability must not prevent startup. A missing required capability should produce an explicit incompatibility result before activation.

Capabilities are authorization boundaries, not merely feature flags. The Host must enforce access for every API call.

## Protocol direction
The current direction is an asynchronous message-based protocol using structured JSON messages and a transport such as MessageChannel where available. This is not a frozen wire protocol.

P1 must define request/response envelopes, method/event naming, request IDs, error codes, version negotiation, timeouts, cancellation, origin/sender validation, and transport mapping for Android WebView and Browser/PWA.

The TypeScript SDK should hide transport details from modules. Other language bindings may implement the same protocol.

## Versioning
The Platform API version is independent from the Host application version. The manifest declares minimum API compatibility. Compatibility rules and deprecation policy must be specified before the first stable contract release.

## Module communication
Direct module-to-module communication is out of scope. The reserved `messaging` namespace may later expose a Host-mediated service bus with explicit permissions, message schemas, and subscription lifecycle.
