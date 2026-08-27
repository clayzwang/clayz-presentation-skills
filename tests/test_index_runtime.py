# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from packages.index_runtime import (
    INDEX_CONTRACT,
    REQUEST_CONTRACT,
    CompositeIndex,
    IndexProvider,
    IndexRuntimeError,
    validate_record,
)


def record(
    record_id: str,
    *,
    provider_id: str,
    record_type: str = "layout-contract",
    title: str = "Balanced comparison",
    summary: str = "A semantic comparison layout with one conclusion and two evidence regions.",
    stages: list[str] | None = None,
    task_modes: list[str] | None = None,
    page_roles: list[str] | None = None,
    purpose_tags: list[str] | None = None,
    asset_class: str = "contract",
    brand_scope: str = "none",
    redistribution: str = "allowed",
    materialization: str = "allowed",
    public_catalog_eligible: bool = True,
    human_admitted: bool = True,
    quality_status: str = "admitted",
    sha: str = "0" * 64,
) -> dict:
    return {
        "contract": INDEX_CONTRACT,
        "record_id": record_id,
        "record_type": record_type,
        "provider_id": provider_id,
        "title": title,
        "summary": summary,
        "source": {
            "source_id": f"source-{record_id}",
            "source_uri": "synthetic://unit-test",
            "source_revision": "1",
            "sha256": sha,
        },
        "governance": {
            "human_admitted": human_admitted,
            "quality_status": quality_status,
            "public_catalog_eligible": public_catalog_eligible,
            "deprecated": False,
        },
        "rights": {
            "license": "Apache-2.0" if redistribution == "allowed" else "private-not-for-redistribution",
            "redistribution": redistribution,
            "materialization": materialization,
            "commercial_use": True if redistribution == "allowed" else None,
            "derivative_use": True if redistribution == "allowed" else None,
            "attribution_required": False,
            "never_copy": ["source wording"] if redistribution != "allowed" else [],
        },
        "classification": {
            "stages": stages or ["art-direction"],
            "task_modes": task_modes or ["new-build"],
            "page_roles": page_roles or ["comparison"],
            "semantic_relations": ["compares", "supports"],
            "purpose_tags": purpose_tags or ["high-density"],
            "languages": ["en-US", "zh-CN"],
            "failure_signals": [],
            "asset_class": asset_class,
            "brand_scope": brand_scope,
        },
        "payload": {"kind": "path", "ref": f"catalog/{record_id}.json"},
        "neighbors": {"physical": [], "semantic": []},
    }


def request(*, context: str = "public-open-source", query: str = "comparison evidence") -> dict:
    return {
        "contract": REQUEST_CONTRACT,
        "request_id": "req-stage-1",
        "stage": "art-direction",
        "query": query,
        "rights_context": context,
        "require_human_admission": True,
        "limit": 5,
        "filters": {
            "record_types": [],
            "provider_ids": [],
            "task_modes": ["new-build"],
            "page_roles": ["comparison"],
            "semantic_relations": [],
            "purpose_tags": [],
            "languages": ["zh-CN"],
            "failure_signals": [],
            "include_metadata_only": True,
        },
        "neighbor_expansion": {"physical": 0, "semantic": 0},
    }


class IndexRuntimeTests(unittest.TestCase):
    def test_provider_identity_and_snapshot_are_stable(self) -> None:
        first = record("layout.compare.alpha", provider_id="builtin-catalog", sha="1" * 64)
        second = record("layout.compare.beta", provider_id="builtin-catalog", sha="2" * 64)
        p1 = IndexProvider.from_records("builtin-catalog", [second, first])
        p2 = IndexProvider.from_records("builtin-catalog", [first, second])
        self.assertEqual(p1.snapshot(), p2.snapshot())
        self.assertEqual(p1.snapshot()["record_count"], 2)

    def test_public_search_excludes_private_brand_assets(self) -> None:
        generic = record("layout.compare.generic", provider_id="builtin-catalog")
        private_template = record(
            "template.local-brand.private",
            provider_id="filesystem-library",
            title="Local brand master",
            summary="A private company template stored only in the owner's local library.",
            asset_class="template",
            brand_scope="brand-specific",
            redistribution="local-private",
            materialization="local-only",
            public_catalog_eligible=False,
        )
        runtime = CompositeIndex(
            [
                IndexProvider.from_records("builtin-catalog", [generic]),
                IndexProvider.from_records("filesystem-library", [private_template]),
            ]
        )
        receipt = runtime.search(request())
        ids = [candidate["record_id"] for candidate in receipt["candidates"]]
        self.assertEqual(ids, ["layout.compare.generic"])
        self.assertEqual(receipt["hallucination_guard"]["invented_record_count"], 0)

    def test_private_runtime_can_retrieve_but_not_publish_local_brand_asset(self) -> None:
        private_template = record(
            "template.local-brand.private",
            provider_id="filesystem-library",
            title="Local brand master",
            summary="A private company template for local runtime use only.",
            asset_class="template",
            brand_scope="brand-specific",
            redistribution="local-private",
            materialization="local-only",
            public_catalog_eligible=False,
        )
        runtime = CompositeIndex([IndexProvider.from_records("filesystem-library", [private_template])])
        private_request = request(context="private-runtime", query="local brand master comparison")
        receipt = runtime.search(private_request)
        self.assertEqual(receipt["candidates"][0]["record_id"], "template.local-brand.private")
        self.assertTrue(receipt["candidates"][0]["materializable"])
        self.assertEqual(receipt["candidates"][0]["rights_decision"], "private-runtime-allowed")

    def test_owner_private_asset_is_available_to_local_or_cloud_private_runtime_only(self) -> None:
        private_reference = record(
            "reference.owner-private.cloud",
            provider_id="owner-private-library",
            record_type="reference",
            title="Owner-private cloud reference",
            summary="A private reference available only inside the owner's selected runtime.",
            asset_class="document",
            brand_scope="brand-specific",
            redistribution="owner-private",
            materialization="owner-private",
            public_catalog_eligible=False,
        )
        runtime = CompositeIndex([IndexProvider.from_records("owner-private-library", [private_reference])])
        public_receipt = runtime.search(request(query="owner private cloud reference"))
        self.assertEqual(public_receipt["candidates"], [])
        private_receipt = runtime.search(request(context="private-runtime", query="owner private cloud reference"))
        self.assertEqual(private_receipt["candidates"][0]["record_id"], "reference.owner-private.cloud")
        self.assertTrue(private_receipt["candidates"][0]["materializable"])

    def test_metadata_only_records_are_non_materializable(self) -> None:
        reference = record(
            "reference.external.metadata",
            provider_id="external-ephemeral",
            record_type="reference",
            title="External composition research",
            summary="Metadata-only research source for conceptual comparison patterns.",
            asset_class="document",
            redistribution="metadata-only",
            materialization="forbidden",
            public_catalog_eligible=True,
        )
        runtime = CompositeIndex([IndexProvider.from_records("external-ephemeral", [reference])])
        receipt = runtime.search(request(query="composition research comparison"))
        self.assertEqual(receipt["candidates"][0]["rights_decision"], "metadata-only")
        self.assertFalse(receipt["candidates"][0]["materializable"])

    def test_shared_record_is_available_to_stage_request(self) -> None:
        shared = record(
            "failure.card-overuse",
            provider_id="builtin-catalog",
            record_type="failure-pattern",
            title="Card overuse",
            summary="Repeated equal-weight containers erase hierarchy.",
            stages=["shared"],
        )
        runtime = CompositeIndex([IndexProvider.from_records("builtin-catalog", [shared])])
        receipt = runtime.search(request(query="card hierarchy comparison"))
        self.assertEqual(receipt["candidates"][0]["record_id"], "failure.card-overuse")

    def test_no_match_emits_explicit_fallback_without_invention(self) -> None:
        generic = record("layout.compare.generic", provider_id="builtin-catalog")
        runtime = CompositeIndex([IndexProvider.from_records("builtin-catalog", [generic])])
        no_match = request(query="unrelated")
        no_match["filters"]["page_roles"] = ["timeline"]
        receipt = runtime.search(no_match)
        self.assertEqual(receipt["candidates"], [])
        self.assertEqual(receipt["fallback"]["reason"], "no-eligible-registered-record")
        self.assertEqual(receipt["hallucination_guard"]["invented_record_count"], 0)
        with self.assertRaises(IndexRuntimeError):
            runtime.finalize_receipt(receipt, selected={"invented.layout": "looks useful"})

    def test_public_catalog_validation_rejects_unlicensed_brand_template(self) -> None:
        unsafe = record(
            "template.brand.unsafe",
            provider_id="builtin-catalog",
            asset_class="template",
            brand_scope="brand-specific",
            redistribution="metadata-only",
            materialization="forbidden",
            public_catalog_eligible=True,
        )
        with self.assertRaises(IndexRuntimeError):
            validate_record(unsafe)

    def test_jsonl_provider_round_trip(self) -> None:
        item = record("layout.compare.generic", provider_id="builtin-catalog")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(json.dumps(item) + "\n", encoding="utf-8")
            provider = IndexProvider.from_jsonl("builtin-catalog", path)
            self.assertEqual(provider.records[0]["record_id"], item["record_id"])


if __name__ == "__main__":
    unittest.main()
