---
name: requesting-code-review
description: Use when completing tasks, implementing features, or before merging to verify work meets requirements using the dedicated code-reviewer subagent
---

# Requesting Code Review

Run an independent review pass using the dedicated `code-reviewer` subagent to catch bugs, regressions, and quality issues before they cascade.

**Core principle:** Always launch a review agent immediately after the coder finishes work. Independent subagent review is mandatory, never skipped, and never replaced with author self-review.

## When to Request Review

**Mandatory:**
- **ALWAYS immediately after the coder finishes implementation** (every task, task batch, or ad-hoc code change)
- Before concluding a plan or completing a feature branch
- Before merging back to main or creating a PR

**Optional but valuable:**
- When stuck on architecture or edge cases
- Before refactoring (baseline health check)
- After fixing a complex bug

## How to Request

### 1. Resolve Review Model

1. **Check the `Execution Profile`** from the plan header:
   ```markdown
   **Execution Profile:**
   - Review (Concurrent): [spec-reviewer (flash) + code-reviewer (pro | inherit | flash)]
   ```
2. **If `Execution Profile` is missing (Ad-Hoc Implementation):**
   - Use `code-reviewer` with `Model: "inherit"` (or `"pro"` for complex/sensitive code).
   - Use `code-reviewer` with `Model: "flash"` for routine boilerplate or small utilities.

### 2. Determine Commit / Diff Range

Identify the base and head commits or modified files:

```bash
git log --oneline -n 5
git diff --stat HEAD~1 HEAD
```

### 3. Dispatch Review Subagents (`spec-reviewer` + `code-reviewer`)

For planned tasks or waves, dispatch `spec-reviewer` and `code-reviewer` **concurrently in a single `invoke_subagent` call** (both are read-only, halving review wait time). For ad-hoc code changes without a formal plan, dispatch `code-reviewer`:

```json
{
  "Subagents": [
    {
      "TypeName": "spec-reviewer",
      "Role": "Spec Reviewer",
      "Model": "flash",
      "Workspace": "inherit",
      "Prompt": "Compare implementation against specification.\n\n## Plan / Requirements\n{PLAN_OR_REQUIREMENTS}\n\n## Modified Files\n{FILES}"
    },
    {
      "TypeName": "code-reviewer",
      "Role": "Code Reviewer",
      "Model": "<inherit | pro | flash>",
      "Workspace": "inherit",
      "Prompt": "Please review the following implementation:\n\n## What Was Implemented\n{WHAT_WAS_IMPLEMENTED}\n\n## Plan / Requirements\n{PLAN_OR_REQUIREMENTS}\n\n## Changes\nBase commit: {BASE_SHA}\nHead commit: {HEAD_SHA}\nModified files: {FILES}\n\nCheck for plan alignment, code quality, edge cases, test quality, and security vulnerabilities."
    }
  ]
}
```

The review subagents inspect the diff and code independently in a clean, read-only context.

#### Parallel Waves (Per-Agent Streaming Review)
When multiple `implementer` subagents run in a wave, **do NOT wait to run a single shared reviewer pair over all tasks**. Instead:
- As soon as each `implementer` finishes (`STATUS: DONE`), immediately launch a dedicated `spec-reviewer` + `code-reviewer` pair in parallel for that specific coder's task spec and modified files (`2 * K` reviewers in one `invoke_subagent` call if `K` coders finish together).
- Record reviewer `conversationId`s (`Spec Reviewer ID`, `Code Reviewer ID`) and update the task status to `IN_REVIEW` in the native session artifact `<appDataDir>\brain\<conversation-id>\task.md` (updated with `ArtifactMetadata: { Summary: "...", UserFacing: true, RequestFeedback: false }`).

### 4. Act on Feedback

When the review reports are returned:
- **Critical issues:** Must fix immediately before proceeding.
- **Important issues:** Must fix before completing the task/feature or merging.
- **Minor / Suggestions:** Address if quick, or note for follow-up.
- **Per-Agent Pair Synchronization:** For any coder `X`, wait for both `Spec Reviewer X` and `Code Reviewer X` to complete before sending consolidated feedback to `Implementer X` via `send_message`. Never send partial feedback piecemeal. Update status to `REWORK` in `task.md`.
- **Fixing via Subagent Re-Awakening (Strict Coder Delegation):**
  - **Single Subagent:** If an `implementer` subagent wrote the code, **the orchestrator is strictly forbidden from fixing code inline in the main session.** Consolidate all findings from `spec-reviewer` and `code-reviewer` and send them directly to the coder subagent via `send_message` with its `conversationId`.
  - **Parallel Wave Subagents (Targeted Rework):** Keep all wave `implementer` subagents in `idle` until review passes. Map each review finding to the `implementer` that owns the affected file(s) and send targeted fix instructions via `send_message` (waking multiple implementers concurrently if multiple modules have issues, while leaving clean modules untouched).
  - **Inline:** Only if code was originally written `Inline` does the orchestrator apply fixes directly in the main chat.
- **Re-Review via `send_message`:** Keep reviewers in `idle` during rework. When `Implementer X` finishes fixes, re-awaken the existing reviewer(s) that flagged issues via `send_message` instead of spawning new reviewers. Update status to `IN_REVIEW` in `task.md`.
- **Early Reviewer Cleanup & Wave Barrier:**
  - Kill `Spec Reviewer X` and `Code Reviewer X` via `manage_subagents` (`Action: 'kill'`) as soon as Task `X` is `APPROVED ✅` in `task.md`.
  - Keep `Implementer X` in `idle` until all tasks in the wave are `APPROVED ✅` and the wave integration test passes.
  - Strict wave barrier: only when all tasks in the wave reach `APPROVED ✅` and the combined wave integration test passes cleanly, kill all wave implementers via `manage_subagents` (`Action: 'kill'`) before advancing to the next wave.
- **Exception Gate:** If a Critical issue requires an architectural change or trade-off decision, present structured options to the user via `ask_question`.

## Integration with Workflows

- **Sequential Execution:** Run concurrent `spec-reviewer` + `code-reviewer` after coder finishes each task.
- **Parallel Waves:** Stream a dedicated `spec-reviewer` + `code-reviewer` pair immediately as each implementer finishes. Follow per-agent pair sync, re-review via `send_message`, early reviewer cleanup upon task approval, and hold the wave barrier (all tasks `APPROVED ✅` + wave integration test passes) before advancing.
- **Ad-Hoc Development:** Run `code-reviewer` immediately after writing code and running tests.
