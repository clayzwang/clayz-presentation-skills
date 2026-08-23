# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path

from packages.index_runtime import CompositeIndex, IndexProvider, mandatory_core, resolve_capabilities

ROOT = Path(__file__).resolve().parents[1]


class CapabilityRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        provider = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
        cls.runtime = CompositeIndex([provider])

    def test_core_contracts_are_deterministic_not_search_dependent(self) -> None:
        for stage in ("logic", "copy", "art-direction", "output", "supervisor"):
            core = mandatory_core(stage)
            self.assertTrue(core)
            self.assertTrue(all(item["ref"] for item in core))

    def test_art_direction_routes_each_signal_to_registered_capability(self) -> None:
        resolution, receipts = resolve_capabilities(
            self.runtime,
            stage="art-direction",
            task_mode="new-build",
            signals=["image-led", "high-risk-composition", "architecture-house"],
            languages=["zh-CN"],
            created_at="2026-08-23T05:00:00Z",
        )
        ids = {item["record_id"] for item in resolution["selected_capabilities"]}
        self.assertEqual(ids, {"cap.art.content-aware", "cap.art.ab-regression", "cap.art.architecture-house"})
        self.assertEqual(resolution["unresolved_signals"], [])
        self.assertEqual(len(receipts), 3)
        self.assertTrue(all(receipt["hallucination_guard"]["invented_record_count"] == 0 for receipt in receipts))

    def test_unknown_signal_remains_unresolved_instead_of_inventing_capability(self) -> None:
        resolution, receipts = resolve_capabilities(
            self.runtime,
            stage="art-direction",
            task_mode="new-build",
            signals=["nonexistent-capability-signal"],
            languages=["zh-CN"],
            created_at="2026-08-23T05:00:00Z",
        )
        self.assertEqual(resolution["selected_capabilities"], [])
        self.assertEqual(resolution["unresolved_signals"], ["nonexistent-capability-signal"])
        self.assertEqual(receipts[0]["candidates"], [])
        self.assertEqual(receipts[0]["fallback"]["reason"], "no-eligible-registered-record")

    def test_capability_catalog_contains_no_brand_specific_assets(self) -> None:
        provider = self.runtime.providers[0]
        for record in provider.records:
            self.assertEqual(record["record_type"], "capability")
            self.assertNotEqual(record["classification"]["brand_scope"], "brand-specific")
            self.assertNotIn(record["classification"]["asset_class"], {"template", "master", "font", "brand-kit"})


if __name__ == "__main__":
    unittest.main()
