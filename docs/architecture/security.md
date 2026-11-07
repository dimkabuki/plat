# WebView Security Boundary v1

## Status and scope

This document selects the Android WebView trust boundary for the first module runtime. The machine-readable policy is `contracts/webview-security-v1.json`; the transport wrapper is `contracts/webview-bridge-v1.schema.json`; required security scenarios are in `contracts/webview-security-conformance-v1.json`.

This is a security contract, not evidence that an Android adapter exists or that PLAT is secure. The reference validator and tests validate the contract and its state model; runtime enforcement must be tested against a real Android WebView before a security claim is made.

## Origin and asset loading

Each installed module receives one stable, unique origin:

`https://m-{sha256(moduleId)[0:48]}.modules.plat.invalid`

The hostname is derived from the stable module ID using the first 48 lowercase hexadecimal characters of SHA-256. A different module ID must never share the origin. The Host UI uses a separate origin, `https://appassets.androidplatform.net`.

Android loads package content through `androidx.webkit.WebViewAssetLoader` and a path handler bound to the verified active package root for the session's module. No unhandled path or unknown host may fall back to network content. Modules are not loaded from `file://` or `data:` URLs. A full document navigation closes the current session and requires a new handshake.

This gives each module a distinct web origin for origin-scoped browser storage and prevents one module from reading another module's origin storage. The Host must also keep native storage namespaces derived from the Host-owned module ID, not from caller-supplied data. Module removal must clear the corresponding origin data after the module is stopped.

## Native bridge

Use `WebViewCompat.addWebMessageListener` from AndroidX WebKit. Register the bridge before loading the document, with the exact module origin as its only allowed-origin rule. Validate both the callback's `sourceOrigin` and `isMainFrame`; reject subframe messages. Require `WebViewFeature.WEB_MESSAGE_LISTENER`. If unavailable, refuse to launch the module - do not fall back to `addJavascriptInterface` or a generic receiver accepting arbitrary origins.

JavaScript is enabled because modules are web applications. No JavaScript interface is registered. The injected `platHost` object carries only the transport protocol; it is not a direct native API surface. Every API request is validated against Platform API v1 and authorized against the session's verified manifest, Host support, and current user consent on every call.

### Handshake and message lifecycle

1. The Host validates and binds the active package, manifest, module ID/version, and exact origin to a new WebView session before navigation.
2. The module sends a `hello` with bridge version 1, Platform API protocol version 1, and a UUID `helloId`.
3. The Host checks the message origin and main-frame flag, then returns `helloAck` with the same `helloId`, a Host-generated UUIDv4 `sessionId`, and enforced limits.
4. All subsequent messages include the active `sessionId`. Module-to-Host messages contain Platform API requests only; Host-to-module messages contain responses or events only.
5. The Host checks encoded UTF-8 byte length before JSON parsing, rejects duplicate JSON keys, validates the bridge wrapper and nested Platform API envelope, then authorizes the method before dispatch.

The v1 defaults are 65,536 bytes per message, 16 concurrent requests, a 15,000 ms request timeout, and a 10,000 ms handshake timeout. A session ID is a stale-message fence, not an authentication secret. Module JavaScript is untrusted code; origin checks and the Host-owned session context remain the security boundary.

Close and invalidate the session on top-level navigation/reload, renderer termination, WebView destruction, Host shutdown, module update activation, disablement, removal, or any origin/package binding mismatch. Cancel pending operations and discard late responses/events. Closing twice is safe.

## WebView hardening

The Host must configure:

- `allowFileAccess=false`, `allowContentAccess=false`, `allowFileAccessFromFileURLs=false`, and `allowUniversalAccessFromFileURLs=false`;
- mixed content `never-allow`, Safe Browsing enabled, multiple windows disabled, and third-party cookies disabled;
- JavaScript interfaces absent; downloads and file chooser denied;
- Web permissions denied unless a future reviewed capability explicitly grants one;
- debugging disabled in release builds. Debugging may be enabled only in a debug build;
- DOM storage scoped by the unique module origin and cleared on explicit module removal.

Top-level navigation is limited to the exact module origin. Subframes, custom schemes, external URL loads, and automatic external-intent dispatch are blocked in the module WebView. External navigation, should it be added later, must be a separate Host-owned user action and reviewed capability rather than an implicit WebView behavior.

Every module response must include this Content Security Policy:

```text
default-src 'self'; base-uri 'none'; object-src 'none'; frame-src 'none'; frame-ancestors 'none'; form-action 'none'; connect-src 'self'; img-src 'self' data: blob:; media-src 'self'; font-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; worker-src 'none'
```

This allows same-origin code and WebAssembly compilation while blocking remote scripts, remote connections, frames, objects, forms, and workers. Inline styles are permitted for UI framework compatibility; inline scripts and `eval` are not. The Host also sets `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cross-Origin-Resource-Policy: same-origin`, and a restrictive Permissions Policy.

## Required conformance

The conformance matrix includes origin spoofing, subframe messages, handshake ordering, stale session IDs, malformed and duplicate-key JSON, UTF-8 size limits, message direction, module-ID spoofing, cross-module storage, unsupported transport features, navigation, file access, remote code, per-call authorization, and teardown.

The current Python reference model validates message envelopes and session lifecycle only. It does not prove Android callback behavior, WebView configuration, origin isolation, or native storage isolation. P2 Android implementation must run these scenarios against a real WebView.

## Platform references

- [Android: Load in-app content](https://developer.android.com/develop/ui/views/layout/webapps/load-local-content) - use WebViewAssetLoader and avoid file/data URLs and unsafe file URL access.
- [AndroidX WebViewCompat API](https://developer.android.com/reference/androidx/webkit/WebViewCompat) - WebMessageListener and allowed-origin rules.
- [Android: Unsafe file inclusion in WebViews](https://developer.android.com/privacy-and-security/risks/webview-unsafe-file-inclusion) - file access and JavaScript risk guidance.
- [OWASP MASTG: Securely Load File Content in a WebView](https://mas.owasp.org/MASTG/best-practices/MASTG-BEST-0011/) - additional WebView hardening guidance.

## Open decisions

Publisher signatures and key rotation, the user-consent UX, Browser/PWA origin isolation implementation, external navigation capability design, network access policy beyond v1's same-origin restriction, persistent data migration semantics, and vulnerability reporting remain open.
