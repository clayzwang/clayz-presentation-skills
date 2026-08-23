# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "synthetic-feedback-loop"
CREATED_AT = "2026-08-23T12:00:00Z"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.feedback import (  # noqa: E402
    ReadinessError,
    build_learning_provider,
    migrate_legacy_knowledge,
    run_retrieval_benchmark,
    validate_release_readiness,
)
from packages.index_runtime import CompositeIndex, IndexProvider  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FeedbackBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning_records = read_jsonl(FIXTURES / "learning-records.jsonl")
        self.learning_admissions = read_jsonl(FIXTURES / "learning-admissions.jsonl")
        self.learning_provider, self.feedback_report = build_learning_provider(
            self.learning_records,
            self.learning_admissions,
            created_at=CREATED_AT,
        )
        self.builtin = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")

    def test_only_hash_bound_human_admission_enters_learning_provider(self) -> None:
        self.assertEqual([record["record_id"] for record in self.learning_provider.records], ["learning.synthetic-label-offset"])
        self.assertEqual(self.feedback_report["admitted_record_count"], 1)
        self.assertEqual(
            self.feedback_report["skipped"],
            [{"record_id": "learning.synthetic-equal-weight-observation", "reason": "human-admission-required"}],
        )

    def test_changed_learning_record_is_rejected_after_admission(self) -> None:
        changed = copy.deepcopy(self.learning_records)
        changed[0]["decision"] = "A changed decision invalidates the prior admission."
        provider, report = build_learning_provider(changed, self.learning_admissions, created_at=CREATED_AT)
        self.assertEqual(provider.snapshot()["record_count"], 0)
        self.assertTrue(any("changed after admission" in item["reason"] for item in report["skipped"]))

    def test_admitted_learning_remains_private_runtime_only(self) -> None:
        spec = read_json(FIXTURES / "retrieval-benchmark.json")
        request = copy.deepcopy(spec["cases"][2]["request"])
        request["rights_context"] = "public-open-source"
        receipt = CompositeIndex([self.learning_provider]).search(request, created_at=CREATED_AT)
        self.assertEqual(receipt["candidates"], [])
        self.assertEqual(receipt["fallback"]["reason"], "no-eligible-registered-record")

    def test_benchmark_fixture_passes_without_invented_records(self) -> None:
        report = run_retrieval_benchmark(
            CompositeIndex([self.builtin, self.learning_provider]),
            read_json(FIXTURES / "retrieval-benchmark.json"),
            created_at=CREATED_AT,
        )
        self.assertTrue(report["summary"]["passed"])
        self.assertEqual(report["summary"]["passed_count"], 4)
        self.assertEqual(report["guards"]["invented_record_count"], 0)

    def test_benchmark_fails_closed_on_provider_snapshot_drift(self) -> None:
        spec = read_json(FIXTURES / "retrieval-benchmark.json")
        spec["expected_provider_snapshots"][0]["digest"] = "0" * 64
        report = run_retrieval_benchmark(
            CompositeIndex([self.builtin, self.learning_provider]),
            spec,
            created_at=CREATED_AT,
        )
        self.assertFalse(report["summary"]["passed"])
        self.assertEqual(report["summary"]["snapshot_drift_count"], 1)

    def test_benchmark_fails_when_a_forbidden_candidate_is_returned(self) -> None:
        spec = read_json(FIXTURES / "retrieval-benchmark.json")
        spec["cases"][2]["forbidden_candidate_ids"] = ["learning.synthetic-label-offset"]
        report = run_retrieval_benchmark(
            CompositeIndex([self.builtin, self.learning_provider]),
            spec,
            created_at=CREATED_AT,
        )
        learning_case = next(case for case in report["cases"] if case["case_id"] == "human-admitted-learning")
        self.assertFalse(learning_case["passed"])
        self.assertIn("forbidden-candidate-returned", learning_case["reasons"])

    def test_unregistered_request_stays_explicitly_unresolved(self) -> None:
        spec = read_json(FIXTURES / "retrieval-benchmark.json")
        report = run_retrieval_benchmark(
            CompositeIndex([self.builtin, self.learning_provider]),
            spec,
            created_at=CREATED_AT,
        )
        unresolved = next(case for case in report["cases"] if case["case_id"] == "unregistered-request-stays-unresolved")
        self.assertEqual(unresolved["actual_status"], "unresolved")
        self.assertEqual(unresolved["actual_candidate_ids"], [])

    def test_legacy_migration_skips_stale_and_unadmitted_sources(self) -> None:
        provider, report = migrate_legacy_knowledge(
            source_root=FIXTURES / "legacy-sources",
            asset_registry=FIXTURES / "legacy-asset-registry.jsonl",
            admission_registry=FIXTURES / "legacy-admissions.jsonl",
            learning_root=FIXTURES / "legacy-learning",
            created_at=CREATED_AT,
        )
        self.assertEqual(report["counts"], {
            "source_assets": 3,
            "migrated_assets": 1,
            "source_learning_records": 2,
            "migrated_learning_records": 1,
            "skipped": 3,
            "orphan_neighbors": 1,
        })
        self.assertEqual({item["reason"] for item in report["skipped"]}, {"source-hash-drift", "human-admission-required"})
        self.assertTrue(all(record["governance"]["public_catalog_eligible"] is False for record in provider.records))
        self.assertTrue(all(not record["neighbors"]["physical"] and not record["neighbors"]["semantic"] for record in provider.records))

    def test_release_readiness_is_evidence_backed_but_never_authorizes_release(self) -> None:
        result = validate_release_readiness(ROOT, read_json(ROOT / "release" / "v0.4.0-readiness.json"))
        self.assertEqual(result["current_public_version"], "0.3.0")
        self.assertFalse(result["release_authorized"])

    def test_release_readiness_rejects_premature_release_action(self) -> None:
        readiness = read_json(ROOT / "release" / "v0.4.0-readiness.json")
        readiness["actions"]["publish"] = True
        with self.assertRaises(ReadinessError):
            validate_release_readiness(ROOT, readiness)

    def test_legacy_cli_reindexes_learning_only_after_separate_admission(self) -> None:
        module = load_module("knowledge_cli_feedback", ROOT / "scripts" / "knowledge_cli.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            shutil.copy2(ROOT / "config" / "default.json", root / "config" / "default.json")
            for path in (
                root / "knowledge" / "registry" / "asset-registry.jsonl",
                root / "knowledge" / "registry" / "admitted-references.jsonl",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            for stage in ("logic", "copy", "art-direction", "output"):
                path = root / "knowledge" / "learning" / stage / "learning-records.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            settings = module.load_settings(root, root / "config" / "default.json")
            observation = module.record_learning(
                settings,
                "output",
                task_purpose="Synthetic compatibility audit",
                observation="A synthetic label shifted after format conversion.",
                evidence_refs=["synthetic://render-a", "synthetic://render-b"],
                decision="Keep a post-conversion position check.",
                user_ruling="Admit only as a compatibility note.",
                task_modes=["audit"],
                page_roles=["evidence"],
                purpose_tags=["renderer-compatibility"],
                language="en-US",
                failure_signals=["label-offset"],
                source_kind="synthetic-fixture",
                source_id="synthetic-cli-fixture",
            )
            self.assertEqual(module.build_index(settings)["learning_document_count"], 0)
            admission = module.admit_reference(
                settings,
                "learning",
                observation["record_id"],
                admitted_by="test-maintainer",
                use_for=["renderer-compatibility"],
                never_copy=["generated coordinates"],
                decision_notes="Synthetic test admission.",
                confirmed=True,
                promotion_target="compatibility-note",
            )
            self.assertEqual(admission["subject_sha256"], module.sha256_json(observation))
            index = module.build_index(settings)
            self.assertEqual(index["contract"], "io.clayz.presentation.knowledge-index/2.0")
            self.assertEqual(index["learning_document_count"], 1)
            result = module.search_index(index, "label conversion", purpose="renderer-compatibility", limit=5)
            self.assertEqual(result[0]["record_id"], observation["record_id"])
            learning_path = root / "knowledge" / "learning" / "output" / "learning-records.jsonl"
            changed = json.loads(learning_path.read_text(encoding="utf-8"))
            changed["decision"] = "Changed after admission."
            learning_path.write_text(json.dumps(changed) + "\n", encoding="utf-8")
            self.assertEqual(module.build_index(settings)["learning_document_count"], 0)


if __name__ == "__main__":
    unittest.main()
