# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from packages.index_runtime import CompositeIndex, IndexProvider
from packages.patterns import (
    PATTERN_REQUEST_CONTRACT,
    PatternLibraryError,
    compile_composition_pattern,
    export_metadata_dataset,
    resolve_composition_pattern,
    validate_registered_library,
)

ROOT = Path(__file__).resolve().parents[1]


def comparison_request(**overrides: object) -> dict:
    value = {
        "contract": PATTERN_REQUEST_CONTRACT,
        "request_id": "stage4-test-comparison",
        "task_mode": "new-build",
        "page_role": "comparison",
        "semantic_relations": ["supports"],
        "purpose_tags": ["evidence-led"],
        "language": "zh-CN",
        "rights_context": "public-open-source",
        "provider_ids": ["builtin-catalog"],
        "constraints": ["keep primary evidence dominant", "emit editable objects"],
        "expected_visual_effect": "evidence leads clearly to a supported implication",
    }
    value.update(overrides)
    return value


class PatternLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provider = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
        cls.runtime = CompositeIndex([cls.provider])

    def test_exact_request_selects_one_registered_pattern_and_linked_failures(self) -> None:
        resolution, receipts = resolve_composition_pattern(
            ROOT,
            self.runtime,
            comparison_request(),
            created_at="2026-08-23T11:00:00Z",
        )
        self.assertEqual(resolution["status"], "selected")
        self.assertEqual(resolution["selected_composition_pattern"]["record_id"], "pattern.asymmetric-evidence-to-decision")
        self.assertEqual(set(resolution["linked_failure_pattern_ids"]), {"failure.equal-weight-flattening", "failure.semantic-visual-mismatch"})
        self.assertEqual(len(receipts), 2)
        selected = {item["record_id"] for receipt in receipts for item in receipt["selection"]["selected"]}
        self.assertEqual(selected, {"pattern.asymmetric-evidence-to-decision", "failure.equal-weight-flattening", "failure.semantic-visual-mismatch"})
        self.assertTrue(all(receipt["hallucination_guard"]["invented_record_count"] == 0 for receipt in receipts))

    def test_compiler_preserves_decision_evidence_and_defers_visual_layers(self) -> None:
        resolution, receipts = resolve_composition_pattern(ROOT, self.runtime, comparison_request(), created_at="2026-08-23T11:00:00Z")
        plan = compile_composition_pattern(ROOT, self.provider, resolution, receipts)
        self.assertEqual(plan["contract"], "io.clayz.presentation.composition-plan/1.0")
        self.assertEqual(plan["decision"]["constraints"], comparison_request()["constraints"])
        self.assertEqual(plan["decision"]["expected_visual_effect"], comparison_request()["expected_visual_effect"])
        self.assertEqual(len(plan["failure_guards"]), 2)
        for layer in ("theme", "visual_variant", "layout_contract", "layout_tree", "resolved_coordinates"):
            self.assertFalse(plan["layers"][layer]["input_used"])
        self.assertTrue(plan["guards"]["no_coordinates_emitted"])
        self.assertTrue(plan["guards"]["editable_output_required"])

    def test_no_match_is_unresolved_and_cannot_compile(self) -> None:
        request = comparison_request(
            request_id="stage4-test-unregistered",
            page_role="orbital-constellation",
            semantic_relations=["orbits"],
            purpose_tags=["unregistered"],
        )
        resolution, receipts = resolve_composition_pattern(ROOT, self.runtime, request, created_at="2026-08-23T11:00:00Z")
        self.assertEqual(resolution["status"], "unresolved")
        self.assertEqual(resolution["fallback"]["reason"], "no-eligible-registered-composition-pattern")
        self.assertEqual(receipts[0]["candidates"], [])
        with self.assertRaisesRegex(PatternLibraryError, "cannot compile"):
            compile_composition_pattern(ROOT, self.provider, resolution, receipts)

    def test_unregistered_preferred_pattern_is_not_invented(self) -> None:
        resolution, receipts = resolve_composition_pattern(
            ROOT,
            self.runtime,
            comparison_request(preferred_pattern_id="pattern.unregistered"),
            created_at="2026-08-23T11:00:00Z",
        )
        self.assertEqual(resolution["status"], "unresolved")
        self.assertEqual(resolution["fallback"]["reason"], "preferred-pattern-not-retrieved")
        self.assertEqual(receipts[0]["selection"]["selected"], [])
        self.assertEqual(receipts[0]["hallucination_guard"]["invented_record_count"], 0)

    def test_ambiguous_patterns_require_explicit_choice(self) -> None:
        records = [copy.deepcopy(record) for record in self.provider.records]
        duplicate = copy.deepcopy(next(record for record in records if record["record_id"] == "pattern.asymmetric-evidence-to-decision"))
        duplicate["record_id"] = "pattern.asymmetric-evidence-to-decision-alt"
        duplicate["source"]["source_id"] = "stage4-synthetic-ambiguous"
        records.append(duplicate)
        runtime = CompositeIndex([IndexProvider.from_records("builtin-catalog", records)])
        resolution, receipts = resolve_composition_pattern(ROOT, runtime, comparison_request(), created_at="2026-08-23T11:00:00Z")
        self.assertEqual(resolution["status"], "unresolved")
        self.assertEqual(resolution["fallback"]["reason"], "ambiguous-eligible-composition-patterns")
        self.assertEqual(len(receipts[0]["selection"]["rejected"]), 2)

    def test_missing_linked_failure_prevents_pattern_selection(self) -> None:
        records = [copy.deepcopy(record) for record in self.provider.records if record["record_id"] != "failure.semantic-visual-mismatch"]
        provider = IndexProvider.from_records("builtin-catalog", records)
        runtime = CompositeIndex([provider])
        resolution, receipts = resolve_composition_pattern(ROOT, runtime, comparison_request(), created_at="2026-08-23T11:00:00Z")
        self.assertEqual(resolution["status"], "unresolved")
        self.assertEqual(resolution["fallback"]["reason"], "linked-failure-pattern-unavailable")
        self.assertEqual(receipts[0]["selection"]["selected"], [])
        self.assertEqual(len(receipts), 2)

    def test_compiler_rejects_registry_hash_drift(self) -> None:
        resolution, receipts = resolve_composition_pattern(ROOT, self.runtime, comparison_request(), created_at="2026-08-23T11:00:00Z")
        records = [copy.deepcopy(record) for record in self.provider.records]
        target = next(record for record in records if record["record_id"] == "pattern.asymmetric-evidence-to-decision")
        target["source"]["sha256"] = "0" * 64
        provider = IndexProvider.from_records("builtin-catalog", records)
        with self.assertRaisesRegex(PatternLibraryError, "source hash"):
            compile_composition_pattern(ROOT, provider, resolution, receipts)

    def test_metadata_export_is_deterministic_and_asset_free(self) -> None:
        first = export_metadata_dataset(ROOT, self.provider, created_at="2026-08-23T11:00:00Z")
        second = export_metadata_dataset(ROOT, self.provider, created_at="2026-08-23T12:00:00Z")
        self.assertEqual(first["dataset_id"], second["dataset_id"])
        self.assertEqual(len(first["records"]), 11)
        self.assertTrue(first["guards"]["metadata_only"])
        self.assertTrue(first["guards"]["no_asset_bytes"])
        self.assertTrue(first["guards"]["no_model_weights"])
        self.assertFalse(first["guards"]["generated_artifacts_auto_admitted"])
        serialized = str(first).casefold()
        self.assertNotIn("base64", serialized)
        self.assertNotIn("coordinates_included': true", serialized)

    def test_metadata_export_rejects_unadmitted_catalog_record(self) -> None:
        records = [copy.deepcopy(record) for record in self.provider.records]
        target = next(record for record in records if record["record_id"] == "reference.synthetic-evidence-opening")
        target["governance"]["human_admitted"] = False
        target["governance"]["quality_status"] = "observation"
        provider = IndexProvider.from_records("builtin-catalog", records)
        with self.assertRaisesRegex(PatternLibraryError, "human-admitted"):
            export_metadata_dataset(ROOT, provider, created_at="2026-08-23T11:00:00Z")

    def test_registered_links_and_public_boundaries_are_closed(self) -> None:
        result = validate_registered_library(ROOT, self.provider)
        self.assertEqual(result["counts"], {"composition-pattern": 3, "failure-pattern": 4, "reference": 3, "sequence": 1})
        for record in self.provider.records:
            if record["record_type"] not in {"composition-pattern", "failure-pattern", "reference", "sequence"}:
                continue
            self.assertEqual(record["classification"]["brand_scope"], "none")
            self.assertEqual(record["payload"]["kind"], "path")
            self.assertNotIn(record["classification"]["asset_class"], {"template", "master", "font", "brand-kit", "dataset", "model"})


if __name__ == "__main__":
    unittest.main()
