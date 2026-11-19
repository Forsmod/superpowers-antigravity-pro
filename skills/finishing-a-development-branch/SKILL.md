---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by verifying tests, presenting integration options using `ask_question`, and executing the chosen workflow.

**Core principle:** Verify tests → Present options via `ask_question` → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**

```bash
# Run project's test suite (examples)
npm test
cargo test
pytest
go test ./...
```

**If tests fail:**
Stop immediately. Show failures and resolve them before proceeding. Never offer merge/PR options with failing tests.

### Step 2: Determine Base Branch

```bash
git branch --show-current
git merge-base HEAD main 2>&1
```

Confirm the target branch (e.g., `main` or `master`).

### Step 3: Present Options with `ask_question`

Use the `ask_question` tool to present structured choices:

```json
{
  "questions": [
    {
      "question": "Implementation is verified and all tests pass. How would you like to integrate the changes?",
      "options": [
        "(Recommended) Merge back to base branch locally and delete feature branch",
        "Push branch to remote and create a Pull Request (PR)",
        "Keep the feature branch as-is (I will handle it later)",
        "Discard this work"
      ],
      "is_multi_select": false
    }
  ]
}
```

### Step 4: Execute Choice

#### Option 1: Merge Locally
```bash
git checkout <base-branch>
git pull
git merge <feature-branch>
# Run test suite to verify merged state
git branch -d <feature-branch>
```
Then cleanup worktree if one was created.

#### Option 2: Push and Create PR
```bash
git push -u origin <feature-branch>
gh pr create --title "<title>" --body "<summary>"
```

#### Option 3: Keep As-Is
Report: "Keeping branch `<name>`. Worktree/branch preserved."

#### Option 4: Discard
Ask for explicit confirmation before permanently deleting any work.

### Step 5: Cleanup Worktree (if applicable)

If work was done in a git worktree:
```bash
git worktree list
git worktree remove <worktree-path>
```
Note: If using Antigravity's native `Workspace: 'branch'` with subagents, workspace cleanup occurs automatically when the subagents are terminated via `manage_subagents` (`Action: 'kill'`).
