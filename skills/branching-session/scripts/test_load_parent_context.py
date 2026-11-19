import json
import tempfile
import unittest
from pathlib import Path

from load_parent_context import clean_user_content, extract_transcript_digest


class TestLoadParentContext(unittest.TestCase):
    def test_clean_user_content_strips_metadata_and_unwraps_request(self):
        raw = (
            "<USER_REQUEST>\n"
            "Давай создадим скилл для планирования.\n"
            "</USER_REQUEST>\n"
            "<ADDITIONAL_METADATA>\n"
            "The current local time is: 2026-10-22T15:32:11+02:00.\n"
            "</ADDITIONAL_METADATA>\n"
            "<USER_SETTINGS_CHANGE>\n"
            "Model changed\n"
            "</USER_SETTINGS_CHANGE>\n"
            "<SYSTEM_MESSAGE>\n"
            "Internal system event\n"
            "</SYSTEM_MESSAGE>"
        )
        cleaned = clean_user_content(raw)
        self.assertEqual(cleaned, "Давай создадим скилл для планирования.")

    def test_extracts_user_and_planner_messages_and_ignores_malformed_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "transcript.jsonl"
            lines = [
                json.dumps(
                    {
                        "step_index": 0,
                        "source": "USER_EXPLICIT",
                        "type": "USER_INPUT",
                        "content": "<USER_REQUEST>\nHello world\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\ntime\n</ADDITIONAL_METADATA>",
                    }
                ),
                "{malformed json line mid-write",
                json.dumps(
                    {
                        "step_index": 1,
                        "source": "MODEL",
                        "type": "PLANNER_RESPONSE",
                        "thinking": "secret thought",
                        "content": "I will check the files.",
                        "tool_calls": [
                            {"name": "read_file", "args": {"Path": "foo.py"}},
                            {"name": "run_command", "args": {"CommandLine": "pytest -v"}},
                        ],
                    }
                ),
                json.dumps(
                    {
                        "step_index": 2,
                        "source": "MODEL",
                        "type": "GENERIC",
                        "content": "huge 50KB file dump that should be skipped",
                    }
                ),
            ]
            transcript.write_text("\n".join(lines), encoding="utf-8")

            digest = extract_transcript_digest(transcript_path=transcript)
            self.assertIn("Hello world", digest)
            self.assertNotIn("ADDITIONAL_METADATA", digest)
            self.assertNotIn("secret thought", digest)
            self.assertNotIn("huge 50KB file dump", digest)
            self.assertIn("I will check the files.", digest)
            self.assertIn("read_file", digest)
            self.assertIn("foo.py", digest)
            self.assertIn("run_command", digest)

    def test_includes_artifacts_when_artifacts_dir_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            brain_dir = Path(tmp)
            sys_dir = brain_dir / ".system_generated" / "logs"
            sys_dir.mkdir(parents=True)
            transcript = sys_dir / "transcript.jsonl"
            transcript.write_text(
                json.dumps({"step_index": 0, "type": "USER_INPUT", "content": "Hi"}),
                encoding="utf-8",
            )
            (brain_dir / "task.md").write_text("# Task Tracker\n- Item 1", encoding="utf-8")
            scratch_dir = brain_dir / "scratch"
            scratch_dir.mkdir()
            (scratch_dir / "temp.md").write_text("ignore me", encoding="utf-8")

            digest = extract_transcript_digest(
                transcript_path=transcript,
                artifacts_dir=brain_dir,
            )
            self.assertIn("task.md", digest)
            self.assertIn("# Task Tracker", digest)
            self.assertNotIn("ignore me", digest)

    def test_respects_max_steps_and_max_chars(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "transcript.jsonl"
            steps = [
                json.dumps(
                    {
                        "step_index": i,
                        "type": "USER_INPUT",
                        "content": f"Message number {i} " + ("x" * 100),
                    }
                )
                for i in range(10)
            ]
            transcript.write_text("\n".join(steps), encoding="utf-8")

            digest_steps = extract_transcript_digest(transcript_path=transcript, max_steps=3)
            self.assertNotIn("Message number 0", digest_steps)
            self.assertIn("Message number 9", digest_steps)

            digest_chars = extract_transcript_digest(transcript_path=transcript, max_chars=300)
            self.assertLessEqual(len(digest_chars), 350)
            self.assertIn("Message number 9", digest_chars)


if __name__ == "__main__":
    unittest.main()
