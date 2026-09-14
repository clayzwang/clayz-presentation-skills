# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Exercise evidence reuse against real subprocesses and changed artifacts."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.task_runtime import run_check, snapshots, canonical, digest


class TaskRuntimeTests(unittest.TestCase):
    def test_reuse_and_dependency_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source.txt", root / "output.txt"
            source.write_text("one", encoding="utf-8")
            command = [sys.executable, "-c", "from pathlib import Path; Path('output.txt').write_bytes(Path('source.txt').read_bytes())"]
            def check():
                return run_check(root, "render", command, [source], [output], reuse=True)
            self.assertFalse(check()["reused"])
            self.assertTrue(check()["reused"])
            source.write_text("two", encoding="utf-8")
            self.assertFalse(check()["reused"])
            output.write_text("tampered", encoding="utf-8")
            self.assertFalse(check()["reused"])
            self.assertEqual(output.read_text(), "two")

    def test_input_changed_during_execution_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source.txt", root / "output.txt"
            source.write_text("before")
            command = [sys.executable, "-c", "from pathlib import Path; Path('source.txt').write_text('after'); Path('output.txt').write_text('done')"]
            with self.assertRaises(RuntimeError):
                run_check(root, "drift", command, [source], [output], reuse=True)

    def test_generated_snapshots_bind_exact_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, plan = root / "package.json", root / "plan.json"
            package.write_text(json.dumps({"brief": {"goal": "decision"}, "logic_layer": {}, "copy_layer": {"slides": []}}))
            plan.write_text(json.dumps({"slides": []}))
            result = snapshots(package, plan)
            for stage, entry in result.items():
                self.assertEqual(entry["snapshot_sha256"], canonical(entry["snapshot"]))
                self.assertEqual(entry["artifact_sha256"], digest(plan if stage == "art_direction" else package))


if __name__ == "__main__":
    unittest.main()
