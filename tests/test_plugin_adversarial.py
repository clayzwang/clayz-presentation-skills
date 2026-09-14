# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Adversarial contract tests for the local discussion knowledge store.

These tests deliberately exercise the boundaries that are easy to weaken while
implementing the plugin facade: a confirmation is bound to the exact draft,
attachments are persisted and verified, revision parents are compare-and-swap
guards, and private knowledge only appears through the shared retrieval engine.
"""
from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest import mock

from packages.knowledge_session.discussion import confirm_draft, prepare_draft
from packages.knowledge_session.store import commit_knowledge, load_snapshot
from packages.runtime.plugin_session import retrieve_knowledge


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PluginAdversarialTests(unittest.TestCase):
    def setUp(self):
        # The owner store is intentionally a temporary directory outside the
        # package root.  This also models a fresh process/store boundary.
        self.temp = tempfile.TemporaryDirectory(prefix="clayz-adversarial-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.root / "Library"
        self.attachment = self.root / "evidence.txt"
        self.attachment.write_text(
            "Synthetic evidence: preserve source facts and recommendation limits.",
            encoding="utf-8",
        )
        self.content = {
            "session_id": "discussion.adversarial",
            "title": "Evidence boundaries",
            "stage": "logic",
            "consensus": "Preserve source facts and recommendation limits in management reports.",
            "applicability": ["management reports"],
            "limitations": ["Does not establish that a recommendation is effective"],
            "provenance": "joint-inference",
            "evidence_refs": ["evidence-one:paragraph 1"],
            "unresolved_questions": ["Whether this generalizes to sales decks"],
            "language": "en-US",
            "purpose_tags": ["management", "evidence"],
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

    def _draft(self, content=None):
        return prepare_draft(
            copy.deepcopy(content or self.content),
            {"evidence-one": self.attachment},
        )

    def _confirmed(self, content=None):
        draft = self._draft(content)
        confirmation = confirm_draft(
            draft,
            expected_sha256=draft["draft_sha256"],
            confirmed_by="synthetic-owner",
            decision="Confirm this exact synthetic draft",
            confirm_human_decision=True,
        )
        return draft, confirmation

    def _commit(self, content=None):
        draft, confirmation = self._confirmed(content)
        committed = commit_knowledge(
            self.store,
            draft,
            confirmation,
            {"evidence-one": self.attachment},
        )
        return draft, confirmation, committed

    def _request(self, provider_id, *, rights_context="private-runtime", stage="logic"):
        # Keep this request complete so the assertion reaches the same
        # IndexRecord/CompositeIndex validation used by production retrieval.
        return {
            "contract": "io.clayz.presentation.retrieval-request/1.0",
            "request_id": "request.adversarial",
            "stage": stage,
            "query": self.content["consensus"],
            "intent": "task-reference",
            "task_context": {
                "decision_goal": "keep evidence limits visible",
                "target_refs": ["synthetic-report"],
                "format_need": "management-report logic",
            },
            "ranking_policy": {
                "profile": "content",
                "minimum_score": 0.0,
                "max_selected": 10,
                "diversity_lambda": 0.8,
            },
            "rights_context": rights_context,
            "require_human_admission": True,
            "limit": 10,
            "filters": {
                "record_types": ["knowledge"],
                "provider_ids": [provider_id],
                "task_modes": [],
                "page_roles": [],
                "semantic_relations": [],
                "purpose_tags": [],
                "languages": [],
                "failure_signals": [],
                "format_tags": [],
                "include_metadata_only": True,
            },
            "neighbor_expansion": {"physical": 0, "semantic": 0},
        }

    @staticmethod
    def _receipt(result):
        """Accept the runtime's normal receipt wrapper or a direct receipt."""
        return result.get("receipt", result) if isinstance(result, dict) else result

    def test_confirmation_is_bound_to_exact_draft_and_actual_human_decision(self):
        draft = self._draft()
        original_digest = draft["draft_sha256"]

        with self.assertRaises((ValueError, TypeError, KeyError)):
            confirm_draft(
                draft,
                expected_sha256="0" * 64,
                confirmed_by="synthetic-owner",
                decision="Confirm this exact synthetic draft",
                confirm_human_decision=True,
            )

        changed = copy.deepcopy(draft)
        # The contract exposes consensus as a draft field.  Keep this mutation
        # local to the review object and retain the original expected digest.
        changed["consensus"] = changed["consensus"] + " Changed after review."
        with self.assertRaises((ValueError, TypeError, KeyError)):
            confirm_draft(
                changed,
                expected_sha256=original_digest,
                confirmed_by="synthetic-owner",
                decision="Confirm this exact synthetic draft",
                confirm_human_decision=True,
            )

        with self.assertRaises((ValueError, TypeError, KeyError)):
            confirm_draft(
                draft,
                expected_sha256=original_digest,
                confirmed_by="synthetic-owner",
                decision="Confirm this exact synthetic draft",
                confirm_human_decision=False,
            )

        confirmation = confirm_draft(
            draft,
            expected_sha256=original_digest,
            confirmed_by="synthetic-owner",
            decision="Confirm this exact synthetic draft",
            confirm_human_decision=True,
        )
        self.assertEqual(confirmation["draft_sha256"], original_digest)

    def test_direct_commit_cannot_create_owner_store_inside_plugin_installation(self):
        draft, confirmation = self._confirmed()
        internal_store = PROJECT_ROOT / f".adversarial-internal-{uuid.uuid4().hex}"
        with self.assertRaises((OSError, ValueError, KeyError, TypeError)):
            commit_knowledge(
                internal_store,
                draft,
                confirmation,
                {"evidence-one": self.attachment},
            )
        self.assertFalse(internal_store.exists())

    def test_attachment_hash_is_in_review_and_persisted_then_tamper_is_rejected(self):
        draft, confirmation, committed = self._commit()
        expected_attachment_sha = hashlib.sha256(self.attachment.read_bytes()).hexdigest()
        draft_attachment = next(
            item for item in draft["attachments"] if item["attachment_id"] == "evidence-one"
        )
        self.assertEqual(draft_attachment["sha256"], expected_attachment_sha)

        snapshot = load_snapshot(self.store, committed["snapshot_id"])
        self.assertEqual(snapshot["snapshot_id"], committed["snapshot_id"])
        self.assertEqual(snapshot["provider_id"], committed["provider_id"])

        # The manifest is the durable binding for all snapshot files. Locate
        # the raw persisted attachment by its content hash, independent of the
        # implementation's attachment filename/layout.
        manifest_path = Path(committed["manifest_path"])
        self.assertTrue(manifest_path.is_file())
        snapshot_root = manifest_path.parent
        persisted = [
            path
            for path in snapshot_root.rglob("*")
            if path.is_file()
            and path != manifest_path
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected_attachment_sha
        ]
        self.assertTrue(persisted, "commit must persist the original attachment bytes")
        persisted[0].write_bytes(b"tampered attachment")
        with self.assertRaises((OSError, ValueError, KeyError, TypeError)):
            load_snapshot(self.store, committed["snapshot_id"])

    def test_new_revision_requires_parent_and_stale_concurrent_writer_cannot_replace_current(self):
        base_draft, _, base = self._commit()

        missing_parent = copy.deepcopy(self.content)
        missing_parent["consensus"] = "A revision without an explicit parent must be rejected."
        # It is a genuinely new draft but accidentally retains the initial
        # null parent, which must never silently overwrite CURRENT.
        with self.assertRaises((OSError, ValueError, KeyError, TypeError)):
            draft, confirmation = self._confirmed(missing_parent)
            commit_knowledge(self.store, draft, confirmation, {"evidence-one": self.attachment})
        current = load_snapshot(self.store)
        self.assertEqual(current["snapshot_id"], base["snapshot_id"])

        revision_a = copy.deepcopy(self.content)
        revision_a["consensus"] = "Revision A preserves source facts and names the parent."
        revision_a["supersedes"] = base_draft["draft_sha256"]
        revision_b = copy.deepcopy(self.content)
        revision_b["consensus"] = "Revision B preserves source facts and names the same parent."
        revision_b["supersedes"] = base_draft["draft_sha256"]
        draft_a, confirmation_a = self._confirmed(revision_a)
        draft_b, confirmation_b = self._confirmed(revision_b)
        committed_a = commit_knowledge(
            self.store, draft_a, confirmation_a, {"evidence-one": self.attachment}
        )
        with self.assertRaises((OSError, ValueError, KeyError, TypeError)):
            commit_knowledge(
                self.store, draft_b, confirmation_b, {"evidence-one": self.attachment}
            )
        current = load_snapshot(self.store)
        self.assertEqual(current["snapshot_id"], committed_a["snapshot_id"])

    def test_concurrent_writers_with_same_parent_have_one_winner(self):
        base_draft, _, base = self._commit()
        revision_a = copy.deepcopy(self.content)
        revision_a["consensus"] = "Concurrent revision A names the same parent."
        revision_a["supersedes"] = base_draft["draft_sha256"]
        revision_b = copy.deepcopy(self.content)
        revision_b["consensus"] = "Concurrent revision B names the same parent."
        revision_b["supersedes"] = base_draft["draft_sha256"]
        draft_a, confirmation_a = self._confirmed(revision_a)
        draft_b, confirmation_b = self._confirmed(revision_b)

        def publish(draft, confirmation):
            return commit_knowledge(
                self.store, draft, confirmation, {"evidence-one": self.attachment}
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(publish, draft_a, confirmation_a),
                pool.submit(publish, draft_b, confirmation_b),
            ]
            outcomes = []
            for future in futures:
                try:
                    outcomes.append(("ok", future.result()))
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    outcomes.append(("error", exc))
        self.assertEqual(sum(kind == "ok" for kind, _ in outcomes), 1)
        winner = next(value for kind, value in outcomes if kind == "ok")
        self.assertEqual(load_snapshot(self.store)["snapshot_id"], winner["snapshot_id"])

    def test_failed_pointer_swap_leaves_previous_snapshot_usable(self):
        base_draft, _, base = self._commit()
        revision = copy.deepcopy(self.content)
        revision["consensus"] = "A failed publication must leave the previous snapshot usable."
        revision["supersedes"] = base_draft["draft_sha256"]
        draft, confirmation = self._confirmed(revision)

        original_replace = __import__("os").replace

        def fail_current_swap(source, destination, *args):
            if Path(destination).name == "CURRENT":
                raise OSError("injected CURRENT pointer failure")
            return original_replace(source, destination, *args)

        # Patching os.replace also intercepts pathlib.Path.replace, while
        # allowing the staged snapshot files themselves to be written.  This
        # exercises the atomic publication boundary rather than input checks.
        with mock.patch("os.replace", side_effect=fail_current_swap):
            with self.assertRaises((OSError, ValueError, KeyError, TypeError)):
                commit_knowledge(
                    self.store, draft, confirmation, {"evidence-one": self.attachment}
                )
        current = load_snapshot(self.store)
        self.assertEqual(current["snapshot_id"], base["snapshot_id"])

    def test_retrieval_uses_shared_engine_and_private_knowledge_is_not_public(self):
        # Before commit, a draft/confirmation object has no registered record.
        draft, confirmation = self._confirmed()
        try:
            unavailable = retrieve_knowledge(
                PROJECT_ROOT,
                self.store,
                self._request("unknown-provider"),
                None,
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            unavailable = {"error": str(exc)}
        else:
            unavailable_receipt = self._receipt(unavailable)
            self.assertIn(unavailable.get("status"), {"blocked", "unavailable"})
            # An unavailable store is not a successful empty retrieval. The
            # runtime may return a structured status with no receipt.
            if unavailable_receipt is not None:
                self.assertFalse(unavailable_receipt.get("candidates"))
        self.assertFalse((self.store / "CURRENT").exists())

        committed = commit_knowledge(
            self.store, draft, confirmation, {"evidence-one": self.attachment}
        )
        private_request = self._request(committed["provider_id"])
        from packages.index_runtime.retrieval import CompositeIndex

        with mock.patch(
            "packages.index_runtime.retrieval.CompositeIndex.search",
            autospec=True,
            side_effect=CompositeIndex.search,
        ) as shared_search:
            private_result = retrieve_knowledge(PROJECT_ROOT, self.store, private_request, None)
        self.assertTrue(shared_search.called, "knowledge retrieval must delegate to CompositeIndex.search")
        private_receipt = self._receipt(private_result)
        private_candidates = private_receipt.get("candidates", [])
        self.assertTrue(private_candidates)
        self.assertEqual(private_candidates[0]["provider_id"], committed["provider_id"])
        self.assertIn(
            committed["provider_id"],
            {item["provider_id"] for item in private_receipt["index_snapshot"]},
        )

        public_result = retrieve_knowledge(
            PROJECT_ROOT,
            self.store,
            self._request(committed["provider_id"], rights_context="public-open-source"),
            None,
        )
        public_receipt = self._receipt(public_result)
        self.assertFalse(public_receipt.get("candidates"))

    def test_one_owner_record_can_be_scoped_to_multiple_authoring_stages(self):
        content = copy.deepcopy(self.content)
        content["applicable_stages"] = ["logic", "copy"]
        draft, confirmation, committed = self._commit(content)
        snapshot = load_snapshot(self.store, committed["snapshot_id"])
        self.assertEqual(len(snapshot["records"]), 1)
        record = snapshot["records"][0]
        self.assertEqual(set(record["classification"]["stages"]), {"logic", "copy"})
        self.assertNotIn("supervisor", record["classification"]["stages"])
        self.assertEqual(record["payload"]["ref"]["owner_stage"], "logic")

        copy_result = retrieve_knowledge(
            PROJECT_ROOT,
            self.store,
            self._request(committed["provider_id"], stage="copy"),
            None,
        )
        copy_receipt = self._receipt(copy_result)
        copy_candidates = [
            candidate
            for candidate in copy_receipt["candidates"]
            if candidate["provider_id"] == committed["provider_id"]
        ]
        self.assertEqual(len(copy_candidates), 1)
        self.assertEqual(copy_candidates[0]["record_id"], record["record_id"])


if __name__ == "__main__":
    unittest.main()
