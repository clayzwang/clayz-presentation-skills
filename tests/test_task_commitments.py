#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Tests for source-aware task acceptance enrichment."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
for path in (ROOT, VALIDATORS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from task_commitments import DEFAULT_POINT_SIZES, enrich_task_acceptance  # noqa: E402


def _config() -> dict[str, object]:
    return {
        "theme": {
            "typography": {
                "primary_fonts": ["Aptos", "Arial", "Noto Sans CJK SC", "sans-serif"],
                "body_minimum_pt": 18,
                "minimum_audience_text_pt": 12,
                "minimum_chart_text_pt": 12,
            },
            "layout_roles": ["cover", "body", "closing"],
        },
        "layout": {"column_count": 12},
    }


class TaskCommitmentTests(unittest.TestCase):
    def test_missing_typography_and_page_defaults_become_explicit_commitments(self) -> None:
        enriched, brief = enrich_task_acceptance({}, _config())

        ids = {item["requirement_id"] for item in enriched["requirements"]}
        expected_ids = {
            "COMMIT-FONT-CJK",
            "COMMIT-FONT-LATIN",
            "COMMIT-FONT-DIGITS",
            "COMMIT-FONT-CHART",
            "COMMIT-SIZE-TITLE",
            "COMMIT-SIZE-BODY",
            "COMMIT-SIZE-CHART",
            "COMMIT-SIZE-FOOTNOTE",
            "COMMIT-SIZE-PAGE-NUMBER",
            "COMMIT-COVER",
            "COMMIT-CLOSING",
            "COMMIT-PAGE-NUMBER",
        }
        self.assertTrue(expected_ids <= ids)
        self.assertIn("COMMIT-CHART-UNIT", ids)
        self.assertEqual(enriched["cover_policy"]["cover_required"], True)
        self.assertEqual(enriched["cover_policy"]["closing_required"], True)
        self.assertEqual(enriched["typography_policy"]["required_cjk_families"], ["Noto Sans CJK SC"])
        self.assertEqual(brief["chart_unit_applicable"], False)
        chart_unit = next(item for item in enriched["requirements"] if item["requirement_id"] == "COMMIT-CHART-UNIT")
        self.assertIn("otherwise not-applicable", chart_unit["expected"])
        self.assertIn("hard classification does not set a release block", brief["text"])

    def test_config_values_and_personal_origin_are_retained_without_user_invention(self) -> None:
        config = _config()
        config["theme"]["typography"] = {
            "primary_fonts": ["Arial", "Noto Sans CJK SC"],
            "body_minimum_pt": 20,
            "minimum_chart_text_pt": 14,
            "title_minimum_pt": 28,
            "footnote_minimum_pt": 12,
            "page_number_minimum_pt": 10,
        }
        origin_map = [
            {"path": "theme.typography.body_minimum_pt", "source": "personal:profile-01"},
            {"path": "theme.typography.primary_fonts", "source": "personal:profile-01"},
        ]

        enriched, brief = enrich_task_acceptance({}, config, origin_map)
        by_id = {item["requirement_id"]: item for item in enriched["requirements"]}
        self.assertEqual(by_id["COMMIT-SIZE-BODY"]["expected"], 20)
        self.assertEqual(by_id["COMMIT-SIZE-TITLE"]["expected"], 28)
        self.assertEqual(by_id["COMMIT-SIZE-CHART"]["expected"], 14)
        self.assertEqual(by_id["COMMIT-SIZE-BODY"]["source"], "personal:profile-01")
        self.assertEqual(by_id["COMMIT-FONT-LATIN"]["source"], "personal:profile-01")
        self.assertEqual(
            by_id["COMMIT-FONT-CHART"]["expected"],
            {
                "cjk": "Noto Sans CJK SC",
                "latin": "Arial",
                "digits": "Arial",
                "role_priority": "language-role family before generic chart family",
            },
        )
        self.assertIn("cjk:personal:profile-01", by_id["COMMIT-FONT-CHART"]["source"])
        self.assertIn("latin:personal:profile-01", by_id["COMMIT-FONT-CHART"]["source"])
        self.assertTrue(all(not str(item.get("source", "")).startswith("user") for item in by_id.values()))
        self.assertEqual(brief["source_precedence"], ["user", "personal", "default"])

    def test_central_point_size_fallbacks_are_visible_in_draft_and_brief(self) -> None:
        enriched, brief = enrich_task_acceptance({}, {"theme": {"typography": {}}})
        by_id = {item["requirement_id"]: item for item in enriched["requirements"]}
        self.assertEqual(by_id["COMMIT-SIZE-TITLE"]["expected"], DEFAULT_POINT_SIZES["title"])
        self.assertEqual(by_id["COMMIT-SIZE-BODY"]["expected"], DEFAULT_POINT_SIZES["body"])
        self.assertEqual(by_id["COMMIT-SIZE-CHART"]["expected"], DEFAULT_POINT_SIZES["chart"])
        self.assertEqual(by_id["COMMIT-SIZE-FOOTNOTE"]["expected"], DEFAULT_POINT_SIZES["footnote"])
        self.assertEqual(by_id["COMMIT-SIZE-PAGE-NUMBER"]["expected"], DEFAULT_POINT_SIZES["page_number"])
        self.assertEqual(
            by_id["COMMIT-PAGE-NUMBER"]["expected"],
            {
                "required": True,
                "position": "footer-right",
                "scope": "body-and-closing",
                "start": 1,
                "cover_counting": False,
                "mechanism": "editable-footer-field",
            },
        )
        self.assertIn("COMMIT-SIZE-TITLE", brief["added_requirement_ids"])
        self.assertTrue(any("COMMIT-SIZE-PAGE-NUMBER" in line for line in brief["lines"]))

    def test_quantitative_chart_unit_commitment_is_conditional(self) -> None:
        no_chart, no_chart_brief = enrich_task_acceptance({"slides": [{"role": "body", "text": "Explain the process."}]}, _config())
        with_chart, with_chart_brief = enrich_task_acceptance(
            {"slides": [{"role": "body", "dominant_medium": "data-chart", "unit": "%"}]},
            _config(),
        )
        self.assertIn("COMMIT-CHART-UNIT", {item["requirement_id"] for item in no_chart["requirements"]})
        self.assertIn("COMMIT-CHART-UNIT", {item["requirement_id"] for item in with_chart["requirements"]})
        self.assertFalse(no_chart_brief["chart_unit_applicable"])
        self.assertTrue(with_chart_brief["chart_unit_applicable"])

    def test_explicit_values_and_legacy_blocking_are_preserved(self) -> None:
        draft = {
            "requirements": [
                {
                    "requirement_id": "REQ-USER-EXACT",
                    "category": "content",
                    "statement": "Use the supplied wording exactly.",
                    "owner_stage": "logic",
                    "expected": "supplied wording",
                    "source": "user-attached-request",
                    "classification": "soft",
                    "verification_method": "compare with task input",
                    "blocking": True,
                },
                {
                    "requirement_id": "REQ-LEGACY-BODY",
                    "category": "typography",
                    "statement": "Body font size remains readable.",
                    "owner_stage": "output",
                    "commitment_kind": "size-body",
                    "blocking": True,
                },
            ],
            "cover_policy": {"mode": "not-applicable", "conclusion_allowed_roles": ["analysis"]},
            "narrative_policy": {"problem_before_recommendation": False, "minimum_friction_impact_pairs": 0, "required_relation_types": []},
        }
        original = copy.deepcopy(draft)
        enriched, _ = enrich_task_acceptance(draft, _config())
        exact = next(item for item in enriched["requirements"] if item["requirement_id"] == "REQ-USER-EXACT")
        legacy = next(item for item in enriched["requirements"] if item["requirement_id"] == "REQ-LEGACY-BODY")
        self.assertEqual({key: exact[key] for key in original["requirements"][0]}, original["requirements"][0])
        self.assertTrue(legacy["blocking"])
        self.assertEqual(legacy["classification"], "hard")
        self.assertEqual(legacy["expected"], 18)
        self.assertEqual(enriched["cover_policy"]["cover_required"], False)
        self.assertEqual(enriched["cover_policy"]["closing_required"], True)
        self.assertEqual(draft, original)

    def test_explicit_cjk_policy_outranks_config_candidate(self) -> None:
        draft = {"typography_policy": {"mode": "explicit-family", "required_cjk_families": ["UserFont"], "exceptions": []}}
        enriched, _ = enrich_task_acceptance(draft, _config())
        cjk = next(item for item in enriched["requirements"] if item["requirement_id"] == "COMMIT-FONT-CJK")
        self.assertEqual(cjk["expected"], "UserFont")
        self.assertEqual(cjk["source"], "acceptance:typography_policy.required_cjk_families")

    def test_fractional_configured_point_size_is_preserved(self) -> None:
        config = _config()
        config["theme"]["typography"]["body_minimum_pt"] = 20.5
        enriched, _ = enrich_task_acceptance({}, config)
        body = next(item for item in enriched["requirements"] if item["requirement_id"] == "COMMIT-SIZE-BODY")
        self.assertEqual(body["expected"], 20.5)

    def test_unknown_single_font_is_a_unified_family_for_all_roles(self) -> None:
        config = _config()
        config["theme"]["typography"]["primary_fonts"] = ["UserFont"]
        enriched, _ = enrich_task_acceptance({}, config)
        by_id = {item["requirement_id"]: item for item in enriched["requirements"]}
        for requirement_id in ("COMMIT-FONT-CJK", "COMMIT-FONT-LATIN", "COMMIT-FONT-DIGITS"):
            self.assertEqual(by_id[requirement_id]["expected"], "UserFont")
        self.assertEqual(
            by_id["COMMIT-FONT-CHART"]["expected"],
            {
                "cjk": "UserFont",
                "latin": "UserFont",
                "digits": "UserFont",
                "role_priority": "language-role family before generic chart family",
            },
        )

    def test_user_primary_font_overrides_default_role_fonts_in_real_config(self) -> None:
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        typography = config["theme"]["typography"]
        # Model the central role fields that a future merged config may carry,
        # while keeping the actual repository default as the base snapshot.
        typography["cjk_fonts"] = ["Noto Sans CJK SC"]
        typography["latin_fonts"] = ["Aptos"]
        typography["digit_fonts"] = ["Aptos"]
        typography["chart_fonts"] = ["Aptos"]
        typography["primary_fonts"] = ["UserFont"]
        enriched, _ = enrich_task_acceptance(
            {},
            config,
            [
                {"path": "theme.typography.cjk_fonts", "source": "default:config"},
                {"path": "theme.typography.latin_fonts", "source": "default:config"},
                {"path": "theme.typography.digit_fonts", "source": "default:config"},
                {"path": "theme.typography.chart_fonts", "source": "default:config"},
                {"path": "theme.typography.primary_fonts", "source": "user:task-overrides"},
            ],
        )
        by_id = {item["requirement_id"]: item for item in enriched["requirements"]}
        self.assertEqual(by_id["COMMIT-FONT-CJK"]["expected"], "UserFont")
        self.assertEqual(by_id["COMMIT-FONT-LATIN"]["expected"], "UserFont")
        self.assertEqual(by_id["COMMIT-FONT-DIGITS"]["expected"], "UserFont")
        self.assertEqual(by_id["COMMIT-FONT-CHART"]["expected"]["cjk"], "UserFont")
        self.assertEqual(by_id["COMMIT-FONT-CHART"]["expected"]["latin"], "UserFont")

    def test_configured_page_number_policy_is_bound_field_by_field(self) -> None:
        config = _config()
        config["theme"]["page_number_policy"] = {
            "required": True,
            "position": "footer-left",
            "scope": "all-slides",
            "start": 3,
            "cover_counting": True,
            "mechanism": "master-field",
        }
        enriched, _ = enrich_task_acceptance({}, config)
        page = next(item for item in enriched["requirements"] if item["requirement_id"] == "COMMIT-PAGE-NUMBER")
        self.assertEqual(page["expected"], config["theme"]["page_number_policy"])
        self.assertEqual(page["source"], "config:theme.page_number_policy")

    def test_explicit_no_page_numbers_is_retained_as_false_requirement(self) -> None:
        enriched, _ = enrich_task_acceptance({"page_numbers_required": False}, _config())
        page = next(item for item in enriched["requirements"] if item["requirement_id"] == "COMMIT-PAGE-NUMBER")
        self.assertEqual(page["expected"]["required"], False)
        self.assertEqual(page["expected"]["position"], "footer-right")
        self.assertEqual(enriched["cover_policy"]["cover_required"], True)

    def test_inherit_page_policy_requires_a_template_reference(self) -> None:
        draft = {
            "page_number_policy": {
                "required": True,
                "position": "inherit",
                "scope": "inherited",
                "mechanism": "master",
            }
        }
        without_template, _ = enrich_task_acceptance(draft, _config())
        without = next(item for item in without_template["requirements"] if item["requirement_id"] == "COMMIT-PAGE-NUMBER")
        self.assertEqual(without["expected"]["position"], "footer-right")
        self.assertEqual(without["expected"]["scope"], "body-and-closing")
        self.assertEqual(without["expected"]["mechanism"], "editable-footer-field")

        draft["page_number_policy"]["template_policy"] = "master://task-template"
        with_template, _ = enrich_task_acceptance(draft, _config())
        inherited = next(item for item in with_template["requirements"] if item["requirement_id"] == "COMMIT-PAGE-NUMBER")
        self.assertEqual(inherited["expected"]["position"], "inherited:master://task-template")
        self.assertEqual(inherited["expected"]["scope"], "inherited:master://task-template")
        self.assertEqual(inherited["expected"]["mechanism"], "inherited:master://task-template")

    def test_cover_and_closing_policy_values_are_independent(self) -> None:
        enriched, _ = enrich_task_acceptance(
            {"cover_policy": {"mode": "topic-only", "cover_required": False, "closing_required": True}},
            _config(),
        )
        by_id = {item["requirement_id"]: item for item in enriched["requirements"]}
        self.assertFalse(by_id["COMMIT-COVER"]["expected"])
        self.assertTrue(by_id["COMMIT-CLOSING"]["expected"])

    def test_enrichment_is_idempotent_and_does_not_duplicate_commitments(self) -> None:
        first, _ = enrich_task_acceptance({}, _config())
        second, _ = enrich_task_acceptance(first, _config())
        self.assertEqual(first, second)
        ids = [item["requirement_id"] for item in second["requirements"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_new_merged_override_refreshes_generated_default_but_preserves_user_requirement(self) -> None:
        base = _config()
        first, _ = enrich_task_acceptance(
            {
                "requirements": [
                    {
                        "requirement_id": "REQ-USER-BODY",
                        "category": "typography",
                        "statement": "Use the user's exact body-size exception.",
                        "owner_stage": "output",
                        "expected": 15,
                        "source": "user-request",
                        "classification": "hard",
                        "verification_method": "compare explicit task exception",
                        "blocking": False,
                    }
                ]
            },
            base,
        )
        overridden = copy.deepcopy(base)
        overridden["theme"]["typography"]["body_minimum_pt"] = 20
        second, _ = enrich_task_acceptance(first, overridden)
        by_id = {item["requirement_id"]: item for item in second["requirements"]}
        self.assertEqual(by_id["COMMIT-SIZE-BODY"]["expected"], 20)
        self.assertEqual(by_id["COMMIT-SIZE-BODY"]["source"], "config:theme.typography.body_minimum_pt")
        self.assertEqual(by_id["REQ-USER-BODY"]["expected"], 15)
        self.assertEqual(by_id["REQ-USER-BODY"]["source"], "user-request")

    def test_hard_defaults_are_nonblocking_and_narrative_has_no_quota(self) -> None:
        enriched, _ = enrich_task_acceptance(
            {"narrative_policy": {"problem_before_recommendation": False, "minimum_friction_impact_pairs": 0, "required_relation_types": []}},
            _config(),
        )
        defaults = [item for item in enriched["requirements"] if str(item["requirement_id"]).startswith("COMMIT-")]
        self.assertTrue(defaults)
        self.assertTrue(all(item["classification"] == "hard" and item["blocking"] is False for item in defaults))
        self.assertFalse(any(item["category"] == "narrative" for item in defaults))
        self.assertEqual(enriched["narrative_policy"]["minimum_friction_impact_pairs"], 0)

    def test_wrapper_config_and_tuple_interface_are_supported(self) -> None:
        result = enrich_task_acceptance({}, {"config": _config()})
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        enriched, brief = result
        self.assertIsInstance(enriched, dict)
        self.assertIsInstance(brief, dict)
        self.assertEqual(enriched["requirements"][0]["source"], "config:theme.typography.primary_fonts")


if __name__ == "__main__":
    unittest.main(verbosity=2)
