# Agent Instructions

## Source of truth
The repository is the authoritative source for project context and development state. Do not rely on previous conversations, hidden agent memory, or provider-specific workspace state.

Before planning or changing code, read:
1. `PROJECT.md`
2. `STATE.md`
3. `ROADMAP.md`
4. Relevant files under `docs/architecture/`
5. Relevant accepted ADRs under `docs/decisions/`
6. Relevant instructions under `docs/workflows/`

Then inspect the actual repository, Git state, recent commits, and latest CI results. Treat code and observed verification as evidence; documentation can become stale.

## Working model
- Expected contributors: repository owner and AI agents.
- Work directly on `main`; no routine pull requests.
- Keep each increment small, scoped, and independently verifiable.
- Prefer one vertical slice over broad scaffolding.
- Do not start another increment while the current increment has an unresolved failure.
- Keep `main` buildable and the repository recoverable after every completed increment.

## Before implementation
1. Identify the single next increment in `STATE.md`.
2. Inspect relevant code and tests.
3. State intended changes and acceptance criteria.
4. Check whether the change affects a public contract or accepted decision.
5. Avoid unrelated cleanup and speculative abstractions.

If the next action is ambiguous or conflicts with the actual repository state, report the discrepancy before changing files.

## Implementation and verification
- Implement only the agreed increment.
- Add or update tests for changed behavior.
- Run relevant formatting, lint, type-check, tests, and build commands that exist.
- Never claim a check passed unless it was executed and its result observed.
- Do not suppress errors, skip relevant tests, or weaken types to obtain a green build.
- Record checks that could not run and why.
- Review the final diff for accidental changes, generated files, secrets, and unrelated edits.

## Checkpoint and continuity
At the end of every completed increment:
1. Update `STATE.md` and `ROADMAP.md` before committing, in the same commit as the implementation.
2. Update architecture docs or ADRs in that same increment when implementation or an accepted decision changes.
3. Ensure no required knowledge exists only in the conversation.
4. Commit the complete, verified increment using Conventional Commits; do not create separate metadata-only or documentation-only follow-up commits for that increment.
5. Push directly to `main`.
6. Inspect the corresponding GitHub Actions run and report its status. Record a post-push CI result in the next substantive checkpoint rather than creating a metadata-only commit.

Do not wait until the context limit is near before saving progress. Checkpoint after each logical increment.

If a session must end before the current increment is complete, do not claim completion. Reduce scope so the next checkpoint is independently verifiable; do not leave the only copy of essential progress in chat or local uncommitted files.

## Git rules
- Branch: `main`.
- Never force-push or rewrite published history.
- Do not amend or delete commits already pushed to `main`.
- Use Conventional Commits, for example:
  - `docs: add architecture baseline`
  - `feat(runtime): load a local web module`
  - `fix(updater): reject an invalid module archive`
  - `test(manifest): cover unsupported schema versions`
  - `ci: validate Android build`
- Do not commit credentials, signing keys, tokens, private data, or local machine configuration.

## Dependencies and security
- Prefer minimal, maintained dependencies.
- Pin GitHub Actions to full commit SHAs.
- Use least-privilege workflow permissions.
- Keep release-only write permissions out of ordinary CI.
- Treat downloaded module packages and module code as untrusted until validated.
- Do not expose unrestricted native APIs to module code.
- Document security assumptions when introducing a new trust boundary.

## Completion report
After pushing an increment, report:
- What changed.
- Commit SHA.
- Checks executed and observed results.
- GitHub Actions status.
- Remaining limitations or risks.
- The next recommended increment.

A task is not complete merely because code was written or committed. Report local verification and remote CI separately.
