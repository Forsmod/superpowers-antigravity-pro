---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same underlying repository, allowing work on multiple branches simultaneously without switching branches in your main checkout.

> **Tip (Antigravity Native Subagents):** When dispatching tasks via `invoke_subagent`, you can specify `Workspace: 'branch'` (isolated cloned branch) or `Workspace: 'share'` (git-worktree style shared repository) directly, letting Antigravity manage workspace creation and cleanup automatically.

**Core principle:** Directory selection + safety verification = reliable workspace isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories
Check for existing worktree folders (`.worktrees/` or `worktrees/`):
- Cross-platform check:
  - PowerShell: `Test-Path .worktrees` or `Test-Path worktrees`
  - Bash: `test -d .worktrees || test -d worktrees`

If found, use the existing directory (`.worktrees` preferred if both exist).

### 2. Check AGENTS.md
Check if a worktree directory preference is documented in `AGENTS.md`. If so, use it.

### 3. Ask User via `ask_question`
If no existing directory is found, ask the user:

```json
{
  "questions": [
    {
      "question": "No worktree directory found. Where should I create isolated git worktrees?",
      "options": [
        "(Recommended) .worktrees/ (project-local, hidden folder)",
        "worktrees/ (project-local, visible folder)",
        "~/.config/superpowers/worktrees/<project-name>/ (global location outside repo)"
      ],
      "is_multi_select": false
    }
  ]
}
```

## Safety Verification

### For Project-Local Directories (`.worktrees` or `worktrees`)
**MUST verify directory is ignored before creating worktree:**

```bash
git check-ignore -q .worktrees || git check-ignore -q worktrees
```

**If NOT ignored:**
1. Add `.worktrees/` (or `worktrees/`) to `.gitignore`.
2. Commit the `.gitignore` update.
3. Proceed with worktree creation.

*Why critical:* Prevents accidentally tracking nested worktree files inside the parent repository.

## Creation Steps

### 1. Create Worktree with New Branch

```bash
git worktree add "<path-to-worktree>" -b "<branch-name>"
```

### 2. Verify Baseline Tests

Before writing new code in the worktree, run the test suite to ensure the baseline is clean:
```bash
# Run project's test command (e.g. npm test, cargo test, pytest)
```
- If tests pass: proceed with implementation.
- If tests fail: report failures to the user before making changes.

## Integration

- **Called by:** `brainstorming`, `single-flow-task-execution`, `executing-plans`.
- **Pairs with:** `finishing-a-development-branch` (for merging and worktree cleanup).
