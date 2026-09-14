"""Black-box checks for the bounded native Library handoff."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "cloud_learning_cli.py"


class CloudLearningCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="clayz-cloud-learning-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.root / "mirror"
        self.attachment = self.root / "source.txt"
        self.attachment.write_text("A confirmed source attachment.", encoding="utf-8")
        self.content = {
            "session_id": "discussion.cloud",
            "title": "Cloud handoff",
            "stage": "logic",
            "consensus": "Keep the exact confirmed consensus bound to its source bytes.",
            "applicability": ["management reports"],
            "limitations": ["A host must verify its fetched bytes before retrieval."],
            "provenance": "joint-inference",
            "evidence_refs": ["source-one:paragraph 1"],
            "unresolved_questions": ["Whether the rule applies to another output format"],
            "language": "en-US",
            "purpose_tags": ["evidence", "handoff"],
            "attachments": [{
                "attachment_id": "source-one",
                "filename": "source.txt",
                "origin": "synthetic test",
                "rights": "owner-provided",
                "locator": "paragraph 1",
            }],
            "supersedes": None,
        }
        self.policy = self.write("native-library-policy.json", {
            "contract": "io.clayz.presentation.native-library-policy/1.0",
            "adapter": "host-library",
            "host_root": "PPT/_extension/confirmed-learning",
            "logical_root": "library://clayz-confirmed/",
            "provider_id": "clayz.owner-consensus",
        })

    def write(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, *args: object, ok: bool = True) -> dict:
        environment = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), *map(str, args)],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=40,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        return {"stderr": result.stderr, "stdout": result.stdout}

    def prepare_and_confirm(self, suffix: str = "") -> tuple[Path, Path]:
        content = self.write(f"content{suffix}.json", self.content)
        draft_path = self.root / f"draft{suffix}.json"
        draft = self.cli(
            "draft", "--content", content, "--attachment", f"source-one={self.attachment}",
            "--output", draft_path,
        )
        confirmation_path = self.root / f"confirmation{suffix}.json"
        self.cli(
            "confirm", "--draft", draft_path, "--expected-sha256", draft["draft_sha256"],
            "--confirmed-by", "synthetic-owner", "--decision", "Confirm this exact draft",
            "--confirm-human-decision", "--output", confirmation_path,
        )
        return draft_path, confirmation_path

    def stage(self) -> tuple[dict, Path, Path]:
        draft, confirmation = self.prepare_and_confirm("-first")
        plan_path = self.root / "plan.json"
        plan = self.cli(
            "stage", "--store", self.store, "--draft", draft, "--confirmation", confirmation,
            "--attachment", f"source-one={self.attachment}", "--policy", self.policy,
            "--output", plan_path,
        )
        return plan, draft, confirmation

    def test_stage_is_pending_and_orders_current_last(self) -> None:
        plan, _, _ = self.stage()
        self.assertEqual(plan["status"], "awaiting-host-write")
        self.assertFalse(plan["staging"]["host_saved"])
        self.assertEqual(plan["expected_previous_current_sha256"], None)
        self.assertEqual(plan["staging_store"], self.store.resolve().as_posix())
        self.assertEqual(plan["actions"][-1]["target_relative"], "CURRENT")
        self.assertTrue(plan["actions"][-1]["last"])
        self.assertTrue(all(item["target_relative"] != "CURRENT" for item in plan["files"]))
        self.assertEqual(plan["actions"][:-1], plan["files"])
        self.assertEqual(plan["host_root"], "PPT/_extension/confirmed-learning")
        self.assertTrue(plan["actions"][-1]["native_target_relative"].endswith("/CURRENT"))
        content_targets = [item["target_relative"] for item in plan["files"]]
        self.assertTrue(any(target.endswith("/content.json") for target in content_targets))

    def test_verify_requires_fresh_readback_and_catches_tamper(self) -> None:
        plan, _, _ = self.stage()
        self.cli("verify", "--store", self.store, "--plan", self.root / "plan.json", ok=False)

        readback = self.root / "fresh-readback"
        shutil.copytree(self.store, readback)
        verified = self.cli("verify", "--store", readback, "--plan", self.root / "plan.json")
        self.assertEqual(verified["status"], "verified-readback")
        self.assertFalse(verified["host_fetch_origin"]["authenticated"])
        self.assertEqual(verified["host_fetch_origin"]["status"], "not-authenticated")

        target = readback / plan["files"][0]["target_relative"]
        target.write_bytes(target.read_bytes() + b"tamper")
        self.cli("verify", "--store", readback, "--plan", self.root / "plan.json", ok=False)

    def test_missing_confirmation_and_changed_attachment_do_not_stage(self) -> None:
        draft, confirmation = self.prepare_and_confirm("-second")
        confirmation.unlink()
        self.cli(
            "stage", "--store", self.store, "--draft", draft, "--confirmation", confirmation,
            "--attachment", f"source-one={self.attachment}", "--policy", self.policy,
            "--output", self.root / "missing-plan.json", ok=False,
        )
        self.assertFalse(self.store.exists())

        draft, confirmation = self.prepare_and_confirm()
        self.attachment.write_text("changed after exact confirmation", encoding="utf-8")
        self.cli(
            "stage", "--store", self.store, "--draft", draft, "--confirmation", confirmation,
            "--attachment", f"source-one={self.attachment}", "--policy", self.policy,
            "--output", self.root / "changed-plan.json", ok=False,
        )
        self.assertFalse(self.store.exists())

    def test_read_and_retrieve_survive_a_new_process(self) -> None:
        plan, _, _ = self.stage()
        record_id = "consensus." + self.content["session_id"]
        read = self.cli(
            "read", "--store", self.store, "--record-id", record_id, "--snapshot", plan["snapshot_id"],
            "--policy", self.policy,
        )
        self.assertEqual(read["status"], "verified-read")
        self.assertEqual(read["consensus"], self.content["consensus"])
        self.assertEqual(read["draft"]["session_id"], self.content["session_id"])
        self.assertEqual(read["confirmation"]["draft_sha256"], read["draft"]["draft_sha256"])
        self.assertTrue(read["attachments"][0]["verified"])

        self.assertEqual(read["record"]["source"]["sha256"], read["draft"]["draft_sha256"])

        request = self.write("request.json", {
            "contract": "io.clayz.presentation.retrieval-request/1.0",
            "request_id": "cloud-readback-request",
            "stage": "logic",
            "query": "exact confirmed consensus source bytes",
            "rights_context": "private-runtime",
            "require_human_admission": True,
            "filters": {"provider_ids": ["clayz.owner-consensus"]},
            "task_context": {
                "decision_goal": "retrieve the confirmed rule",
                "target_refs": ["stage:logic"],
                "format_need": "knowledge",
            },
            "ranking_policy": {
                "profile": "content",
                "minimum_score": 0.0,
                "max_selected": 5,
                "diversity_lambda": 0.8,
            },
            "neighbor_expansion": {"physical": 0, "semantic": 0},
            "limit": 5,
        })
        receipt = self.cli("retrieve", "--store", self.store, "--request", request)
        self.assertEqual(receipt["contract"], "io.clayz.presentation.retrieval-receipt/1.0")
        self.assertTrue(any(item["record_id"] == record_id for item in receipt["candidates"]))


if __name__ == "__main__":
    unittest.main()
