# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Black-box restart tests: the executable facade must preserve owner decisions."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PluginCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="clayz-cli-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.root / "Library"
        self.attachment = self.root / "source.txt"
        self.attachment.write_text("Synthetic evidence: separate facts from recommendations.", encoding="utf-8")
        self.content = {
            "session_id": "discussion.example", "title": "Evidence first",
            "stage": "logic", "consensus": "Separate source facts from recommendations in a management report.",
            "applicability": ["management reports"], "limitations": ["Does not prove a recommendation effective"],
            "provenance": "joint-inference", "evidence_refs": ["source-one:paragraph 1"],
            "unresolved_questions": ["Whether this generalizes to sales decks"],
            "language": "en-US", "purpose_tags": ["management", "evidence"],
            "attachments": [{"attachment_id": "source-one", "filename": "source.txt", "origin": "synthetic test",
                             "rights": "owner-provided", "locator": "paragraph 1"}],
            "supersedes": None,
        }

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, *args, ok=True):
        env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/plugin_cli.py"), *map(str, args)],
                                cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8", timeout=40)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def prepare(self):
        source = self.write("content.json", self.content)
        draft_path = self.root / "draft.json"
        draft = self.cli("draft", "--content", source, "--attachment", f"source-one={self.attachment}", "--output", draft_path)
        return draft_path, draft

    def admit(self):
        draft_path, draft = self.prepare()
        confirmation = self.root / "confirmation.json"
        self.cli("confirm", "--draft", draft_path, "--expected-sha256", draft["draft_sha256"],
                 "--confirmed-by", "synthetic-test-user", "--decision", "Confirm this exact synthetic draft",
                 "--confirm-human-decision", "--output", confirmation)
        return draft_path, confirmation

    def commit(self, draft_path, confirmation):
        return self.cli("commit", "--store", self.store, "--draft", draft_path,
                        "--confirmation", confirmation, "--attachment", f"source-one={self.attachment}")

    def test_new_process_retrieves_and_reads_confirmed_content(self):
        draft, confirmation = self.admit()
        committed = self.commit(draft, confirmation)
        request = self.write("request.json", {
            "contract": "io.clayz.presentation.retrieval-request/1.0", "request_id": "req.evidence",
            "stage": "logic", "query": "Separate source facts from recommendations in management reports",
            "rights_context": "private-runtime", "require_human_admission": True,
            "filters": {"provider_ids": [committed["provider_id"]]},
        })
        found = self.cli("retrieve", "--store", self.store, "--request", request)
        self.assertEqual(found["snapshot_id"], committed["snapshot_id"])
        candidates = found["receipt"]["candidates"]
        self.assertTrue(candidates)
        read = self.cli("read", "--store", self.store, "--record-id", candidates[0]["record_id"],
                        "--snapshot", committed["snapshot_id"])
        self.assertIn(self.content["consensus"], json.dumps(read))
        self.assertIn("joint-inference", json.dumps(read))
        self.assertIn("paragraph 1", json.dumps(read))

    def test_confirmation_is_not_implicit(self):
        draft_path, draft = self.prepare()
        self.cli("confirm", "--draft", draft_path, "--expected-sha256", draft["draft_sha256"],
                 "--confirmed-by", "synthetic-test-user", "--decision", "pending",
                 "--output", self.root / "not-confirmed.json", ok=False)
        self.assertFalse((self.root / "not-confirmed.json").exists())
        self.assertFalse(self.store.exists())

    def test_changed_attachment_does_not_publish(self):
        draft, confirmation = self.admit()
        self.attachment.write_text("changed after review", encoding="utf-8")
        self.cli("commit", "--store", self.store, "--draft", draft, "--confirmation", confirmation,
                 "--attachment", f"source-one={self.attachment}", ok=False)
        self.assertFalse((self.store / "CURRENT").exists())

    def test_duplicate_bindings_and_plugin_internal_store_rejected(self):
        self.cli("draft", "--content", self.write("content.json", self.content),
                 "--attachment", f"source-one={self.attachment}", "--attachment", f"source-one={self.attachment}",
                 "--output", self.root / "bad.json", ok=False)
        self.cli("inspect", "--store", ROOT / "knowledge" / "owner", ok=False)


if __name__ == "__main__":
    unittest.main()
