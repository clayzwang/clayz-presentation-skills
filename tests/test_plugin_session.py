# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Focused tests for the local plugin inspection and retrieval facade."""

from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from packages.knowledge_session.discussion import confirm_draft, prepare_draft
from packages.knowledge_session.store import commit_knowledge
from packages.runtime.plugin_session import inspect_plugin, list_tools, materialize_knowledge, retrieve_knowledge


ROOT = Path(__file__).resolve().parents[1]


class PluginSessionTests(unittest.TestCase):
    def test_inspection_is_read_only_and_catalog_is_available(self) -> None:
        report = inspect_plugin(ROOT)
        self.assertEqual(report["status"], "ready")
        self.assertTrue(report["guards"]["read_only"])
        self.assertFalse(report["guards"]["production_preflight"])
        self.assertEqual(report["public_index"]["snapshot"]["record_count"], 24)
        self.assertEqual(report["content_manifest"]["status"], "source-unsealed")

    def test_missing_external_library_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clayz-plugin-session-") as directory:
            report = inspect_plugin(ROOT, Path(directory) / "missing-library")
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["library"]["status"], "unavailable")
        self.assertEqual(report["library"]["reason"], "store-absent")

    def test_retrieval_keeps_selection_open_and_read_materializes_hashes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clayz-plugin-session-") as directory:
            work = Path(directory)
            store = work / "library"
            attachment = work / "evidence.txt"
            attachment.write_text("Keep evidence limits visible.", encoding="utf-8")
            content = {
                "session_id": "session.facade",
                "title": "Evidence limits",
                "stage": "logic",
                "consensus": "Keep evidence limits visible in management reports.",
                "applicability": ["management reports"],
                "limitations": ["Does not prove an intervention effective"],
                "provenance": "joint-inference",
                "evidence_refs": ["evidence-one:paragraph 1"],
                "unresolved_questions": ["Whether this generalizes to sales decks"],
                "language": "en-US",
                "purpose_tags": ["management", "evidence"],
                "attachments": [{
                    "attachment_id": "evidence-one",
                    "filename": "evidence.txt",
                    "origin": "synthetic test",
                    "rights": "owner-provided",
                    "locator": "paragraph 1",
                }],
                "supersedes": None,
            }
            draft = prepare_draft(copy.deepcopy(content), {"evidence-one": attachment})
            confirmation = confirm_draft(
                draft,
                expected_sha256=draft["draft_sha256"],
                confirmed_by="synthetic-owner",
                decision="Confirm this exact draft",
                confirm_human_decision=True,
            )
            committed = commit_knowledge(store, draft, confirmation, {"evidence-one": attachment})
            request = {
                "contract": "io.clayz.presentation.retrieval-request/1.0",
                "request_id": "request.facade",
                "stage": "logic",
                "query": content["consensus"],
                "rights_context": "private-runtime",
                "filters": {"provider_ids": [committed["provider_id"]]},
            }
            found = retrieve_knowledge(ROOT, store, request, committed["snapshot_id"])
            self.assertEqual(found["status"], "ready")
            self.assertEqual(found["snapshot_id"], committed["snapshot_id"])
            self.assertEqual(found["receipt"]["selection"]["selected"], [])
            self.assertEqual(found["selection"]["status"], "not-finalized")
            candidate = found["receipt"]["candidates"][0]
            materialized = materialize_knowledge(ROOT, store, candidate["record_id"], committed["snapshot_id"])
            self.assertEqual(materialized["consensus"], content["consensus"])
            self.assertTrue(materialized["attachments"][0]["verified"])
            self.assertEqual(materialized["attachments"][0]["locator"], "paragraph 1")

    def test_tool_catalog_reports_host_requirements_separately(self) -> None:
        report = list_tools(ROOT)
        self.assertEqual(report["status"], "ready")
        self.assertFalse(report["guards"]["arbitrary_executor"])
        self.assertFalse(report["guards"]["network_access"])
        power_point = next(item for item in report["tools"] if item["tool_id"] == "presentation.render-powerpoint")
        self.assertEqual(power_point["implementation"]["status"], "installed")
        self.assertTrue(power_point["host_capability"]["required"])
        self.assertEqual(power_point["host_capability"]["status"], "not-inspected")


if __name__ == "__main__":
    unittest.main()
