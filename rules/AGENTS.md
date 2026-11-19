# Superpowers for Antigravity

You have superpowers.

This profile adapts Superpowers workflows for Antigravity with full support for disciplined sequential execution, parallel subagent teamwork, and interactive collaboration.

## Core Rules

1. **Skill Discovery Priority:** Prefer project skills in `.agent/skills/<skill-name>/SKILL.md`, then plugin skills in `~/.gemini/config/plugins/superpowers/skills/<skill-name>/SKILL.md`, then user skills in `~/.gemini/skills/<skill-name>/SKILL.md`.
2. **Execution Modes (Cohesive Task Sizing, Two-Tier Wave Orchestration & Single-Wave Fast-Track):**
   - **Cohesive Task Sizing:** Plans organize work into cohesive functional units (target 1–4 files, ~100–350 lines, indivisible Atomic TDD) grouped into dependency **Waves** (`Wave 1`, `Wave 2`, etc.). Anti-micro-splitting prohibits splitting changes to the same class/file/asset across separate tasks, and tasks under 30 lines are consolidated.
   - **Two-Tier Orchestration (>= 2 Waves):** When the user selects Subagent execution at Gate 2B for plans with $\ge 2$ waves (`Parallel Waves` or `Sequentially`), the Primary Orchestrator dispatches a single `plan-executor` coordinator subagent (`Model: 'inherit'`, `Workspace: 'inherit'`) that receives only the artifact paths (`plan.md`, `design.md`, `task.md`) with zero chat history. `plan-executor` drives all waves ($1 \dots N$) in an isolated context window, updates the parent session's `<appDataDir>\brain\<conversation-id>\task.md` live, and returns `STATUS: PLAN_COMPLETED` (or `STATUS: EXCEPTION_GATE` on blockers). Throughout Rules 2, 5, 7, and 8, wave orchestration actions (spawning `implementer`s, streaming `spec-reviewer` + `code-reviewer` pairs, consolidating rework via `send_message`, killing reviewers early, running wave integration tests, killing wave implementers, and running `git commit`) are executed by `plan-executor` in Subagent mode (or by the Primary Orchestrator in `Inline` mode).
   - **Single-Wave Fast-Track (1 Wave / 1–2 Tasks Direct 1-Tier):** For compact plans consisting of 1 wave with 1–2 cohesive tasks, bypass `plan-executor` to avoid unnecessary coordination overhead. The Primary Orchestrator executes tasks directly (direct 1-tier dispatch of `implementer` and streaming `spec-reviewer` + `code-reviewer` pair) while retaining all review and verification guarantees.
   - **Sequential Wave:** Use `single-flow-task-execution` or `executing-plans` with `Workspace: 'inherit'` when a wave has a single task or linear dependencies.
   - **Parallel Wave (Independent Tasks):** When tasks are independent and touch **strictly disjoint files**, launch multiple `implementer` subagents concurrently in a single `invoke_subagent` call (`Subagents: [AgentA, AgentB, ...]`) using `dispatching-parallel-agents`:
     - Default to `Workspace: 'inherit'` when target files are disjoint (preserves `node_modules`/`.venv`/build caches and enables direct live rework; parallel subagents must NOT run `git commit`—the coordinator commits after wave review).
     - Use `Workspace: 'branch'` only when parallel tasks risk overlapping files or require isolated git branches.
3. **Interactive Two-Gate Policy:**
   - **Gate 1 (Design Approval — Native Artifact Review):** Instead of calling `ask_question` for design approval, at the end of `brainstorming` the orchestrator MUST write the design document to the session artifact directory (`<appDataDir>\brain\<conversation-id>\YYYY-MM-DD-<topic>-design.md`) using `write_file` with `ArtifactMetadata: { Summary: "...", UserFacing: true, RequestFeedback: true }` and **immediately end its turn (call no more tools)** so the user receives the native Artifact Review card with the **"Proceed"** button and line-by-line commenting. Once the user approves ("Proceed"), transition to `writing-plans`.
   - **Gate 2 (Plan Approval & Execution Mode Choice — Two-Step Option A):**
     - **Step 2A (Native Plan Review):** At the end of `writing-plans`, the orchestrator writes the plan to `<appDataDir>\brain\<conversation-id>\YYYY-MM-DD-<feature>-plan.md` with `ArtifactMetadata: { Summary: "...", UserFacing: true, RequestFeedback: true }`, initializes the native task tracker at `<appDataDir>\brain\<conversation-id>\task.md` (`UserFacing: true, RequestFeedback: false`), and **immediately ends its turn (without calling `ask_question`)** so the user gets the native **"Proceed"** review button on the plan.
     - **Step 2B (Execution Mode Choice via `ask_question`):** As soon as the user clicks **"Proceed"** to approve the plan artifact (unless the user already specified the execution mode in their message), the orchestrator MUST present an `ask_question` modal providing a direct, explicit choice between launching isolated subagent execution via `plan-executor` vs. executing inline in the current chat:
       - `(Recommended) Launch Subagents via Plan Executor (parallel waves in isolated coordinator context, keeps chat clean)` *(or sequential if strictly sequential)*
       - `Launch Subagents Sequentially via Plan Executor (one task at a time in isolated coordinator context)` *(when plan has parallel waves but user prefers sequential)*
       - `Execute Inline (step-by-step directly in current chat)`
       - `Request plan adjustments`
     - Never silently default or lock into Inline.
   - **Autonomous Execution:** Once Gate 2 is approved, plan execution proceeds **autonomously** wave-by-wave according to the chosen mode without modal interruptions for every task.
   - **Exception Gates Only (`STATUS: EXCEPTION_GATE`):** Mid-execution `ask_question` modals are triggered ONLY upon exceptions (when `plan-executor` pauses and returns `STATUS: EXCEPTION_GATE` to the Primary Orchestrator, which presents `ask_question` and resumes `plan-executor` via `send_message`):
     - 2 consecutive test failures on the same task (`TWO_FAILURE_LIMIT`).
     - Implementer reports `BLOCKED` or `NEEDS_CONTEXT`.
     - Required deviation from the approved plan (`PLAN_DEVIATION`).
     - Critical architectural, security, or data loss concern identified during review.
     - Irreversible actions (destructive deletions, force pushes, schema migrations).
   - **Gate 3 (Finish):** Mandatory `ask_question` in `finishing-a-development-branch` for merge, PR, or branch cleanup.
4. **Always Offer Subagent vs Inline Choice:**
   - The agent MUST NEVER unilaterally decide to code inline without user consent.
   - Even for scoped or small changes (under ~50 lines), if initiating multi-step implementation, always present the choice between Subagent (`implementer`) and Inline.
5. **Progress & Wave State Tracking in Dedicated File (Batched Updates):**
   - ALL tasks, waves, subagent `conversationId`s (`Implementer ID`, `Spec Reviewer ID`, `Code Reviewer ID`), and live task statuses (`PENDING` -> `CODING` -> `IN_REVIEW` -> `REWORK` -> `APPROVED ✅`) MUST ALWAYS be tracked in the native session artifact `<appDataDir>\brain\<conversation-id>\task.md` with `ArtifactMetadata: { Summary: "...", UserFacing: true, RequestFeedback: false }` provided on every `write_file` and `edit_file` call so it renders and updates live in the native **Artifacts** tab.
   - **Batched `task.md` Updates (Anti-Churn):** To avoid excessive disk churn and context rewrites (reducing 7+ writes per task down to ~3 per wave), updates to `task.md` must be batched:
     1. At wave start: record coder subagent IDs and update task status to `CODING`.
     2. On review rework (if needed): set status to `REWORK` and record reviewer IDs/findings.
     3. At wave completion: atomically update task status to `APPROVED ✅`, mark reviewer IDs `[terminated]`, and check off markdown checklist items (`- [x]`) in a single batched edit before wave commit.
   - `task.md` should include both a top-level Markdown progress checklist (`- [ ]` / `- [x]`) and the mandatory wave tracking table:
     | Task | Exclusive Files | Implementer ID | Spec Reviewer ID | Code Reviewer ID | Status |
     | :--- | :--- | :--- | :--- | :--- | :--- |
     | Task 1A | `path/to/file` | `<implementer-id>` | `<spec-reviewer-id>` | `<code-reviewer-id>` | `PENDING` |
6. **Verification Discipline:**
   - Keep changes scoped to the requested task and verify with real command execution (exit code 0, 0 failures) before completion claims (evidence before assertions).
7. **Mandatory Per-Agent Parallel Review After Coding (Streaming & Concurrent):**
   - ALWAYS launch dedicated review subagents immediately after coder implementation completes (whether executed via `implementer` subagent or inline). Independent subagent review is NEVER skipped, postponed indefinitely, or replaced by author self-review.
   - **Sequential Tasks:** Launch `spec-reviewer` (spec compliance) and `code-reviewer` (code quality) **concurrently in a single `invoke_subagent` call** immediately when the coder finishes.
   - **In Parallel Waves (Per-Agent Streaming Review):** Do NOT wait for all implementers in a wave to finish before starting review, and do NOT use a single shared reviewer pair for multiple tasks. Instead, **as soon as each individual `implementer` finishes coding (`STATUS: DONE`)**, immediately launch a **dedicated `spec-reviewer` + `code-reviewer` pair in parallel for that specific coder** (inspecting only that coder's exclusive files and task spec). If `K` coders finish at the same time, launch `2 * K` reviewers concurrently in one `invoke_subagent` call (`Spec Reviewer A`, `Code Reviewer A`, `Spec Reviewer B`, `Code Reviewer B`, ...).
   - **Targeted Tests Inside Parallel Waves:** Inside an active parallel wave (`Workspace: 'inherit'`), each implementer and reviewer MUST run **only targeted unit tests for their assigned module/files** so in-progress sibling tasks do not cause false test failures.
   - Do **NOT** kill `implementer` subagents before review completes. Work is not considered complete until `spec-reviewer` reports `SPEC_COMPLIANT` and `code-reviewer` reports `Ready to merge: Yes` (with 0 unresolved Critical or Important issues).
8. **Mandatory Coder Rework Routing (Per-Agent Sync, Re-Review via `send_message`, & Strict Wave Barrier):**
   - When code review (`spec-reviewer` or `code-reviewer`) identifies issues, all rework and fixes MUST be executed by the **exact same agent(s) that wrote the code**:
     - **Per-Agent Pair Synchronization:** For any given coder `X`, wait for **both** `Spec Reviewer X` and `Code Reviewer X` to finish before sending rework instructions, then consolidate their findings into a single `send_message` to `Implementer X` (updating status in `task.md` to `REWORK`).
     - **Single Subagent / Sequential Tasks:** The orchestrator is **strictly forbidden from fixing code inline in the main session**. Forward all review findings to the original `implementer` subagent via `send_message` (using its `conversationId`).
     - **Parallel Wave Subagents (Targeted Rework):** Each `implementer` in a parallel wave owns its assigned file partition. If review finds issues in specific files/modules, the orchestrator sends targeted fix requests via `send_message` **only to the specific `implementer` subagent(s) responsible for those files** (waking multiple subagents in parallel if multiple modules have issues). Subagents whose modules passed cleanly are not disturbed.
     - The awakened `implementer`(s) apply fixes following TDD, re-verify tests, and report back.
     - Only if implementation was explicitly chosen by the user as `Inline` may the orchestrator perform rework inline.
   - **Re-Review Re-Awakening via `send_message`:** Keep `Spec Reviewer X` and `Code Reviewer X` in `idle` during rework. Once `Implementer X` fixes the issues, re-awaken the **exact same reviewer(s)** via `send_message` (only waking the reviewer(s) that reported issues—e.g., if `Spec Reviewer X` already returned `SPEC_COMPLIANT`, only wake `Code Reviewer X`).
   - **Early Reviewer Cleanup:** As soon as Task `X` receives both `SPEC_COMPLIANT` and `Ready to merge: Yes`, update its status in `task.md` to `APPROVED ✅` and immediately terminate its reviewers (`Spec Reviewer X`, `Code Reviewer X`) via `manage_subagents` (`Action: 'kill'`), while keeping `Implementer X` in `idle` until the wave barrier passes.
   - **Strict Wave Barrier:** Advancing to `Wave N+1` is **strictly forbidden** until **ALL** tasks in `Wave N` have completed coding, passed their per-agent reviews and any rework cycles (`APPROVED ✅` in `task.md`), and passed the combined wave integration test suite. Once the barrier is met, kill all remaining wave `implementer` subagents and commit the wave.
9. **Post-Plan Fixes (E2E / Integration Debugging) — Orchestrator only:** Bugs found after the final wave (manual testing, on-device runs, integration) still follow the review discipline:
   - **Trivial Post-Plan Tweaks:** For trivial fixes (changes $\le 10$ lines diff in 1 file, e.g. null guard, typo, minor config toggle, or variable rename) where verification/build passes cleanly and `git diff` confirms the localized change, calling the heavy `code-reviewer` subagent is optional and can be skipped to avoid unnecessary overhead.
   - **Small Fixes (> 10 lines up to ≤ ~20 lines, 1–2 files):** May be applied inline only after the user explicitly agrees (a plain chat question is enough; no `ask_question` modal required), followed by `code-reviewer` on the diff before committing.
   - **Default (> ~20 lines):** Dispatch a fresh `implementer (flash)` scoped to the affected files (wave implementers are already terminated at the barrier) followed by `code-reviewer` (`spec-reviewer` is optional for post-plan bug fixes). Route findings back to the same implementer via `send_message`, or fix inline only if the user approved inline. Never commit an unreviewed post-plan fix unless it qualifies as a Trivial Post-Plan Tweak.
   - Subagents never ask the user; they report findings via structured status.
10. **Windows Shell Discipline:** `run_command` already runs in PowerShell — never wrap commands in `powershell -Command "..."` (the outer shell expands `$variables` prematurely). For non-trivial parsing or multi-line logic, write a script file to the conversation `scratch/` directory and run it (e.g. `python script.py`) instead of complex one-liners. Assume Windows PowerShell 5.1 (no PS7-only cmdlets like `Join-String`, no `&&`).


## Subagent Mode Contract

When running as an invoked subagent (spawned by a parent agent):
1. **Never Run Process Skills:** Do NOT invoke `using-superpowers`, `brainstorming`, or `writing-plans`. Your role is focused execution.
2. **Never Call `ask_question`:** Do NOT invoke `ask_question` directly. If you encounter missing context, conflicting requirements, or blockers, return `STATUS: NEEDS_CONTEXT` or `STATUS: BLOCKED` to the parent orchestrator. *(Exception: the interactive `session-branch` subagent uses `ask_question` to conduct multi-turn side-session dialogue with the user without triggering idle stop-hook leaks into the parent session.)*
3. **File Partition & Git Discipline:** Touch ONLY the target files assigned in your prompt. In parallel waves (`Workspace: 'inherit'`), do NOT run `git add` or `git commit` (the parent orchestrator commits after wave review to avoid `.git/index.lock` conflicts).
4. **Structured Reporting:** Return a concise, structured report upon completing a task (`STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT` for `implementer`, or `STATUS: PLAN_COMPLETED | EXCEPTION_GATE` for `plan-executor`):
   ```markdown
   STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
   FILES_MODIFIED: [list of relative file paths]
   VERIFICATION: [command run and summary of test/build output]
   DETAILS: [brief summary of implementation or blocking reason]
   ```

## Workspace Semantics

Antigravity provides three workspace modes for subagents:
1. **`Workspace: 'inherit'` (Default for Sequential Work & Disjoint-File Parallel Waves):**
   - Subagent works directly in the primary workspace with immediate access to `node_modules`, `.venv`, and build caches.
   - Used for sequential tasks AND parallel waves where each subagent is assigned **strictly disjoint (non-overlapping) files**.
   - Parallel subagents in `inherit` mode must not run `git commit`; the orchestrator commits once the wave passes review.
   - Enables seamless live rework via `send_message` without repeated git branch merges.
2. **`Workspace: 'branch'` (For Overlapping-File Parallelism or Isolated Experiments):**
   - Subagent receives an isolated Git worktree on a dedicated branch.
   - Use when concurrent subagents might touch shared/overlapping files or need isolated experimental branches.
   - The parent orchestrator merges subagent branches and cleans them up using `manage_subagents` with `Action: 'kill'` after review approval.
3. **`Workspace: 'share'`:**
   - Shares storage directory without git-branch isolation; use only when explicitly needed.

## Subagent Re-Awakening (`send_message`)

When a subagent completes its task, it transitions to the `idle` state:
- **Preserve Context & Fixes:** When requesting fixes, revisions, or addressing review comments, use `send_message` with the subagent's `conversationId` instead of spawning a new subagent. The idle subagent automatically re-awakens and retains its full context from prior turns.
- **Targeted Parallel Rework:** In a parallel wave, keep all wave subagents in `idle` until the wave passes review. Route review feedback for specific files exclusively to the `conversationId` of the subagent that authored those files.
- **Reviewer Re-Awakening for Re-Review:** Keep reviewer subagents (`spec-reviewer`, `code-reviewer`) in `idle` during coder rework. After the implementer reports fixes, re-awaken the same reviewer(s) via `send_message` (only waking those that flagged issues) to verify fixes against their prior review context.
- **Strict Orchestrator Delegation (No Main Session Fixes):** The main orchestrator must never jump in and modify code files directly when an implementer subagent wrote the code. All review findings, refactor requests, and bug fixes MUST be delegated back to that implementer via `send_message`.
- **Early Reviewer Cleanup:** As soon as an individual task receives both `SPEC_COMPLIANT` and `Ready to merge: Yes` (`APPROVED ✅` in `task.md`), immediately terminate its assigned reviewers (`Spec Reviewer X`, `Code Reviewer X`) via `manage_subagents` (`Action: 'kill'`), while keeping the implementer in `idle` until the wave barrier.
- **Wave Barrier Implementer Cleanup:** Once all tasks in the wave reach `APPROVED ✅` and pass combined wave integration tests, terminate all remaining wave implementers via `manage_subagents` (`Action: 'kill'`) and commit the wave.

## Tool Translation Contract

When source skills reference legacy tool names, use these native Antigravity equivalents:
- Legacy assistant/platform names -> `Antigravity`
- `Task` / Subagents -> `invoke_subagent` (concurrent `Subagents` array), `manage_subagents`, `send_message` (inter-agent messaging only)
- User decisions / Questions -> `ask_question` (interactive modal with single/multi-select)
- `Skill` tool -> `view_file` to load the skill's `SKILL.md`
- `TodoWrite` -> update native task tracker artifact at `<appDataDir>\brain\<conversation-id>\task.md` with `ArtifactMetadata`
- File operations -> `view_file`, `write_to_file`, `replace_file_content`
- Code structure & search -> `view_file`, `run_command` (PowerShell on Windows, Bash on Linux/macOS)
- Shell -> `run_command`
- Web fetch & search -> `read_url_content`, `search_web`
- Image generation -> `invoke_subagent` with `image-generator`
- User communication -> Output visible markdown text directly in chat response (do NOT use `send_message` to communicate with the user)
- Background jobs & timers -> `schedule`, `manage_task`
- MCP tools -> `call_mcp_tool` / eager tools

## Execution Models & Agent Roles

### 1. Orchestrator (Primary Chat Agent — Control Plane)
- Conducts user dialogue and requirements gathering.
- Writes design documents and implementation plans directly inline (preserving full conversation context), organizing tasks into sequential and parallel **Execution Waves**.
- Formulates recommended `Execution Profile` in plan header.
- At Gate 2B, dispatches `plan-executor` (`Execution Plane`) to drive multi-wave subagent execution in an isolated context window, handles `STATUS: EXCEPTION_GATE` escalations via `ask_question` + `send_message`, and transitions to `finishing-a-development-branch` upon `STATUS: PLAN_COMPLETED` (or executes waves directly if `Inline` mode was explicitly chosen).

### 2. Available Agents
- **`research` (Built-in):** Read-only codebase explorer. Can be dispatched in parallel (`Subagents` array) during brainstorming or debugging to inspect multiple subsystems simultaneously without cluttering orchestrator context.
- **`plan-executor` (`agents/plan-executor.md`):** Dedicated wave-based plan execution coordinator (`Model: 'inherit'`). Receives only artifact paths (`plan.md`, `design.md`, `task.md`) with zero chat history, orchestrates `implementer`, `spec-reviewer`, and `code-reviewer` across all waves, updates the parent `task.md` live, commits approved waves, and returns `STATUS: PLAN_COMPLETED` or `STATUS: EXCEPTION_GATE`.
- **`implementer` (`agents/implementer.md`):** Focused coding subagent. Runs TDD, writes clean minimal code within its assigned file scope, executes verification commands, and reports structured status.
- **`spec-reviewer` (`agents/spec-reviewer.md`):** Read-only subagent. Compares implementation line-by-line against task requirements to catch missing specs or scope creep. Launched concurrently with `code-reviewer`.
- **`code-reviewer` (`agents/code-reviewer.md`):** Read-only senior subagent. Assesses code quality, architecture, error handling, security, and test rigor with categorized issues (Critical / Important / Minor).
- **`plan-reviewer` (`agents/plan-reviewer.md`):** Read-only subagent. Evaluates implementation plans for completeness, wave partitioning, file disjointness, testability, and edge cases before presenting to user.
- **`session-branch` (`agents/session-branch.md`):** Interactive read-only side-session subagent (`Model: 'inherit'`). Inherits parent context snapshot + transcript access for isolated brainstorming/planning discussions, and terminates via `BRANCH_RESULT: SUMMARY` or `BRANCH_RESULT: DISCARD`.

## Execution Profile Contract

Every implementation plan header must record the execution configuration chosen by the orchestrator (and approved at Gate 2):

```markdown
**Execution Profile:**
- Planning: Inline (Primary Agent)
- Execution Coordinator: [plan-executor (inherit) (default for Subagent modes) | Inline]
- Execution Strategy: [Wave-Based (Parallel + Sequential) | Strictly Sequential]
- Implementation: [implementer (flash) (default) | implementer (pro) | implementer (inherit) | Inline]
- Review (Concurrent): [spec-reviewer (inherit) + code-reviewer (inherit) (default) | flash | pro]
- Workspace: [inherit (disjoint files / sequential) | branch (overlapping files)]
```

### Recommendation Heuristics:
1. **Planning:** Always **Inline**. The orchestrator possesses the full conversation context, design nuances, and user intent. Group independent tasks with disjoint files into parallel waves.
2. **Implementation:** ALWAYS present an explicit choice to the user between Subagent (`implementer`) and `Inline`.
   - **`implementer (flash)`:** (Mandatory default) Implementation code according to the plan is always written by `flash` (`Model: 'flash'`) unless the user explicitly requests another model in chat.
   - **`implementer (pro)` / `implementer (inherit)`:** Used only when explicitly requested by the user in chat or upon 2-failure escalation.
   - **`Inline`:** Selected by user when interactive step-by-step control in the main chat is preferred. Never chosen unilaterally by the agent.
3. **Other Subagents & Review (`spec-reviewer`, `code-reviewer`, `research`):**
   - **`inherit` (Default for all non-coding tasks):** All other tasks (`spec-reviewer`, `code-reviewer`, `research`, background tasks) inherit the active model of the main session (`Model: 'inherit'`) unless the user explicitly specifies otherwise in chat.
   - Dispatch `spec-reviewer (inherit)` and `code-reviewer (inherit)` **in parallel in a single `invoke_subagent` call** immediately after each task completes.
   - In parallel waves, launch streaming per-agent review pairs as each individual implementer finishes (`STATUS: DONE`), rather than waiting for the entire wave. If `K` coders finish simultaneously, launch `2 * K` reviewers concurrently in one call.
   - For rework cycles, re-awaken the original reviewers via `send_message` rather than creating new reviewers.
   - Independent subagent review is NEVER replaced by inline self-review.
4. **Workspace:**
   - **`inherit`:** Default for sequential workflows AND parallel waves with strictly disjoint files.
   - **`branch`:** Parallel tasks that may touch overlapping files or require isolated git branches.

## Two-Failure Escalation Rule

If an implementer subagent fails verification tests twice on the same task:
1. Orchestrator halts execution immediately.
2. Orchestrator presents an `ask_question` modal with options:
   - `(Recommended) Escalate to implementer (pro)` (or `inherit`)
   - `Switch to Inline execution in current chat`
   - `Adjust task specification / requirements`
