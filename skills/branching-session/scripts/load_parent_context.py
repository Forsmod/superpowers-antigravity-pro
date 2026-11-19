#!/usr/bin/env python3
"""Extract a clean, token-efficient conversation digest from an Antigravity parent transcript."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


_METADATA_BLOCKS_RE = re.compile(
    r"<(ADDITIONAL_METADATA|USER_SETTINGS_CHANGE|SYSTEM_MESSAGE)>[\s\S]*?</\1>",
    flags=re.MULTILINE,
)
_USER_REQUEST_RE = re.compile(
    r"<USER_REQUEST>\s*([\s\S]*?)\s*</USER_REQUEST>",
    flags=re.MULTILINE,
)


def clean_user_content(raw: str) -> str:
    """Strip Antigravity system metadata tags and unwrap <USER_REQUEST> blocks."""
    if not raw:
        return ""
    cleaned = _METADATA_BLOCKS_RE.sub("", raw)
    match = _USER_REQUEST_RE.search(cleaned)
    if match:
        return match.group(1).strip()
    return cleaned.strip()


def _format_tool_call(tc: dict[str, Any]) -> str:
    name = tc.get("name", "unknown_tool")
    args = tc.get("args") or {}
    if not isinstance(args, dict):
        return name
    for key in ("Path", "AbsolutePath", "CommandLine", "query", "TypeName", "Action"):
        if key in args and args[key]:
            val = str(args[key]).strip('"').replace("\n", " ")
            if len(val) > 80:
                val = val[:77] + "..."
            return f"{name}({key}={val})"
    return name


def extract_transcript_digest(
    transcript_path: Path,
    artifacts_dir: Path | None = None,
    max_steps: int = 50,
    max_chars: int = 24000,
) -> str:
    """Parse transcript.jsonl and optional top-level artifacts into a compact markdown digest."""
    entries: list[str] = []

    if transcript_path.exists():
        raw_lines = transcript_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for raw_line in raw_lines:
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            step_type = obj.get("type", "")
            step_idx = obj.get("step_index", "?")

            if step_type == "USER_INPUT":
                text = clean_user_content(obj.get("content", ""))
                if text:
                    entries.append(f"### [Step {step_idx}] User\n{text}")
            elif step_type == "PLANNER_RESPONSE":
                parts: list[str] = []
                content = (obj.get("content") or "").strip()
                if content:
                    parts.append(content)
                tool_calls = obj.get("tool_calls") or []
                if isinstance(tool_calls, list) and tool_calls:
                    tc_summary = ", ".join(
                        _format_tool_call(tc) for tc in tool_calls if isinstance(tc, dict)
                    )
                    if tc_summary:
                        parts.append(f"*Tools called:* `{tc_summary}`")
                if parts:
                    entries.append(f"### [Step {step_idx}] Assistant\n" + "\n\n".join(parts))

    if max_steps > 0 and len(entries) > max_steps:
        entries = entries[-max_steps:]

    sections: list[str] = ["# Parent Session Transcript Digest"]
    if entries:
        sections.append("\n\n".join(entries))
    else:
        sections.append("*(No dialogue entries found in transcript)*")

    if artifacts_dir and artifacts_dir.exists() and artifacts_dir.is_dir():
        artifact_blocks: list[str] = []
        for md_file in sorted(artifacts_dir.glob("*.md")):
            if md_file.is_file():
                content = md_file.read_text(encoding="utf-8", errors="replace").strip()
                if content:
                    artifact_blocks.append(f"### Artifact: `{md_file.name}`\n{content}")
        if artifact_blocks:
            sections.append("## Active Session Artifacts\n\n" + "\n\n".join(artifact_blocks))

    full_text = "\n\n".join(sections)
    if max_chars > 0 and len(full_text) > max_chars:
        tail = full_text[-max_chars:]
        return "... [Truncated earlier context]\n" + tail
    return full_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Load clean parent session context from transcript.jsonl")
    parser.add_argument("--transcript", required=True, type=Path, help="Path to parent transcript.jsonl")
    parser.add_argument("--artifacts-dir", type=Path, default=None, help="Path to parent brain/<id> artifact folder")
    parser.add_argument("--max-steps", type=int, default=50, help="Maximum dialogue turns to include")
    parser.add_argument("--max-chars", type=int, default=24000, help="Maximum character length of output")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    digest = extract_transcript_digest(
        transcript_path=args.transcript,
        artifacts_dir=args.artifacts_dir,
        max_steps=args.max_steps,
        max_chars=args.max_chars,
    )
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
