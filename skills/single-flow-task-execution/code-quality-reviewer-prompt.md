# Code Quality Review via Subagent

Use this template when invoking the `code-reviewer` subagent in Antigravity.

**Purpose:** Independent verification that implementation is clean, tested, and maintainable.

**Only proceed after spec compliance review passes.**

## Invocation Example

```json
{
  "Subagents": [
    {
      "TypeName": "code-reviewer",
      "Role": "Code Reviewer",
      "Model": "<selected_model: pro | flash>",
      "Prompt": "Please review the implementation for Task N.\n\n## What Was Implemented\n[Brief summary of implementation]\n\n## Plan / Requirements\n[Requirements or acceptance criteria for this task]\n\n## Git Commit Range / Files\nBase: [BASE_SHA]\nHead: [HEAD_SHA]\nModified files: [list of files]\n\nAssess plan alignment, code quality, test coverage, and security."
    }
  ]
}
```

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment.
Address all Critical and Important issues before completing the task.
