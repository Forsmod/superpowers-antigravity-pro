# Antigravity Superpowers

An enhanced port and evolution of [`obra/superpowers`](https://github.com/obra/superpowers) for **Google Antigravity** — not just a platform adaptation, but a redesigned agentic workflow featuring two-tier wave orchestration, streaming parallel reviews, targeted subagent rework, cost-optimized model routing, and interactive session branching.

## What's Improved Over Upstream `obra/superpowers`

1. **Two-Tier Wave Orchestration (`plan-executor` + Fast-Track):** Multi-wave plans ($\ge 2$ waves) are delegated to an isolated `plan-executor` coordinator subagent so the primary chat stays clean and compact, while small 1-wave plans (1–2 tasks) take a direct 1-tier fast-track without coordinator overhead.
2. **Cohesive Task Sizing & Anti-Micro-Splitting:** Replaces tiny micro-tasks with cohesive functional units (~100–350 lines, 1–4 files, hard floor of 30 lines) grouped into dependency **Waves**, cutting subagent spawn and review overhead.
3. **Parallel Waves in Disjoint-File `inherit` Mode:** Independent tasks touching strictly disjoint files run concurrently in `Workspace: 'inherit'` (reusing `node_modules`, `.venv`, and build caches without worktree duplication), while overlapping tasks can still isolate via `Workspace: 'branch'`.
4. **Streaming Concurrent Review & Targeted Rework:** As soon as an `implementer` finishes, `spec-reviewer` + `code-reviewer` launch concurrently for that task without waiting for sibling tasks. Rework is routed back to the exact original `implementer` via `send_message`, only the flagging reviewer(s) are re-awakened, and reviewers are terminated early upon approval.
5. **Batched `task.md` Tracking & Strict Wave Barriers:** Wave and task states (`PENDING` → `CODING` → `IN_REVIEW` → `REWORK` → `APPROVED ✅`) update live in `task.md` using batched writes, and `Wave N+1` cannot start until every task in `Wave N` is approved, wave integration tests pass, and the wave is committed.
6. **Native Artifact Review Gates & Autonomous Execution:** Design (`Gate 1`) and plan (`Gate 2A`) approvals use native `RequestFeedback` ("Proceed") cards with line-by-line commenting, followed by an explicit execution-mode choice (`Gate 2B`) and autonomous execution that pauses only on `EXCEPTION_GATE`s (e.g., 2 consecutive test failures, `BLOCKED`, or plan deviations).
7. **Cost-Optimized Model Defaults:** Coding tasks default to `implementer` on `flash`, while planning, orchestration, and reviews default to `inherit`.
8. **Interactive Session Branching (`branching-session`):** New workflow to fork a read-only `session-branch` subagent loaded with parent context (`load_parent_context.py`) for side discussions, returning either `SUMMARY` or `DISCARD` without polluting the main session.
9. **Post-Plan Fix Discipline & Windows PowerShell Support:** Tiered review rules for post-plan fixes (trivial $\le 10$-line tweaks vs. `code-reviewer` / `implementer` dispatch) and built-in Windows PowerShell 5.1 shell discipline.

## Key Features

- **Two-Gate Approval Flow:**
  - **Gate 1 (Design):** `brainstorming` produces a design artifact with native `RequestFeedback` ("Proceed") review before any planning or coding.
  - **Gate 2 (Plan & Mode):** `writing-plans` groups cohesive tasks into dependency **Waves**, then presents native Artifact Review followed by an explicit choice between isolated subagent execution (`plan-executor`) or inline execution.
- **Two-Tier Wave Orchestration:**
  - Plans with $\ge 2$ waves are driven by `plan-executor` in an isolated context window, keeping the primary chat clean.
  - Single-wave plans (1–2 tasks) use a 1-tier fast-track directly from the primary orchestrator.
  - Independent tasks touching disjoint files run in parallel (`Workspace: 'inherit'`), while overlapping tasks can use `Workspace: 'branch'`.
- **Streaming Concurrent Review & Targeted Rework:**
  - Every completed `implementer` task is immediately reviewed in parallel by `spec-reviewer` (spec compliance) and `code-reviewer` (code quality).
  - Rework is routed back to the exact `implementer` that wrote the code via `send_message`, and only the flagging reviewer(s) are re-awakened for re-review.
- **Cost-Optimized Model Defaults:**
  - Coding tasks default to `implementer` on `flash`; planning, orchestration, and reviews default to `inherit`.
- **Interactive Session Branching:**
  - `branching-session` (`session-branch` subagent) lets you spin up an isolated read-only side discussion with parent context snapshot and return either a `SUMMARY` or `DISCARD` without polluting the main session.
- **Live Progress Tracking:**
  - Wave and task states (`PENDING` → `CODING` → `IN_REVIEW` → `REWORK` → `APPROVED ✅`) are tracked live in `task.md`.

## Installation

Clone this repository into your Antigravity plugins directory as `superpowers`:

**Windows (PowerShell):**
```powershell
git clone https://github.com/Forsmod/superpowers-antigravity-pro.git "$env:USERPROFILE\.gemini\config\plugins\superpowers"
```

**macOS / Linux:**
```bash
git clone https://github.com/Forsmod/superpowers-antigravity-pro.git ~/.gemini/config/plugins/superpowers
```

Restart Antigravity (or reload plugins) so `plugin.json`, `rules/AGENTS.md`, `agents/`, `skills/`, and `workflows/` are discovered.

## How to Use

### Typical Development Flow

1. **Brainstorm & Design** — Start a feature by invoking `/brainstorm` (or describing a non-trivial feature; `using-superpowers` triggers `brainstorming`). Review the generated design artifact and click **Proceed** (Gate 1).
2. **Write the Plan** — Run `/write-plan` (or continue after Gate 1). The orchestrator drafts a wave-based plan, optionally audits it with `plan-reviewer`, and presents the plan artifact for **Proceed** (Gate 2A), followed by execution mode selection (Gate 2B).
3. **Execute Waves** — `plan-executor` (or `/execute-plan`) runs each wave autonomously:
   - Dispatches `implementer` subagents (`flash`) following TDD.
   - Streams `spec-reviewer` + `code-reviewer` pairs as each coder finishes.
   - Enforces a strict wave barrier (integration checks + wave git commit) before advancing to the next wave.
   - Escalates to you only on `EXCEPTION_GATE` (e.g., 2 consecutive test failures, `BLOCKED`, or plan deviation).
4. **Finish the Branch** — `finishing-a-development-branch` guides merge, PR creation, or worktree cleanup (Gate 3).

### Side Discussions (`branching-session`)

When you want to explore an idea or clarify architecture without cluttering the main conversation, ask Antigravity to branch the session (triggers `branching-session`). It spawns a read-only `session-branch` subagent loaded with the parent context via `skills/branching-session/scripts/load_parent_context.py`.

## Repository Structure

```text
.
├── plugin.json          # Plugin manifest
├── rules/AGENTS.md      # Core orchestration, wave, review & shell rules
├── agents/              # Custom subagent definitions
│   ├── plan-executor.md
│   ├── implementer.md
│   ├── spec-reviewer.md
│   ├── code-reviewer.md
│   ├── plan-reviewer.md
│   └── session-branch.md
├── skills/              # Modular workflow & discipline skills
│   ├── brainstorming/
│   ├── branching-session/
│   ├── dispatching-parallel-agents/
│   ├── executing-plans/
│   ├── finishing-a-development-branch/
│   ├── receiving-code-review/
│   ├── requesting-code-review/
│   ├── single-flow-task-execution/
│   ├── systematic-debugging/
│   ├── test-driven-development/
│   ├── using-git-worktrees/
│   ├── using-superpowers/
│   ├── verification-before-completion/
│   ├── writing-plans/
│   └── writing-skills/
├── workflows/           # Slash-command entrypoints (/brainstorm, /write-plan, /execute-plan)
├── LICENSE
└── README.md
```

## Credits & License

- Original `superpowers` workflow system by **Jesse Vincent** ([`obra/superpowers`](https://github.com/obra/superpowers)).
- Adapted and extended for Google Antigravity by **Forsmod**.
- Licensed under the [MIT License](LICENSE).
