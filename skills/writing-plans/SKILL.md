---
name: writing-plans
description: Use when you have a design or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive, cohesive implementation plans. Document everything needed: target files to create/modify, code snippets, failing tests, exact verification commands, and dependency ordering. Follow DRY, YAGNI, TDD, and small verifiable steps.

The primary orchestrator drafts the plan **inline** to preserve the full conversation context and nuances from brainstorming.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Plan Destination & Mandatory Task Tracking:**
- Save the plan document as a native session artifact at `<appDataDir>\brain\<conversation-id>\YYYY-MM-DD-<feature-name>-plan.md` using `write_file` with:
  ```json
  "ArtifactMetadata": {
    "Summary": "Implementation plan for <feature-name>",
    "UserFacing": true,
    "RequestFeedback": true
  }
  ```
- In addition to the plan document, all tasks and wave execution states MUST ALWAYS be tracked in the native session artifact `<appDataDir>\brain\<conversation-id>\task.md` with:
  ```json
  "ArtifactMetadata": {
    "Summary": "Task progress and wave state tracking",
    "UserFacing": true,
    "RequestFeedback": false
  }
  ```
  provided on every `write_file` and `edit_file` call.
- The `task.md` artifact must include both a high-level Markdown checklist (`- [ ]` / `- [x]`) and the live wave status table:
  ```markdown
  ### Checklist
  - [ ] Task 1A: Setup foundation
  - [ ] Task 1B: Core implementation

  ### Wave Status
  | Task | Exclusive Files | Implementer ID | Spec Reviewer ID | Code Reviewer ID | Status |
  |------|-----------------|----------------|------------------|------------------|--------|
  | 1A   | path/to/file.ts | subagent-123   | subagent-456     | subagent-789     | IN_REVIEW |
  ```
  Status values transition through: `PENDING` -> `CODING` -> `IN_REVIEW` -> `REWORK` -> `APPROVED ✅`.

## Cohesive Task Sizing & Execution Waves

Organize tasks into dependency **Execution Waves (`Wave 1`, `Wave 2`, ...)** by analyzing dependencies and target file overlap:
1. **Sequential Wave (`[Sequential]`):** Tasks that establish shared interfaces, schemas, or wire components together into a common entry point.
2. **Parallel Wave (`[Parallel — Disjoint Files]`):** Multiple independent tasks that have no sequential dependency on each other AND touch **strictly separate (disjoint) files**.
   - **Targeted Module Tests & Streaming Reviews:** Inside `[Parallel — Disjoint Files]` waves, each task's verification step runs **targeted module tests** (rather than a full test suite) to maximize speed and isolation. Each task is reviewed immediately upon coder completion by its own dedicated `spec-reviewer` + `code-reviewer` pair.
   - **Strict Wave Synchronization Barrier:** All tasks within the wave must reach `APPROVED ✅` in `task.md` and pass the combined wave integration test before the orchestrator commits and advances to the next wave.
   - **Shared Glue File Rule:** If independent tasks (e.g., creating 3 separate modules) also need to register themselves in a single shared file (e.g., `index.ts`, `routes.ts`, `CMakeLists.txt`), keep module creation and unit tests in the `[Parallel]` wave, and extract the shared-file registration into the subsequent `[Sequential]` wave to guarantee zero file collisions.
   - **Shared-Type Ripple Rule:** When a task changes a shared type or contract (sealed/sum-type variants, enum values, interface/abstract signatures, constructor/record fields, public function signatures, DB/JSON schemas), find every consumer that must change to keep the build green (exhaustive `switch`/`match`/`when`, implementations, call sites — e.g. via `git grep`) and include those files in that same task's exclusive scope. If such a consumer is owned by a sibling task in the same wave or by a later-wave task, either move the minimal compile fix into the current task or reorder waves. Never leave a wave in a non-compiling state.

## Cohesive Task Sizing & Anti-Micro-Splitting Rules

Every task must represent a meaningful, cohesive, testable increment. Avoid excessive fragmentation (micro-splitting) that produces unnecessary agent roundtrips, review overhead, or race conditions:

1. **Cohesive Task Sizing (Target ~100–350 lines, 1–4 files, 2–5 verification scenarios):**
   - The ideal task size is ~100–350 lines of combined implementation and test code across 1–4 files with 2–5 verification scenarios.
   - Tasks should bundle cohesive logical changes rather than splitting trivial pieces across multiple steps.

2. **Anti-Same-File Splitting Rule:**
   - Strict prohibition against splitting changes to the same class/file/asset across multiple tasks or waves.
   - If a class, file, or asset requires modifications, all edits to that entity should be made within a single task unless there is an insurmountable architectural dependency. Never split changes to the same file across consecutive tasks or waves.

3. **Atomic TDD Rule:**
   - Schema/DTO definitions, underlying service logic, and corresponding unit tests are indivisible and must belong to a single task.
   - Do NOT create one task for "create DTO/schema" and a separate task for "implement service logic" or "write unit test". An atomic TDD task implements the schema/DTO, the logic, and the tests together.

4. **Hard Floor Against Micro-Splitting (< 30 lines):**
   - Standalone tasks for < 30 lines are strictly prohibited.
   - Trivial modifications—such as adding a config key, `.gitignore` entries, adding a single dependency in `Build.cs`/`package.json`, simple file renames, or a single UI toggle—MUST be bundled into the nearest functional task, never given their own standalone task or wave.

5. **Monolithic Target Build Rule:**
   - In projects with monolithic compile targets (e.g., Unreal Engine / C++ using `Build.bat Engine/Editor -WaitMutex`), if module edits are < 150 lines per file, it is strictly forbidden to split them into parallel C++ tasks in `Workspace: inherit`.
   - Running parallel C++ tasks against a monolithic target leads to compiler mutex lock contention (`-WaitMutex` blocking or aborting sibling compilers). Combine such edits into a single sequential task to avoid compiler mutex lock contention.

6. **Prohibition of Phantom Waves:**
   - Never create artificial or phantom waves such as "Compile Project", "Run Full Build", or "Code Review".
   - Compilation and verification are standard steps within each task; code review is handled automatically by the orchestration workflow (`spec-reviewer` + `code-reviewer`) and must never be scheduled as a plan wave.

7. **Single-Wave Mandatory Rule:**
   - If an entire feature fits in <= 4 files and <= 350 lines without independent branches or conflicting dependencies, the implementation plan MUST be formatted as exactly 1 Wave and 1 Task.
   - Do NOT artificially inflate small, straightforward changes into multi-wave or multi-task plans.

### Task Execution Granularity (TDD)

Each task within a wave follows TDD granularity:
1. "Write failing test"
2. "Run test command to verify failure"
3. "Implement minimal production code"
4. "Run test command to verify success"
5. "Commit changes" *(for parallel waves in `Workspace: 'inherit'`, the orchestrator commits once the wave passes review)*

## Plan Document Header

Every plan MUST include this header with a formulated **Execution Profile**:

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach, components, and data flow]

**Execution Profile:**
- Planning: Inline (Primary Agent)
- Execution Coordinator: plan-executor (inherit) (default for Subagent modes) | Inline
- Execution Strategy: [Wave-Based (Parallel + Sequential) | Strictly Sequential]
- Implementation: [implementer (flash) (default) | implementer (pro) | implementer (inherit) | Inline]
- Review (Concurrent): [spec-reviewer (inherit) + code-reviewer (inherit) (default) | flash | pro]
- Workspace: [inherit (disjoint files / sequential) | branch (overlapping files)]

**Wave Summary:**
- Wave 1 [Sequential]: Task 1 (Shared interfaces / foundation)
- Wave 2 [Parallel — Disjoint Files]: Task 2A (`moduleA`), Task 2B (`moduleB`)
- Wave 3 [Sequential]: Task 3 (Integration & wiring)

**Profile Rationale:** [1-2 sentences explaining why this model, wave structure, and workspace mode fit this task]

**Tech Stack & Dependencies:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
## Wave N: [Wave Name] ([Sequential] OR [Parallel — Disjoint Files])

### Task N.1: [Component Name]

**Files (Exclusive Scope):**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**
```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**
```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit (Orchestrator commits after wave review for parallel waves)**
```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Pre-Approval Plan Review (Required for 2+ Waves / Shared Contracts)

Before presenting the plan, you MUST dispatch the `plan-reviewer` subagent when the plan has 2+ waves OR any task modifies a shared type/contract. For simpler plans it is optional.

```json
{
  "Subagents": [
    {
      "TypeName": "plan-reviewer",
      "Role": "Plan Reviewer",
      "Model": "inherit",
      "Prompt": "Review draft plan: [SUMMARY OF PLAN]. Check for task granularity, wave dependency ordering, strict file disjointness within parallel waves, missing edge cases, and testability."
    }
  ]
}
```

## Gate 2: Mandatory Plan & Execution Choice Gate (Two-Step Option A)

### Step 2A (Native Plan Review via `RequestFeedback: true`):
After running `plan-reviewer` (if applicable), creating `task.md` (`RequestFeedback: false`), and saving the plan artifact (`RequestFeedback: true`), **stop calling tools and end your turn** (do NOT call `ask_question` in the same turn). This triggers Antigravity's native Artifact Review card with the **"Proceed"** button on the plan.

If the user submits comments or requests revisions, update the plan artifact via `edit_file` (with `ArtifactMetadata` and `RequestFeedback: true`) and end turn again.

### Step 2B (Execution Mode Choice via `ask_question` upon Approval):
As soon as the user approves the plan via the native **"Proceed"** button (unless they already specified the execution mode in their message), immediately present the `ask_question` modal providing an explicit choice between Subagents and Inline:

```typescript
ask_question({
  questions: [
    {
      question: "Implementation plan is ready. How would you like to execute the coding tasks?",
      is_multi_select: false,
      options: [
        "(Recommended) Launch Subagents via Plan Executor (parallel waves in isolated coordinator context, keeps chat clean)",
        "Launch Subagents Sequentially via Plan Executor (one task at a time in isolated coordinator context)",
        "Execute Inline (step-by-step directly in this chat)",
        "Request plan adjustments"
      ]
    }
  ]
})
```

*(Note: If the plan has no independent tasks and is strictly sequential, omit the second option and use `(Recommended) Launch Subagents Sequentially via Plan Executor (background TDD execution in isolated coordinator context, keeps chat clean)`.)*

**Never unilaterally begin coding inline without explicit user selection.**
- If the user selects **Launch Subagents via Plan Executor (Parallel Waves)**: invoke `executing-plans` to dispatch `plan-executor` with `ExecutionMode: ParallelWaves`.
- If the user selects **Launch Subagents Sequentially via Plan Executor**: invoke `executing-plans` to dispatch `plan-executor` with `ExecutionMode: SequentialSubagents`.
- If the user selects **Execute Inline**: execute tasks directly in the current session via `executing-plans` (Mode B: Inline) while still launching `spec-reviewer` + `code-reviewer` after each task.
- If the user selects **Request plan adjustments**: revise the plan based on feedback.
