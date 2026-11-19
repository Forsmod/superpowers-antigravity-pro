---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages & Stack Traces Carefully**
   - Don't skip past errors or warnings — they often contain the exact cause.
   - Note exact file paths, line numbers, error codes, and exception types.

2. **Leverage Knowledge Graph (if project is indexed in `codebase-memory-mcp`)**
   - Use `trace_path` to map the call graph between the entry point and the failing function.
   - Use `query_graph` or `search_graph` to inspect callers, callees, and dependencies.
   - Trace data flow backward to find where the invalid value originated.

3. **Reproduce Consistently**
   - Formulate exact reproduction steps.
   - If intermittent or timing-related, add diagnostic logs before changing logic.

4. **Investigate Without Context Pollution**
   - If extensive log analysis or multi-file research is needed, consider dispatching a `research` subagent via `invoke_subagent` to explore the codebase and report findings without cluttering the primary conversation context.

5. **Check Recent Changes**
   - Check git history for recent modifications: `git diff HEAD~1`, `git log -n 5`.

### Phase 2: Pattern Analysis

1. **Find Working Examples**
   - Locate similar working code within the codebase.
   - What works that is similar to what is broken?

2. **Compare Against References**
   - Read reference implementations completely.
   - Identify every difference between working and broken code paths.

3. **Understand Dependencies & Assumptions**
   - Check configuration, environment variables, and assumptions about data contracts.

### Phase 3: Hypothesis and Testing

1. **Form a Single Hypothesis**
   - State clearly: *"I think X is the root cause because Y"*.
   - Be specific and falsifiable.

2. **Test Minimally**
   - Make the smallest possible change to test the hypothesis.
   - Test one variable at a time.

3. **Verify Before Proceeding**
   - Did it confirm the hypothesis? Yes → proceed to Phase 4.
   - Did it fail? Form a NEW hypothesis. Do NOT stack speculative fixes.

### Phase 4: Implementation (via TDD)

1. **Create a Failing Test First**
   - Write an automated test reproducing the exact failure (see `test-driven-development` skill).
   - Verify that the test fails for the expected reason.

2. **Implement the Minimal Fix**
   - Address the root cause directly at its source.
   - No bundled refactoring or unrequested changes.

3. **Verify Fix & Regression Safety**
   - Confirm the failing test now passes.
   - Run the entire test suite to ensure zero regressions.

4. **Escalation: 3+ Fixes Failed? Question Architecture**
   - If 3 or more fix attempts fail, **STOP immediately**.
   - Multiple failed fixes indicate an architectural mismatch or bad abstraction, not a simple bug.
   - Discuss with the user via `ask_question` or in chat before attempting further fixes.

## Red Flags - STOP and Follow Process

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- Proposing solutions before inspecting error logs or tracing data flow
- "One more fix attempt" (when already tried 2+)
- Changing tests to make broken code pass

**ALL of these mean: STOP. Return to Phase 1.**

## Debugging Techniques & Reference Guides

For specific failure classes, consult the specialized reference guides in this skill directory:

- **Root Cause Tracing:** [root-cause-tracing.md](root-cause-tracing.md) — Step-by-step method to trace data flow backward from the symptom to the original trigger.
- **Defense-in-Depth Validation:** [defense-in-depth.md](defense-in-depth.md) — How to add defensive checks at multiple architectural layers so bugs fail loudly at the source.
- **Async & Timing Bugs:** [condition-based-waiting.md](condition-based-waiting.md) — Replace flaky sleeps and timeouts with deterministic condition-based polling.
- **Test Suite Pollution:** [find-polluter.sh](find-polluter.sh) — Script to bisect and isolate test cases polluting shared state across test runs.

## Integration

- **Knowledge Graph (`codebase-memory-mcp`)** — Trace component dependencies and call paths.
- **`test-driven-development`** — Create the failing reproduction test before fixing.
- **`verification-before-completion`** — Confirm fix with fresh verification command output before claiming completion.

