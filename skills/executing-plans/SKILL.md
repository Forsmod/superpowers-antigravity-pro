---
name: executing-plans
description: Use when you have a written implementation plan and need to execute it systematically via sequential steps or parallel subagent teamwork in Antigravity.
---

# Executing Plans

## Overview

Execute approved implementation plans systematically using a **Two-Tier Orchestration** architecture (**Control Plane** vs. **Execution Plane**) for multi-wave plans, or **Single-Wave Fast-Track** (**1-Tier Execution**) for single-wave plans:

- **Single-Wave Fast-Track (1-Tier Execution):** When an approved plan has 1 wave (up to 2 tasks), do not spawn `plan-executor`. Spawning a coordinator subagent for a single wave adds unnecessary nesting and overhead. Instead, the Primary Orchestrator executes the implementer directly -> launches a parallel `spec-reviewer` + `code-reviewer` pair -> commits the result.
- **Two-Tier Execution (Reserved for Plans with >= 2 Waves):** When a plan has 2 or more waves (>= 2 waves), the Primary Orchestrator delegates wave execution to a single `plan-executor` coordinator subagent (`Model: 'inherit'`, `Workspace: 'inherit'`). `plan-executor` runs in an isolated context window with zero chat history—receiving only artifact paths (`plan.md`, `design.md`, `task.md`) and execution profile. It drives Waves $1 \dots N$ autonomously (spawning `implementer`s, streaming `spec-reviewer` + `code-reviewer` pairs, routing rework via `send_message`, updating parent `task.md` live, enforcing wave barriers, running integration tests, and committing approved waves).
- **Inline Mode (`Mode B: Inline`):** Remains available when explicitly chosen by the user at Gate 2B.

**Core principles:** Two-tier context isolation (`plan-executor` for >= 2 waves) OR single-wave fast-track (1-tier execution for 1 wave) + status batching for `task.md` + targeted coder unit testing + per-agent streaming parallel review + reviewer re-awakening (`send_message`) + strict wave barrier + autonomous wave progression.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 1: Load Plan, Waves, Execution Profile & Initialize `task.md`

1. Read the plan file and identify the **Execution Waves** (`Wave 1`, `Wave 2`, ...). Count the total waves and tasks to determine whether to apply **Single-Wave Fast-Track** (1 wave, up to 2 tasks) or **Two-Tier Execution** (>= 2 waves).
2. Extract the `**Execution Profile:**` from the plan header:
   ```markdown
   **Execution Profile:**
   - Planning: Inline (Primary Agent)
   - Execution Coordinator: [plan-executor (inherit) (for >= 2 waves) | Inline | Single-Wave Fast-Track]
   - Execution Strategy: [Wave-Based (Parallel + Sequential) | Strictly Sequential]
   - Implementation: [implementer (flash) | implementer (pro) | implementer (inherit) | Inline]
   - Review (Concurrent): [spec-reviewer (inherit) + code-reviewer (inherit) (default) | flash | pro]
   - Workspace: [inherit (disjoint files / sequential) | branch (overlapping files)]
   ```
3. **Initialize Dedicated `task.md` Tracking File with Status Batching:**
   Before starting execution, `task.md` MUST be created/updated at `<appDataDir>\brain\<conversation-id>\task.md` using `write_file` / `edit_file` with `ArtifactMetadata: { Summary: "Task progress and wave state tracking", UserFacing: true, RequestFeedback: false }` so that it is always visible and updated live in Antigravity's native **Artifacts** tab.
   
   Populate it with all waves from the plan, including both a top-level Markdown checklist (`- [ ] Task 1A: ...` -> `- [x] Task 1A: ...`) and the live wave status table:
   ```markdown
   # Task Tracking & Wave Status

   ## Progress Checklist
   - [ ] Task 1A: Implement Auth module
   - [ ] Task 1B: Implement Billing module

   ## Wave Status Tables

   ### Wave 1
   | Task | Exclusive Files | Implementer ID | Spec Reviewer ID | Code Reviewer ID | Status |
   | :--- | :--- | :--- | :--- | :--- | :--- |
   | Task 1A | `src/auth/*` | - | - | - | PENDING |
   | Task 1B | `src/billing/*` | - | - | - | PENDING |
   ```
   **Status Batching for `task.md` (60–70% reduction in rewrites):**
   To avoid constant re-rendering and token bloat from 7+ updates per wave, status updates to `task.md` MUST follow status batching:
   - **Update 1 (Wave Start):** Set status to `CODING` and record real `Implementer ID`(s) in one atomic update after spawning.
   - **Update 2 (Issue Gate - REWORK):** Update status to `REWORK` ONLY when reviewers report spec violations or critical/important issues. If reviewers approve cleanly, skip intermediate status writes (`IN_REVIEW`).
   - **Update 3 (Wave Completion):** Set status to `APPROVED ✅` for all tasks in the wave and check off checklist items (`- [x]`) in one atomic edit upon wave completion / approval.
   
   **Status Lifecycle:** `PENDING` -> `CODING` -> [`REWORK` if issues] -> `APPROVED ✅` (or `BLOCKED ⚠️` on exception).
4. **Ensure Execution Mode Choice:** If the user has not yet explicitly chosen between Subagent and Inline (e.g. executing plan ad-hoc), present an `ask_question` modal before writing any code:
   ```typescript
   ask_question({
     questions: [
       {
         question: "How should the tasks be executed?",
         is_multi_select: false,
         options: [
           "(Recommended) Launch Subagents via Plan Executor (parallel waves in isolated coordinator context, keeps chat clean)",
           "Launch Subagents Sequentially via Plan Executor (one task at a time in isolated coordinator context)",
           "Execute Inline (step-by-step in current chat)",
           "Review plan first"
         ]
       }
     ]
   })
   ```
   **Never unilaterally execute inline without user selection.**

---

### Step 2: Execution Dispatch (`plan-executor` Coordinator vs Inline)

#### Mode A: Subagent Execution

##### Mode A.1: Single-Wave Fast-Track (1-Tier Execution)
When an approved plan has 1 wave (up to 2 tasks), do not spawn `plan-executor`. Spawning a coordinator subagent for a single wave creates unnecessary overhead and subagent nesting. Instead, the Primary Orchestrator uses Single-Wave Fast-Track (1-Tier Execution):
1. **Direct Implementer Dispatch:** Primary orchestrator executes implementer directly using `Workspace: 'inherit'` and `Model: <ImplementationModel>`.
2. **Batched task.md Update:** Updates `task.md` with status `CODING` and real returned `Implementer ID`(s) in one atomic update (`ArtifactMetadata` required).
3. **Direct Parallel Review:** Upon coder completion, launches parallel `spec-reviewer` + `code-reviewer` pair directly in a single `invoke_subagent` call.
4. **Rework Routing:** Routes rework (if flagged) directly to the original implementer via `send_message`.
5. **Direct Commit & Completion:** Once approved, marks `APPROVED ✅` and checklist (`- [x]`) in `task.md`, runs integration tests, and commits the result (`git add` and `git commit`).

##### Mode A.2: Two-Tier Execution via `plan-executor` (Reserved for Plans with >= 2 Waves)
Two-Tier Execution is reserved for plans with >= 2 waves. When an approved plan has 2 or more waves, the Primary Orchestrator delegates wave coordination to a single `plan-executor` subagent so intermediate coder/reviewer traffic across multiple waves never bloats the main conversation:

- **Coordinator Context Isolation & Anti-Exploration:** `plan-executor` receives only artifact paths (`PlanArtifactPath`, `DesignArtifactPath`, `TaskArtifactPath`). To prevent truncation of middle waves (`Wave 2+`), `plan-executor` reads `PlanArtifactPath` in chunked line ranges (`StartLine`/`EndLine`). It is strictly forbidden from exploring repository source/test files or running exploratory shell commands (`dir`, `Get-ChildItem`, `where.exe`, `Get-Content`, etc.) before or between waves.

1. **Dispatch `plan-executor`:**
   ```json
   {
     "Subagents": [
       {
         "TypeName": "plan-executor",
         "Role": "Plan Execution Coordinator",
         "Model": "inherit",
         "Workspace": "inherit",
         "Prompt": "Execute the approved implementation plan across all waves.\nParentConversationId: <current-conversation-id>\nPlanArtifactPath: <appDataDir>/brain/<current-conversation-id>/YYYY-MM-DD-<feature>-plan.md\nDesignArtifactPath: <appDataDir>/brain/<current-conversation-id>/YYYY-MM-DD-<feature>-design.md\nTaskArtifactPath: <appDataDir>/brain/<current-conversation-id>/task.md\nExecutionMode: <ParallelWaves | SequentialSubagents>\nImplementationModel: <flash | pro | inherit>\nReviewModel: <inherit | flash | pro>\nFollow your 6 wave state-machine rules strictly. Update TaskArtifactPath with ArtifactMetadata on every state transition. Return STATUS: EXCEPTION_GATE if an exception occurs, or STATUS: PLAN_COMPLETED when all waves are approved and committed."
       }
     ]
   }
   ```
   *(Pre-Restart Fallback)*: If `invoke_subagent(TypeName: "plan-executor")` returns an unknown agent error because Antigravity has not been restarted since `agents/plan-executor.md` was created, call `define_subagent` first (`Name: "plan-executor"`, `Description: "Dedicated wave-based plan execution coordinator"`, `EnableWriteTools: true`, `EnableSubagentTools: true`, `EnableMCPTools: true`, loading `SystemPrompt` from `agents/plan-executor.md`) and then call `invoke_subagent`.
2. **Present Coordinator Link & Wait:**
   - Output a concise message in the main chat with a clickable link to the coordinator session:
     `🚀 Запущен координатор выполнения плана: [plan-executor](conversation://<executor-conversation-id>). Прогресс задач в реальном времени отображается в артефакте task.md.`
   - **End your turn immediately** (call no more tools) and wait for `plan-executor` to wake you.
3. **Handle `plan-executor` Wakeups (`EXCEPTION_GATE` vs `PLAN_COMPLETED`):**
   - **Case 1 — `STATUS: EXCEPTION_GATE` received:**
     - Inspect `WAVE`, `TASK`, `REASON` (`TWO_FAILURE_LIMIT`, `BLOCKED`, `NEEDS_CONTEXT`, `PLAN_DEVIATION`), and `DETAILS`.
     - Present an `ask_question` modal to the user (see Step 4 below).
     - Once the user responds:
       - If the user chooses to continue in subagent mode (e.g., escalate model to `pro`/`inherit`, provide missing context, or adjust task spec), wake the **same** idle `plan-executor` via `send_message(Recipient: "<executor-conversation-id>", Message: "User resolution for <TASK>: ...")` and end your turn to wait.
       - If the user chooses `"Switch to Inline execution in current chat"`, terminate `plan-executor` (and its child subagents) via `manage_subagents(Action: 'kill', ConversationIds: ["<executor-conversation-id>"])` and continue remaining tasks via Mode B (`Inline`).
   - **Case 2 — `STATUS: PLAN_COMPLETED` received:**
     - Immediately terminate `plan-executor` via `manage_subagents(Action: 'kill', ConversationIds: ["<executor-conversation-id>"])`.
     - Proceed directly to Step 5 (`Complete Development` / `finishing-a-development-branch`).
   - **Case 3 — Premature System Idle Notification without `STATUS:`:**
     - If an automatic idle notification arrives before `STATUS: PLAN_COMPLETED` or `STATUS: EXCEPTION_GATE` and `plan-executor` has no running children, wake `plan-executor` via `send_message` instructing it to continue the next pending wave/step in `task.md`.

#### Mode B: Inline Implementation (`Inline`)
When the user explicitly selects `Execute Inline (step-by-step in current chat)` at Gate 2B:
- The Primary Orchestrator executes tasks directly in the current chat session following TDD (`test-driven-development`) and running verification commands via `run_command`.
- Even in `Inline` mode, the Primary Orchestrator MUST update `task.md` (`CODING` -> `IN_REVIEW` -> `REWORK` -> `APPROVED ✅` with `ArtifactMetadata`) and MUST launch concurrent `spec-reviewer` + `code-reviewer` subagents after each task (Step 3).

---

### Step 3: Wave State-Machine Rules (Executed by `plan-executor` in Mode A.2, or Primary Orchestrator in Mode A.1 / Mode B)

#### 0. Dynamic Coalescing Authorization
`plan-executor` (and Primary Orchestrator in Single-Wave Fast-Track) has explicit authority for **Dynamic Coalescing**:
If micro-splitting slipped through the planning phase (e.g. adjacent micro-tasks touching the same file, class, or module in a wave), `plan-executor` is authorized to coalesce adjacent micro-tasks touching the same file/module into a single `implementer` run. This eliminates redundant subagent spawns, context switching overhead, and compilation mutex contention.

#### 1. Wave Coding Dispatch (Mode A.2 inside `plan-executor` or Mode A.1 in Primary Orchestrator)
- **Chunked Plan Reading & Anti-Exploration Discipline:**
  - Before dispatching each wave, read its specific section in `PlanArtifactPath` using `StartLine` and `EndLine` (e.g., 150–250 lines) so task instructions are never lost to middle-file truncation.
  - Never explore repository source/test files or execute exploratory shell commands (`dir`, `Get-ChildItem`, `where.exe`, `Get-Content`, etc.) from `plan-executor`.
- **Atomic Dispatch Order (Invoke First, Real IDs Only):**
  - Do **NOT** write placeholder IDs (`pending`, `dispatching`, `TBD`, `-`) to `task.md` before calling `invoke_subagent`.
  - Always call `invoke_subagent` **first** to spawn the wave's `implementer`(s).
  - Immediately update `task.md` with `CODING` status AND the real returned `Implementer ID`(s) in a single atomic update (`ArtifactMetadata` required), then end your turn to wait for wakeup.
- **Sequential Wave (`[Sequential]`) or `ExecutionMode: SequentialSubagents`:**
  1. Dispatch 1 `implementer` subagent via `invoke_subagent` using `Workspace: 'inherit'`:
     ```json
     {
       "Subagents": [
         {
           "TypeName": "implementer",
           "Role": "Task Implementer",
           "Model": "<flash | pro | inherit>",
           "Workspace": "inherit",
           "Prompt": "Execute Task N from plan: [DETAILS]. Follow TDD. Run verification: [COMMAND]. Return structured report."
         }
       ]
     }
     ```
  2. Immediately update `task.md` status to `CODING` and record the real returned `Implementer ID` (with `ArtifactMetadata: { Summary: "Task progress and wave state tracking", UserFacing: true, RequestFeedback: false }`).
  3. Wait for reactive wakeup, inspect the structured report, keep the subagent in `idle` state, and transition directly to Concurrent Reviews.
- **Parallel Wave (`[Parallel — Disjoint Files]`) when `ExecutionMode: ParallelWaves`:**
  1. Verify that target file scopes for all tasks in the wave have zero overlap (follow `dispatching-parallel-agents`).
  2. Dispatch all `implementer` subagents for the wave **concurrently in a single `invoke_subagent` call** (`Workspace: 'inherit'`).
  3. Immediately update `task.md` status to `CODING` for all tasks in the wave with the real returned conversation IDs (`ArtifactMetadata` required).
  4. **Targeted Coder Unit Tests:** Instruct each parallel implementer to run **only targeted unit tests** for its exclusive file scope and **never run `git add` or `git commit`**:
     ```json
     {
       "Subagents": [
         {
           "TypeName": "implementer",
           "Role": "Implementer Task N.1 (Module A)",
           "Model": "<flash | pro | inherit>",
           "Workspace": "inherit",
           "Prompt": "Execute Task N.1: [DETAILS_A]. EXCLUSIVE FILE SCOPE: [FILES_A]. Do NOT touch other files. Do NOT run git commit. Follow TDD and run targeted unit tests: [TARGETED_COMMAND_A]. Return structured report."
         },
         {
           "TypeName": "implementer",
           "Role": "Implementer Task N.2 (Module B)",
           "Model": "<flash | pro | inherit>",
           "Workspace": "inherit",
           "Prompt": "Execute Task N.2: [DETAILS_B]. EXCLUSIVE FILE SCOPE: [FILES_B]. Do NOT touch other files. Do NOT run git commit. Follow TDD and run targeted unit tests: [TARGETED_COMMAND_B]. Return structured report."
         }
       ]
     }
     ```
  5. **Streaming Review Transition:** Do **NOT** wait for all implementers in the wave before starting reviews. As each completed coder finishes and transitions to `idle`, transition that completed coder immediately into Concurrent Reviews.

#### 2. Launch Concurrent Reviewers (Per Task or Per Completed Coder in a Wave)
Immediately after coding completes for a sequential task or for any completed implementer in a parallel wave:
- **Case 1: Single / Sequential Task:**
  - Launch 1 `spec-reviewer` + 1 `code-reviewer` concurrently in a single `invoke_subagent` call:
    ```json
    {
      "Subagents": [
        {
          "TypeName": "spec-reviewer",
          "Role": "Spec Reviewer Task N",
          "Model": "<inherit | flash | pro>",
          "Workspace": "inherit",
          "Prompt": "Compare implementation of Task N against specification. Target files: [FILES]. Task spec: [SPEC]."
        },
        {
          "TypeName": "code-reviewer",
          "Role": "Code Quality Reviewer Task N",
          "Model": "<inherit | flash | pro>",
          "Workspace": "inherit",
          "Prompt": "Audit implementation of Task N for code quality, architecture, edge cases, security, and test rigor. Modified files: [FILES]."
        }
      ]
    }
    ```
  - Under **Status Batching**, do NOT write intermediate `IN_REVIEW` status to `task.md` if the review proceeds without issues. Avoid noisy intermediate file writes that trigger artifact re-renders.
- **Case 2: Parallel Wave (Per-Agent Streaming Review):**
  - As soon as any `implementer` (or `K` implementers simultaneously) finishes coding in a wave, immediately launch a **dedicated `spec-reviewer` + `code-reviewer` pair for each completed coder in parallel** (`2 * K` reviewers in one `invoke_subagent` call).
  - Each review pair checks **only** that coder's exclusive files (`[FILES_X]`) and spec (`[SPEC_X]`) and runs only targeted tests.

#### 3. Per-Agent Pair Sync & Rework Routing
- **Per-Agent Pair Sync:** Wait for **both** `Spec Reviewer X` and `Code Reviewer X` of a specific coder `X` to complete before taking action on Task `X`.
- **Consolidated Rework Delegation:** If either reviewer flags issues (spec gaps or Critical/Important code quality concerns):
  - Consolidate all findings from both `Spec Reviewer X` and `Code Reviewer X`.
  - Update `task.md` status to `REWORK` for Task `X` (`ArtifactMetadata` required).
  - Route rework to the original coder:
    - If code was written by an `implementer` subagent: **strictly forbidden from fixing code inline**. Forward all consolidated review findings to `Implementer X` via `send_message` with its `conversationId`.
    - If code was written `Inline`: fix the issues directly in the current chat and re-verify.
  - The awakened implementer applies fixes following TDD, re-verifies with targeted unit tests, and reports back.

#### 4. Re-Review via Reviewer Re-Awakening (`send_message`)
- Do **not** spawn brand-new reviewer subagents after rework.
- Keep `Spec Reviewer X` and `Code Reviewer X` in `idle` state.
- Once `Implementer X` reports rework completion, re-awaken via `send_message` **only the reviewer(s) that reported issues**.
- Repeat until both reviewers report approval (`SPEC_COMPLIANT` and `Ready to merge: Yes`).

#### 5. Early Reviewer Cleanup & Strict Wave Barrier
- **Early Reviewer Cleanup:**
  - As soon as Task `X` is fully approved (`SPEC_COMPLIANT` + `Ready to merge: Yes`):
  - Immediately terminate its reviewer pair (`Spec Reviewer X` and `Code Reviewer X`) via `manage_subagents` (`Action: 'kill'`).
  - Keep `Implementer X` in `idle` (do NOT kill implementers until the wave barrier is passed).
- **Status Batching at Wave Completion:**
  - Update all approved tasks in the wave to `APPROVED ✅` and check off checklist items (`- [x] Task X`) in a single atomic edit to `task.md` (`ArtifactMetadata` required). This status batching avoids 7+ updates per wave and reduces rewrites by 60–70%.
- **Strict Wave Barrier:**
  - **Never advance to `Wave N+1` until ALL tasks in `Wave N` are `APPROVED ✅` in `task.md`.**
  - Once all tasks in `Wave N` are `APPROVED ✅`:
    1. Run the combined wave integration test suite in the primary workspace to confirm all modules work together cleanly.
    2. Terminate all `implementer` subagents of `Wave N` via `manage_subagents` (`Action: 'kill'`).
    3. Stage and commit the approved wave changes in git.
    4. Proceed autonomously to `Wave N+1`.

---

### Step 4: Autonomous Progression & Exception Gates

**Autonomous Rule:** As long as tasks/waves pass verification and reviews, **proceed directly to the next wave without interrupting the user**.

**Exception Gate Handling:**
When `plan-executor` returns `STATUS: EXCEPTION_GATE` (or when an exception occurs during `Inline` execution):
1. **Two-Failure Rule (`TWO_FAILURE_LIMIT`):** An implementer fails tests twice on the same task. The Primary Orchestrator presents:
   ```typescript
   ask_question({
     questions: [
       {
         question: "Task N failed tests twice. How should we proceed?",
         is_multi_select: false,
         options: [
           "(Recommended) Escalate to implementer with higher reasoning (pro/inherit)",
           "Switch to Inline execution in current chat",
           "Adjust task spec / test expectations"
         ]
       }
     ]
   })
   ```
2. **Blocked (`BLOCKED` / `NEEDS_CONTEXT`):** Subagent reports `STATUS: BLOCKED` or `STATUS: NEEDS_CONTEXT`. Primary Orchestrator asks the user via `ask_question` and forwards the answer to `plan-executor` via `send_message`.
3. **Plan Deviation / Critical Review Finding (`PLAN_DEVIATION`):** The task requires altering architectural choices or addressing a critical security/architecture defect. Primary Orchestrator confirms with the user via `ask_question` and resumes `plan-executor` via `send_message`.

---

### Step 5: Complete Development

After all waves are implemented, reviewed, and verified (`STATUS: PLAN_COMPLETED` from `plan-executor` or completion of `Inline` waves):
1. Ensure `plan-executor` and all child subagents have been cleaned up via `manage_subagents` (`Action: 'kill'`).
2. Verify that all tasks across all waves in `task.md` are marked `APPROVED ✅` and all items in the progress checklist are checked off (`- [x]`) (passing `ArtifactMetadata: { Summary: "Task progress and wave state tracking", UserFacing: true, RequestFeedback: false }` on `edit_file` if making final updates).
3. Hand off to `finishing-a-development-branch` to present final integration options (merge, PR, branch retention) via `ask_question`.
