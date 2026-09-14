from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from validate_supervision_report import (  # noqa: E402
    _canonical_sha256,
    _retrieval_totals,
    validate_generation_efficiency,
    validate_requirement_traceability,
    validate_retrieval_quality,
    validate_stage_snapshots,
)
from validate_logic_package import validate_package as validate_logic_package  # noqa: E402
from acceptance_contract import validate_stage_retrieval_budget  # noqa: E402


class MethodGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = json.loads((ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8"))
        cls.plan = json.loads((ROOT / "tests" / "fixtures" / "synthetic-art-direction-plan.json").read_text(encoding="utf-8"))

    def _snapshots(self) -> dict:
        snapshots = {
            "logic": {"brief": self.package["brief"], "logic_layer": self.package["logic_layer"]},
            "copy": self.package["copy_layer"],
            "art_direction": {
                key: self.plan.get(key)
                for key in ("communication_contract", "art_direction", "decision_log", "typography_contract", "deck_rhythm", "slides")
            },
        }
        return {
            stage: {
                "artifact_sha256": character * 64,
                "snapshot_sha256": _canonical_sha256(snapshot),
                "snapshot": snapshot,
            }
            for stage, snapshot, character in (
                ("logic", snapshots["logic"], "a"),
                ("copy", snapshots["copy"], "b"),
                ("art_direction", snapshots["art_direction"], "c"),
            )
        }

    def test_stage_snapshots_are_verbatim_and_hash_bound(self) -> None:
        errors: list[str] = []
        validate_stage_snapshots(self._snapshots(), self.package, self.plan, errors)
        self.assertEqual(errors, [])
        drifted = copy.deepcopy(self._snapshots())
        drifted["logic"]["snapshot"]["logic_layer"]["narrative"]["opening"] = "drifted"
        errors = []
        validate_stage_snapshots(drifted, self.package, self.plan, errors)
        self.assertTrue(any("verbatim immutable copy" in error for error in errors))

    def test_requirement_traceability_covers_every_acceptance_requirement(self) -> None:
        trace = [
            {
                "requirement_id": item["requirement_id"],
                "logic_refs": ["logic:S01"], "copy_refs": ["copy:S01"],
                "art_direction_refs": ["art:S01"], "output_refs": ["pptx:S01"],
                "supervisor_refs": ["check:S01"], "status": "pass",
                "evidence": "Synthetic requirement is traceable through all governed stages.",
                "earliest_owner": "logic" if item["owner_stage"] == "logic" else "system",
            }
            for item in self.package["acceptance_contract"]["requirements"]
        ]
        errors: list[str] = []
        failed = validate_requirement_traceability(trace, self.package["acceptance_contract"], errors)
        self.assertEqual(errors, [])
        self.assertEqual(failed, set())

    def test_retrieval_and_generation_budgets_are_auditable(self) -> None:
        evidence = self.plan["index_evidence"]
        totals = _retrieval_totals(evidence)
        quality = {
            "status": "pass", "total_receipts": totals["receipts"],
            "total_candidates": totals["candidates"], "total_selected": totals["selected"],
            "unique_selected": totals["unique_selected"], "material_adoptions": totals["material_adoptions"],
            "stage_summaries": totals["stage_summaries"],
            "evidence": "Ranked stage receipts remain within the task acceptance budget.",
        }
        errors: list[str] = []
        validated = validate_retrieval_quality(quality, evidence, self.package["acceptance_contract"], errors)
        self.assertEqual(errors, [])
        efficiency = {
            "status": "pass", "run_mode": "warm", "total_seconds": 600,
            "stage_seconds": {"root": 30, "preflight": 60, "logic": 120, "copy": 60, "art-direction": 90, "output": 180, "supervisor": 45, "delivery": 15},
            "retrieval_receipt_count": validated["receipts"], "candidate_count": validated["candidates"],
            "selected_count": validated["selected"], "write_count": 1, "render_count": 1,
            "repair_count": 0, "evidence": "One bounded write and render completed within the warm-run budget.",
        }
        over_budget = validate_generation_efficiency(efficiency, self.package["acceptance_contract"], validated, errors)
        self.assertFalse(over_budget)
        self.assertEqual(errors, [])

    def test_acceptance_contract_blocks_cover_verdict_and_missing_problem_chain(self) -> None:
        package = copy.deepcopy(self.package)
        acceptance = package["acceptance_contract"]
        acceptance["cover_policy"] = {"mode": "topic-only", "conclusion_allowed_roles": ["recommendation", "decision", "closing"]}
        acceptance["narrative_policy"] = {
            "problem_before_recommendation": True,
            "minimum_friction_impact_pairs": 1,
            "required_relation_types": ["cause", "supports"],
        }
        slide = package["logic_layer"]["slides"][0]
        slide["narrative_role"] = "cover"
        slide["claim_status"] = "recommendation"
        slide["decision_weight"] = "high"
        errors = validate_logic_package(package, "copy-approved")
        self.assertTrue(any("topic-only cover" in error for error in errors), errors)
        self.assertTrue(any("closing slide" in error for error in errors), errors)
        self.assertTrue(any("friction-impact relations" in error for error in errors), errors)

    def test_executive_summary_recommendation_does_not_bypass_problem_first_policy(self) -> None:
        package = copy.deepcopy(self.package)
        acceptance = package["acceptance_contract"]
        acceptance["narrative_policy"] = {
            "problem_before_recommendation": True,
            "minimum_friction_impact_pairs": 1,
            "required_relation_types": ["supports"],
        }
        slide = package["logic_layer"]["slides"][0]
        slide["narrative_role"] = "executive-summary"
        slide["claim_status"] = "recommendation"
        errors = validate_logic_package(package, "copy-approved")
        self.assertTrue(any("friction-impact relations" in error for error in errors), errors)

    def test_stage_retrieval_budget_is_cumulative_across_receipts(self) -> None:
        evidence = copy.deepcopy(self.package["index_evidence"])
        duplicate = copy.deepcopy(evidence["stage_receipts"]["logic"][0])
        duplicate["receipt_id"] = "receipt-cumulative-budget-regression"
        evidence["stage_receipts"]["logic"].append(duplicate)
        acceptance = copy.deepcopy(self.package["acceptance_contract"])
        acceptance["performance_budget"]["max_candidates_per_stage"] = 1
        errors: list[str] = []
        validate_stage_retrieval_budget(evidence, acceptance, ["logic"], "index_evidence", errors)
        self.assertTrue(any("cumulative candidates" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
