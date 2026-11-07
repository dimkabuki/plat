# ADR-0005: Android WebView Module Security Boundary

- Status: Accepted
- Date: 2026-11-07

## Context

Modules are downloaded executable web content. Android WebView must host them without granting access to the Host UI, another module's origin/storage, local files, arbitrary Android APIs, or unrestricted external navigation. The Android WebView implementation must also preserve the Host-independent Platform API contract.

## Decision

1. Give each stable module ID a distinct HTTPS origin derived from the first 48 lowercase hexadecimal characters of SHA-256(module ID), under `modules.plat.invalid`.
2. Serve only the verified active package root through AndroidX `WebViewAssetLoader`. The Host UI uses a separate origin. Unknown paths/hosts do not fall back to network content.
3. Use `WebViewCompat.addWebMessageListener` with one exact allowed-origin rule and validate `sourceOrigin` plus `isMainFrame` on every callback.
4. Require `WebViewFeature.WEB_MESSAGE_LISTENER`. Refuse module launch when unsupported; never fall back to `addJavascriptInterface` or an unrestricted receiver.
5. Require a `hello`/ `helloAck` handshake and a Host-generated UUIDv4 session ID. Bind module identity, version, verified manifest, capabilities, and storage namespace in Host-owned session context. Never trust caller-supplied module identity.
6. Enforce strict message direction, Platform API schema validation, per-call capability/consent authorization, a 65,536-byte UTF-8 message limit, 16 concurrent requests, and a 15,000 ms request timeout.
7. Disable file/content access, file-URL access, mixed content, third-party cookies, multiple windows, downloads, file chooser, and unapproved Web permissions. Block subframes, cross-origin navigation, custom schemes, and remote executable resources. Apply a restrictive CSP and security response headers.
8. Invalidate sessions on document navigation/reload, renderer loss, WebView/Host shutdown, package activation, disablement, removal, or binding mismatch.

## Consequences

- Android module origins and origin-scoped browser storage are isolated by stable module identity.
- The Android bridge has a platform-supported origin restriction and an explicit main-frame check.
- Modules cannot assume remote network access, workers, frames, or external navigation in v1.
- WebMessageListener availability is a runtime prerequisite; the Host must fail closed on older unsupported WebView implementations.
- The decision does not prove runtime isolation. P2 must exercise the contract against actual Android WebViews and device/API combinations.
- Browser/PWA needs its own binding and conformance implementation; this ADR does not prescribe it.
