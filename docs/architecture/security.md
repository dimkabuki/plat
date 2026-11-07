# Security Baseline

Security is a core design constraint even though PLAT is experimental. A module is downloaded executable web content and must be treated as untrusted unless its provenance and permissions have been established.

## Trust boundaries
1. GitHub repository/release metadata to the Host.
2. Downloaded archive to local module storage.
3. Module web content to the Host API bridge.
4. Module storage to other modules and the Platform.
5. Host capability calls to Android or browser APIs.

## Initial requirements
- Validate the manifest before installation using the canonical v1 schema and semantic rules. CI checks the reference implementation with the same schema; the Android Host must preserve these semantics when its validator is implemented.
- Reject path traversal, absolute paths, drive-prefixed paths, backslashes, NULs, non-normalized names, case-insensitive collisions, symlinks, special archive entries, encrypted entries, unexpected compression methods, duplicate paths, and invalid package layouts.
- Enforce compressed/uncompressed size, entry-count, and compression-ratio limits before activation.
- Read and verify every ZIP entry, including CRC, before accepting a package.
- Verify downloaded package integrity before activation.
- A checksum is useful against accidental corruption only when the expected checksum comes from an authenticated trusted channel; it does not by itself prove publisher identity.
- Plan publisher signatures and key rotation before accepting third-party modules.
- Isolate module storage by stable module identity.
- Do not expose unrestricted filesystem, intents, JavaScript interfaces, or arbitrary native APIs.
- Use an explicit capability allowlist and enforce it for every call.
- Validate message origin, sender, payload shape, size, and method.
- Treat module HTML, JavaScript, CSS, SVG, WebAssembly, and metadata as untrusted input.
- Do not place secrets in module packages or expose Host credentials to module code.
- Avoid remote executable scripts in a module unless a separately reviewed policy explicitly permits them.

## Android-specific review
Before implementation, review current Android WebView guidance and choose a design for WebView origin/assets, navigation allowlists, WebMessageListener or MessageChannel, JavaScript/file/content access, mixed content, release debugging, downloads, external intents, and WebView lifecycle.

Avoid unrestricted `addJavascriptInterface` exposure to module content.

## Update integrity
- Download to a staging location.
- Enforce package size and extraction limits.
- Validate archive paths and manifest compatibility.
- Verify the expected digest and publisher signature once signature verification is implemented.
- Activate atomically only after validation.
- Preserve the previous known-good version for rollback.
- Do not delete the active version until activation is confirmed.

## Open security decisions
Publisher identity/signature format, trusted-key distribution and rotation, capability approval UX, per-module origin and WebView isolation, network access policy, module-data backup/migration, and vulnerability reporting are not finalized.

Do not claim the system is secure merely because packages are downloaded over HTTPS or contain a SHA-256 checksum.
