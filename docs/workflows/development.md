# Development Workflow

## Branch and commit model
- The only planned long-lived branch is `main`.
- Routine work is committed and pushed directly to `main`.
- Pull requests are not part of the initial workflow.
- Never force-push or rewrite published history.
- Keep increments small enough to verify independently.

## Increment lifecycle
1. Recover context from `AGENTS.md`, `PROJECT.md`, `STATE.md`, and `ROADMAP.md`.
2. Inspect actual code, Git status, recent commits, and CI status.
3. Select the single next increment in `STATE.md`.
4. Define a small scope and explicit acceptance criteria.
5. Implement the change and its tests.
6. Run relevant checks locally.
7. Review the complete diff.
8. Update docs, ADRs, and `STATE.md`.
9. Commit with a Conventional Commit message.
10. Push to `main`.
11. Inspect the corresponding GitHub Actions run.
12. Report commit, validation, CI, remaining issues, and next increment.

## Context-limit handling
Do not wait until an agent context is nearly exhausted to checkpoint. Complete and commit one verified increment before starting another.

If an increment is too large, split it into a smaller independently verifiable change. Do not leave the only copy of essential progress in chat or local uncommitted files.

## Commit examples
- `docs: add architecture baseline`
- `feat(host): create Android application shell`
- `feat(runtime): launch a local web module`
- `fix(updater): reject unsafe archive paths`
- `test(api): cover capability negotiation`
- `ci: run Android lint and unit tests`

## Continuous integration
Initial CI checks repository metadata and required continuity documents. It is intentionally small because application source does not exist yet.

As implementation is added, extend CI with relevant formatting, lint, type checking, unit tests, manifest/schema validation, and Android build steps. Do not add placeholder checks that claim to verify components that do not exist.

## Releases
- Product releases are created from version tags matching `v*`.
- The release workflow is separate from ordinary CI.
- Platform releases should contain a signed APK and a SHA-256 checksum.
- Signing keys are protected secrets and must never be committed.
- Do not create release tags until the Android build and signing configuration are ready.
- Module releases will use a separate workflow in the future demo-module repository.
