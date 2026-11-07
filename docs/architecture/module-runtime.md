# Module Runtime

## Package boundary

A module is delivered as a ZIP archive whose root contains `module.json` and the web assets referenced by that manifest. Archives must not have an enclosing top-level directory.

```text
<module-id>-<module-version>.zip
├── module.json
├── index.html
├── assets/
│   ├── app.js
│   └── app.css
└── wasm/
    └── engine.wasm
```

The release asset name is `<module-id>-<module-version>.zip`, for example `dev.plat.example.counter-1.0.0.zip`. The archive filename is a distribution convention, not module identity; the Host trusts the validated manifest identity.

The canonical JSON Schema is `contracts/module-manifest.schema.json` (JSON Schema 2020-12). A valid example package source is in `contracts/examples/counter/`. The CI package validator uses the pinned `jsonschema` development dependency and enforces both the schema and the archive-level rules below.

### Manifest v1

Required fields:

| Field | Meaning |
|---|---|
| `schemaVersion` | Integer `1`; version of the manifest format, independent from module and Platform API versions. |
| `id` | Stable reverse-domain identifier, lowercase segments, e.g. `dev.plat.example.counter`. Identity must not change between releases. |
| `name` | Display name, 1-80 characters. |
| `version` | Module release version using Semantic Versioning 2.0.0. |
| `entry` | Case-sensitive POSIX-relative path to the entry HTML file inside the ZIP. |
| `platformApi.minVersion` | Minimum compatible stable Platform API `major.minor.patch`. |
| `capabilities.required` | Capabilities that must be present before activation. |
| `capabilities.optional` | Capabilities used only when the Host advertises them. |

Optional fields are `description` (up to 280 characters) and `platformApi.maxVersionExclusive` (exclusive upper bound on compatible API versions). Unknown fields are rejected in v1; extensions require a new schema revision rather than silently changing semantics.

Capability names use a namespace-qualified identifier such as `storage.kv`. The concrete capability registry and API methods are specified separately. A capability must not be requested in both `required` and `optional`.

### Compatibility semantics

- Manifest `schemaVersion` must be exactly `1`; unknown schema versions are incompatible.
- The Host API version must have the same major version as `platformApi.minVersion` and compare greater than or equal to that minimum.
- If `maxVersionExclusive` is present, the Host API version must be lower than it. The upper bound must use the same major version and be greater than the minimum.
- A missing required capability makes the module incompatible before activation. Missing optional capabilities do not block launch; the module must degrade gracefully.
- Module `version` is independent from both manifest schema and Platform API version. Releases of one module retain the same `id` and advance `version` according to SemVer.

### Archive validation

The package validator rejects:

- missing root `module.json`, malformed/duplicate-key JSON, unsupported or unknown manifest fields, and invalid manifest values;
- missing entry file or a manifest entry that is not a safe package-relative path;
- absolute paths, drive-prefixed paths, backslashes, NULs, `.` or `..` segments, non-NFC names, paths over 240 UTF-8 bytes, and case-insensitive path collisions;
- symlinks and special filesystem entries, encrypted entries, unsupported ZIP compression methods, and file/directory path conflicts;
- archives over 50 MiB compressed, more than 1,000 entries, a file over 50 MiB uncompressed, total uncompressed content over 100 MiB, or an entry compression ratio over 100:1.

Only ZIP_STORED and ZIP_DEFLATED are supported. The validator reads every file entry to verify its size and CRC before accepting the package. The active installed module must never be overwritten as part of package validation; installation staging and activation are separate lifecycle operations.

These limits are v1 policy and can be raised only through a reviewed contract revision. Validation does not prove publisher identity, module-code safety, or permission approval. Do not treat a valid archive as trusted executable content.

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
