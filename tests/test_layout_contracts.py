# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from packages.index_runtime import CompositeIndex, IndexProvider
from packages.layout import (
    LayoutContractError,
    compile_layout_contract,
    resolve_layout_contract,
    solve_compilation,
    validate_layout_contract_instance,
)

ROOT = Path(__file__).resolve().parents[1]


def comparison_request(**overrides: object) -> dict:
    value = {
        "contract": "io.clayz.presentation.layout-contract-request/1.0",
        "request_id": "request-layout-comparison",
        "task_mode": "new-build",
        "page_role": "comparison",
        "semantic_relations": ["supports"],
        "purpose_tags": ["evidence-led"],
        "language": "zh-CN",
        "rights_context": "public-open-source",
        "provider_ids": ["builtin-catalog"],
    }
    value.update(overrides)
    return value


def comparison_instance() -> dict:
    return {
        "contract": "io.clayz.presentation.layout-contract-instance/1.0",
        "instance_id": "synthetic-comparison-slide",
        "layout_contract_id": "layout.evidence-with-implication",
        "semantic_layout_tree_id": "SLT-SYNTHETIC-COMPARISON",
        "frame": {"x": 0.55, "y": 1.35, "w": 12.23, "h": 5.25},
        "bindings": [
            {"slot_id": "primary-evidence", "content_kind": "chart", "copy_ids": ["COPY-EVIDENCE"], "semantic_node_ids": ["SLT-NODE-EVIDENCE"]},
            {"slot_id": "source-note", "content_kind": "source-note", "copy_ids": ["COPY-SOURCE"], "semantic_node_ids": ["SLT-NODE-SOURCE"]},
            {"slot_id": "findings", "content_kind": "text", "copy_ids": ["COPY-FINDING-1", "COPY-FINDING-2"], "semantic_node_ids": ["SLT-NODE-FINDINGS"]},
            {"slot_id": "decision-implication", "content_kind": "text", "copy_ids": ["COPY-IMPLICATION"], "semantic_node_ids": ["SLT-NODE-IMPLICATION"]},
        ],
    }


class LayoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provider = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
        cls.runtime = CompositeIndex([cls.provider])

    def test_exact_semantics_select_one_registered_contract(self) -> None:
        resolution, receipt = resolve_layout_contract(
            self.runtime,
            comparison_request(),
            created_at="2026-08-23T08:00:00Z",
        )
        self.assertEqual(resolution["status"], "selected")
        self.assertEqual(resolution["selected_layout_contract"]["record_id"], "layout.evidence-with-implication")
        self.assertFalse(resolution["fallback"]["used"])
        self.assertEqual(receipt["selection"]["selected"][0]["record_id"], "layout.evidence-with-implication")
        self.assertEqual(receipt["hallucination_guard"]["invented_record_count"], 0)

    def test_compiler_preserves_five_explicit_layers_and_lineage(self) -> None:
        resolution, receipt = resolve_layout_contract(self.runtime, comparison_request(), created_at="2026-08-23T08:00:00Z")
        compilation = compile_layout_contract(ROOT, self.provider, resolution, receipt, comparison_instance())
        self.assertEqual(list(compilation["layers"]), ["theme", "visual_variant", "layout_contract", "layout_tree", "resolved_coordinates"])
        self.assertFalse(compilation["layers"]["theme"]["input_used"])
        self.assertFalse(compilation["layers"]["visual_variant"]["input_used"])
        self.assertEqual(compilation["layers"]["resolved_coordinates"]["status"], "pending")
        tree = compilation["layout_tree"]
        self.assertEqual(tree["contract"], "io.clayz.presentation.layout-tree/1.0")
        self.assertEqual(tree["source"]["record_id"], "layout.evidence-with-implication")
        resolved = solve_compilation(compilation)
        self.assertEqual(resolved["layers"]["resolved_coordinates"]["status"], "materialized")
        self.assertEqual(resolved["source_tree_id"], tree["tree_id"])
        boxes = {box["id"]: box for box in resolved["boxes"]}
        self.assertLess(boxes["evidence-column"]["x"], boxes["implication-column"]["x"])
        self.assertGreater(boxes["evidence-column"]["w"], boxes["implication-column"]["w"])
        self.assertEqual(boxes["decision-implication-region"]["copy_ids"], ["COPY-IMPLICATION"])

    def test_no_match_is_explicitly_unresolved_without_compilation(self) -> None:
        request = comparison_request(
            request_id="request-layout-unregistered",
            page_role="radial-constellation",
            semantic_relations=["orbits"],
            purpose_tags=["unregistered"],
        )
        resolution, receipt = resolve_layout_contract(self.runtime, request, created_at="2026-08-23T08:00:00Z")
        self.assertEqual(resolution["status"], "unresolved")
        self.assertIsNone(resolution["selected_layout_contract"])
        self.assertTrue(resolution["fallback"]["used"])
        self.assertEqual(resolution["fallback"]["reason"], "no-eligible-registered-layout-contract")
        self.assertEqual(receipt["candidates"], [])
        with self.assertRaises(LayoutContractError):
            compile_layout_contract(ROOT, self.provider, resolution, receipt, comparison_instance())

    def test_preferred_unretrieved_contract_is_not_invented(self) -> None:
        request = comparison_request(preferred_contract_id="layout.unregistered-contract")
        resolution, receipt = resolve_layout_contract(self.runtime, request, created_at="2026-08-23T08:00:00Z")
        self.assertEqual(resolution["status"], "unresolved")
        self.assertEqual(resolution["fallback"]["reason"], "preferred-contract-not-retrieved")
        self.assertEqual(receipt["selection"]["selected"], [])
        self.assertEqual(receipt["hallucination_guard"]["invented_record_count"], 0)

    def test_ambiguous_registered_matches_require_explicit_choice(self) -> None:
        records = [copy.deepcopy(record) for record in self.provider.records]
        duplicate = copy.deepcopy(next(record for record in records if record["record_id"] == "layout.evidence-with-implication"))
        duplicate["record_id"] = "layout.evidence-with-implication-alt"
        duplicate["source"]["source_id"] = "synthetic-ambiguous-contract"
        records.append(duplicate)
        runtime = CompositeIndex([IndexProvider.from_records("builtin-catalog", records)])
        resolution, receipt = resolve_layout_contract(runtime, comparison_request(), created_at="2026-08-23T08:00:00Z")
        self.assertEqual(resolution["status"], "unresolved")
        self.assertEqual(resolution["fallback"]["reason"], "ambiguous-eligible-layout-contracts")
        self.assertEqual(receipt["selection"]["selected"], [])
        self.assertEqual(len(receipt["selection"]["rejected"]), 2)

    def test_contract_payload_is_hash_bound(self) -> None:
        records = [copy.deepcopy(record) for record in self.provider.records]
        target = next(record for record in records if record["record_id"] == "layout.evidence-with-implication")
        target["source"]["sha256"] = "0" * 64
        provider = IndexProvider.from_records("builtin-catalog", records)
        runtime = CompositeIndex([provider])
        resolution, receipt = resolve_layout_contract(runtime, comparison_request(), created_at="2026-08-23T08:00:00Z")
        with self.assertRaisesRegex(LayoutContractError, "hash mismatch"):
            compile_layout_contract(ROOT, provider, resolution, receipt, comparison_instance())

    def test_binding_contract_rejects_duplicates_and_cross_layer_inputs(self) -> None:
        duplicate = comparison_instance()
        duplicate["bindings"][1]["copy_ids"] = ["COPY-EVIDENCE"]
        with self.assertRaisesRegex(LayoutContractError, "already bound"):
            validate_layout_contract_instance(duplicate)
        mixed_layers = comparison_instance()
        mixed_layers["theme"] = {"name": "should remain external"}
        with self.assertRaisesRegex(LayoutContractError, "unsupported fields"):
            validate_layout_contract_instance(mixed_layers)

    def test_public_layout_contract_records_are_brand_neutral_methods(self) -> None:
        records = [record for record in self.provider.records if record["record_type"] == "layout-contract"]
        self.assertGreaterEqual(len(records), 2)
        for record in records:
            self.assertEqual(record["classification"]["brand_scope"], "none")
            self.assertEqual(record["classification"]["asset_class"], "contract")
            self.assertEqual(record["payload"]["kind"], "path")
            self.assertNotIn(record["classification"]["asset_class"], {"template", "master", "font", "brand-kit"})


if __name__ == "__main__":
    unittest.main()
