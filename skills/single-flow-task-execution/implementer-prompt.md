# Implementer Task Template

Use this template when scoping and executing an implementation task via an isolated `implementer` subagent or inline.

## Subagent Invocation (When Execution Profile specifies `implementer`)

```json
{
  "Subagents": [
    {
      "TypeName": "implementer",
      "Role": "Task Implementer",
      "Model": "<flash | pro | inherit>",
      "Workspace": "inherit",
      "Prompt": "Execute Task N according to this brief.\n\n## Task Description\n[FULL TEXT of task from plan]\n\n## Target Files & Scope\n- Target: [FILES]\n- Tests: [TEST FILES]\n\n## Verification Command\n[COMMAND]\n\nFollow TDD strictly. Run verification command, confirm exit code 0, and return structured status report."
    }
  ]
}
```

## Task Brief Structure

```markdown
## Task N: [task name]

### Task Description
[FULL TEXT of task from plan]

### Context & Dependencies
[Where this fits, dependencies, architectural context]

### Target Files & Scope
- Modify: `path/to/target/file`
- Tests: `path/to/test/file`

### Constraints & Standards
- Follow TDD (test-driven development)
- Minimal changes (YAGNI)
- Run verification command: `[test/build command]`
- If unclear or blocked, report STATUS: NEEDS_CONTEXT or STATUS: BLOCKED in your return message (do not attempt user interaction).
```

## Expected Return Format

```markdown
STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
FILES_MODIFIED:
- path/to/file1
- path/to/file2
VERIFICATION:
Command: [test command]
Result: PASS (0 failures, exit code 0)
DETAILS:
[Brief summary of implementation]
```
