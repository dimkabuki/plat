# Agent Session Recovery Prompt

Copy the prompt below into a new AI-agent session. Replace the repository URL only if using a different project repository.

---

Please recover the project context from this repository and prepare to continue development.

Repository: https://github.com/dimkabuki/plat

Read these files first:

1. `AGENTS.md`
2. `PROJECT.md`
3. `STATE.md`
4. `ROADMAP.md`
5. `docs/architecture/overview.md`
6. All relevant accepted ADRs under `docs/decisions/`

Then inspect the current repository tree, recent commits, Git status, and latest GitHub Actions results. Follow any additional instructions in `AGENTS.md`.

Do not rely on previous conversations or provider-specific agent memory. The repository is the source of truth. Verify documentation against the actual implementation and CI evidence; clearly identify stale or conflicting information.

Do not modify files, create commits, push, or open pull requests during this recovery pass.

Return a concise recovery report with these sections:

1. **Project** - what PLAT is and what problem it is intended to solve.
2. **Architecture** - current Host/runtime model, module packaging, Platform API direction, portability targets, and key security boundaries.
3. **Current phase** - the phase and overall status from `STATE.md`.
4. **Implemented** - what demonstrably exists in the repository.
5. **Not implemented** - planned components that do not exist yet.
6. **Verification** - latest CI result and checks actually observed. Do not infer success from workflow files alone.
7. **Next increment** - the single next action and its acceptance criteria from `STATE.md`.
8. **Discrepancies** - any mismatch between documentation, code, Git state, and CI.

End by stating whether the repository contains enough information to continue without access to the original conversation. Do not begin implementation until the owner asks you to proceed.
