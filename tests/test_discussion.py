# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Contract tests for discussion drafts and exact human confirmations."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from packages.knowledge_session.discussion import (
    CONFIRMATION_CONTRACT,
    DRAFT_CONTRACT,
    DiscussionError,
    canonical_sha256,
    confirm_draft,
    prepare_draft,
    validate_confirmation,
    validate_draft,
)


class DiscussionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = {
            "session_id": "discussion.test",
            "title": "Evidence boundaries",
            "stage": "logic",
            "consensus": "Keep source facts separate from recommendations.",
            "applicability": ["management reports"],
            "limitations": ["Does not establish recommendation effectiveness"],
            "provenance": "joint-inference",
            "evidence_refs": ["evidence-one:paragraph 1"],
            "unresolved_questions": ["Whether this generalizes to sales decks"],
            "language": "en-US",
            "purpose_tags": ["evidence", "management"],
            "attachments": [
                {
                    "attachment_id": "evidence-one",
                    "filename": "evidence.txt",
                    "origin": "synthetic test",
                    "rights": "owner-provided",
                    "locator": "paragraph 1",
                }
            ],
            "supersedes": None,
        }

    def test_prepare_is_deterministic_and_does_not_store_native_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clayz-discussion-") as directory:
            path = Path(directory) / "evidence.txt"
            payload = b"Synthetic evidence."
            path.write_bytes(payload)
            first = prepare_draft(copy.deepcopy(self.content), {"evidence-one": path})
            second = prepare_draft(copy.deepcopy(self.content), {"evidence-one": path})

        self.assertEqual(first["contract"], DRAFT_CONTRACT)
        self.assertEqual(first, second)
        self.assertEqual(first["applicable_stages"], ["logic"])
        attachment = first["attachments"][0]
        self.assertEqual(attachment["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(attachment["bytes"], len(payload))
        rendered = json.dumps(first, ensure_ascii=False)
        self.assertNotIn(str(path), rendered)
        self.assertEqual(first["draft_sha256"], canonical_sha256({k: v for k, v in first.items() if k != "draft_sha256"}))
        self.assertEqual(validate_draft(first), first)

    def test_confirmation_requires_actual_user_flag_and_exact_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clayz-discussion-") as directory:
            path = Path(directory) / "evidence.txt"
            path.write_text("evidence", encoding="utf-8")
            draft = prepare_draft(self.content, {"evidence-one": path})

        with self.assertRaises(DiscussionError):
            confirm_draft(
                draft,
                expected_sha256="0" * 64,
                confirmed_by="owner",
                decision="confirm",
                confirm_human_decision=True,
            )
        with self.assertRaises(DiscussionError):
            confirm_draft(
                draft,
                expected_sha256=draft["draft_sha256"],
                confirmed_by="owner",
                decision="confirm",
                confirm_human_decision=False,
            )

        confirmation = confirm_draft(
            draft,
            expected_sha256=draft["draft_sha256"],
            confirmed_by="owner",
            decision="Confirm this exact draft",
            confirm_human_decision=True,
        )
        self.assertEqual(confirmation["contract"], CONFIRMATION_CONTRACT)
        self.assertEqual(confirmation["draft_sha256"], draft["draft_sha256"])
        self.assertTrue(confirmation["confirm_human_decision"])
        self.assertEqual(validate_confirmation(draft, confirmation), confirmation)

        changed = copy.deepcopy(draft)
        changed["consensus"] += " Changed after review."
        with self.assertRaises(DiscussionError):
            validate_draft(changed)
        with self.assertRaises(DiscussionError):
            validate_confirmation(changed, confirmation)

    def test_bindings_and_attachment_metadata_are_strict(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clayz-discussion-") as directory:
            path = Path(directory) / "evidence.txt"
            path.write_text("evidence", encoding="utf-8")
            with self.assertRaises(DiscussionError):
                prepare_draft(self.content, {})
            with self.assertRaises(DiscussionError):
                prepare_draft(self.content, {"evidence-one": path, "extra": path})

            unsafe = copy.deepcopy(self.content)
            unsafe["attachments"][0]["filename"] = "../evidence.txt"
            with self.assertRaises(DiscussionError):
                prepare_draft(unsafe, {"evidence-one": path})

    def test_provenance_and_applicable_stage_rules(self) -> None:
        source_fact = copy.deepcopy(self.content)
        source_fact["provenance"] = "source-fact"
        source_fact["evidence_refs"] = []
        with tempfile.TemporaryDirectory(prefix="clayz-discussion-") as directory:
            path = Path(directory) / "evidence.txt"
            path.write_text("evidence", encoding="utf-8")
            with self.assertRaises(DiscussionError):
                prepare_draft(source_fact, {"evidence-one": path})

        personal = copy.deepcopy(self.content)
        personal["provenance"] = "user-experience"
        personal["evidence_refs"] = []
        personal["attachments"] = []
        personal["limitations"] = []
        with self.assertRaises(DiscussionError):
            prepare_draft(personal, {})

        personal["limitations"] = ["Personal experience; no external validation"]
        personal["applicable_stages"] = ["logic", "copy", "output"]
        draft = prepare_draft(personal, {})
        self.assertEqual(draft["applicable_stages"], ["logic", "copy", "output"])


if __name__ == "__main__":
    unittest.main()
