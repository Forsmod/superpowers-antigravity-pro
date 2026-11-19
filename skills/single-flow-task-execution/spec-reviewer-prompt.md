# Spec Compliance Review Template

Use this checklist to verify that an implementation matches its specification before proceeding to code quality review.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less).

## Review Checklist

```markdown
### 1. Requirements Check
- Compare actual code against requirements line by line.
- Are all requested features and edge cases implemented?
- Did any requirements get skipped?

### 2. Scope & YAGNI Check
- Were unrequested features or flags added?
- Is there unnecessary complexity or over-engineering?

### 3. Misunderstandings Check
- Was the requirement interpreted correctly?
- Does the behavior match user expectations?

### Status
- [ ] Spec Compliant: all requirements satisfied.
- [ ] Gaps Found: [list specific missing or extra items with file:line references]
```
