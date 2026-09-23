#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Independent black-box acceptance and adversarial tests for the calibrated route.

These tests deliberately construct task-local files and invoke the public
validator/CLI surfaces.  They do not patch ``validate_report`` and do not
equate a caller-provided label, prose evidence reference, or JSON hash with
the fact it is meant to prove.
"""

from __future__ import annotations

import builtins
import copy
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
# The caller selects the runtime (the acceptance command uses the bundled
# Python).  A test file must remain portable and must not encode a developer
# home directory or a private dependency path.
PYTHON = Path(os.environ.get("CALIBRATED_AUDIT_PYTHON", sys.executable))

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "packages" / "validators") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages" / "validators"))

from tests.calibrated_audit_fixtures import (  # noqa: E402
    assert_real_png,
    build_minimal_pptx,
    build_synthetic_pixel_render,
    file_ref,
    json_bytes,
    patch_theme_east_asian_font,
    sha256_file,
    write_json,
)


def _acceptance_contract(*, include_soft: bool = True) -> dict[str, object]:
    from acceptance_contract import acceptance_contract_digest  # noqa: E402

    requirements: list[dict[str, object]] = [
        {
            "requirement_id": "REQ-RAW-USER",
            "category": "content",
            "statement": "Read the exact current user request before authoring.",
            "owner_stage": "root",
            "verification_method": "task-byte-bound evidence",
            "blocking": True,
            "classification": "hard",
        },
    ]
    if include_soft:
        requirements.append(
            {
                "requirement_id": "REQ-VISUAL-QUALITY",
                "category": "visual",
                "statement": "Disclose visual quality defects and unverified checks honestly.",
                "owner_stage": "supervisor",
                "verification_method": "independent audit observation",
                "blocking": False,
                "classification": "soft",
            }
        )
    value: dict[str, object] = {
        "contract": "io.clayz.presentation.task-acceptance/1.0",
        "requirements": requirements,
        "cover_policy": {"mode": "topic-only", "conclusion_allowed_roles": ["analysis", "decision"]},
        "narrative_policy": {
            "problem_before_recommendation": False,
            "minimum_friction_impact_pairs": 0,
            "required_relation_types": [],
        },
        "typography_policy": {
            "mode": "no-explicit-requirement",
            "required_cjk_families": [],
            "exceptions": [],
        },
        "performance_budget": {
            "run_mode": "either",
            "max_total_seconds": 60,
            "stage_seconds": {
                "root": 10,
                "preflight": 10,
                "logic": 10,
                "copy": 10,
                "art-direction": 10,
                "output": 10,
                "supervisor": 10,
                "delivery": 10,
            },
            "max_receipts_per_stage": 3,
            "max_candidates_per_stage": 5,
            "max_selected_per_stage": 3,
            "max_write_count": 2,
            "max_render_count": 2,
            "max_repair_count": 1,
        },
    }
    value["contract_sha256"] = acceptance_contract_digest(value)
    return value


def _evidence_ref(path: Path, *, fragment: str | None = None) -> str:
    suffix = f"#{fragment}" if fragment else ""
    # Evidence refs use a stable bound-artifact token and the current hash.
    # Negative cases deliberately omit the hash to ensure names alone cannot
    # prove a check.
    return f"{path.name}{suffix} sha256={sha256_file(path)}"


class IndependentAuditAdversarialTests(unittest.TestCase):
    """Check independent context, binding, coverage, and honest status rules."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="calibrated-audit-independent-")
        self.work = Path(self.temp.name)
        self.task = write_json(self.work / "raw-user-request.json", {"request": "Build the requested decision deck.", "revision": 1})
        self.acceptance = write_json(self.work / "acceptance-rules.json", _acceptance_contract())
        self.supervisor_rules = write_json(
            self.work / "supervisor-rules.json",
            {
                "fixed_commitments": [
                    {
                        "rule_id": "SUP-READ-RAW",
                        "statement": "Read the raw user request directly.",
                        "classification": "hard",
                    },
                    {
                        "rule_id": "SUP-RETURN-CONTROL",
                        "statement": "Return control after release.",
                        "classification": "soft",
                    },
                ],
                "explicit_changes": [],
            },
        )
        self.package = write_json(self.work / "package.json", {"source": "logic", "finding": "synthetic"})
        self.plan = write_json(self.work / "plan.json", {"source": "art-direction", "status": "approved"})
        self.qa = write_json(self.work / "qa.json", {"source": "output", "status": "complete"})
        self.inventory = write_json(self.work / "inventory.json", {"source": "inventory", "status": "complete"})
        self.pptx = build_minimal_pptx(self.work / "final.pptx")
        self.render = build_synthetic_pixel_render(self.work / "render-01.png")
        assert_real_png(self.render)
        self.run_id = "run-calibrated-independent-001"
        self.task_sha = sha256_file(self.task)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _coverage(self, *, render_status: str = "complete", refs: list[str] | None = None) -> dict[str, object]:
        refs = refs or [_evidence_ref(self.package)]
        return {
            "hard_requirement_ids": ["REQ-RAW-USER"],
            "soft_requirement_ids": ["REQ-VISUAL-QUALITY"],
            "requirements": [
                {
                    "requirement_id": "REQ-RAW-USER",
                    "classification": "hard",
                    "status": "pass",
                    "evidence_refs": list(refs),
                    "observation": "The auditor opened the task-local raw request bytes.",
                },
                {
                    "requirement_id": "REQ-VISUAL-QUALITY",
                    "classification": "soft",
                    "status": "pass",
                    "evidence_refs": list(refs),
                    "observation": "The synthetic pixel fixture is present and clearly marked synthetic.",
                },
            ],
            "rules": [
                {
                    "rule_id": "SUP-READ-RAW",
                    "source": "fixed_commitment",
                    "status": "pass",
                    "evidence_refs": list(refs),
                    "observation": "The auditor opened the raw task request before review.",
                },
                {
                    "rule_id": "SUP-RETURN-CONTROL",
                    "source": "fixed_commitment",
                    "status": "pass",
                    "evidence_refs": list(refs),
                    "observation": "The release remains returnable to the user.",
                },
            ],
            "render_status": render_status,
        }

    def _create(self, *, output: Path | None = None, coverage: dict[str, object] | None = None, findings: list[dict[str, object]] | None = None, source_records: object | None = None, render_evidence: object = ..., context: dict[str, object] | None = None) -> dict[str, object]:
        from independent_audit import create_auditor_artifact  # noqa: E402

        if render_evidence is ...:
            render_evidence = {"synthetic-pixel-render": self.render}

        return create_auditor_artifact(
            task_request=self.task,
            acceptance_rules=self.acceptance,
            supervisor_rules=self.supervisor_rules,
            source_records=source_records or {
                "package": self.package,
                "plan": self.plan,
                "qa": self.qa,
                "inventory": self.inventory,
            },
            final_pptx=self.pptx,
            render_evidence=render_evidence,
            coverage=coverage or self._coverage(),
            findings=findings or [],
            independent_context=context
            or {
                "execution_mode": "same-model-new-context",
                "context_id": "auditor-context-001",
                "model_identity_disclosure": "same-model-possible",
                "limitations": ["Synthetic fixture; native Office render was not executed."],
            },
            run_id=self.run_id,
            task_request_sha256=self.task_sha,
            output=output,
            audited_at="2026-09-14T01:20:00Z",
        )

    def test_real_minimal_pptx_and_pixel_fixture_are_nonempty_and_explicitly_synthetic(self) -> None:
        self.assertGreater(self.pptx.stat().st_size, 1000)
        assert_real_png(self.render)
        self.assertEqual(self.render.suffix, ".png")

    def test_valid_artifact_accepts_one_auditor_context_without_five_model_claim(self) -> None:
        from independent_audit import validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        validate_auditor_artifact(
            artifact,
            expected_run_id=self.run_id,
            expected_task_request_sha256=self.task_sha,
            expected_pptx_sha256=sha256_file(self.pptx),
        )
        self.assertEqual(artifact["independent_context"]["execution_mode"], "same-model-new-context")
        self.assertIn("native Office render was not executed", artifact["independent_context"]["limitations"][0])

    def test_missing_native_render_is_deferred_and_never_clean(self) -> None:
        from independent_audit import validate_auditor_artifact  # noqa: E402

        coverage = self._coverage(render_status="deferred")
        artifact = self._create(coverage=coverage, render_evidence={})
        artifact["render_evidence"] = []
        artifact["audit_status"] = "incomplete-evidence"
        artifact["record_sha256"] = importlib.import_module("independent_audit").canonical_record_sha256(artifact)
        validate_auditor_artifact(artifact)
        self.assertEqual(artifact["audit_status"], "incomplete-evidence")

    def test_free_form_finding_evidence_reference_cannot_prove_a_finding(self) -> None:
        from independent_audit import IndependentAuditError, validate_auditor_artifact  # noqa: E402

        findings = [
            {
                "finding_id": "F-UNSUPPORTED",
                "requirement_ids": ["REQ-VISUAL-QUALITY"],
                "rule_ids": [],
                "slide_ids": ["S1"],
                "owner_layer": "supervisor",
                "severity": "major",
                "statement": "The visual defect is disclosed.",
                "expected": "The defect is disclosed with bound evidence.",
                "actual": "The defect is only asserted in prose.",
                "impact": "The audit cannot be independently reproduced.",
                "evidence_refs": ["render-01.png"],
                "recommended_change": "Review the final slide manually.",
            }
        ]
        artifact = self._create(findings=findings)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_free_form_coverage_evidence_reference_cannot_prove_a_requirement(self) -> None:
        from independent_audit import IndependentAuditError, validate_auditor_artifact  # noqa: E402

        artifact = self._create(coverage=self._coverage(refs=["package.json"]))
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_expected_source_kind_self_assertion_cannot_replace_known_source_binding(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        # Re-label an actual output record as an invented source and recompute
        # the outer record hash.  A label and a matching self-declared list do
        # not establish that the file is the required upstream calibration.
        artifact["source_records"][0]["kind"] = "invented-source-kind"
        artifact["expected_source_kinds"] = sorted(row["kind"] for row in artifact["source_records"])
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_missing_or_unavailable_acceptance_validator_must_not_widen_to_contract_only(self) -> None:
        import independent_audit  # noqa: E402

        artifact = self._create()
        original_import = builtins.__import__

        def blocked_import(name: str, *args: object, **kwargs: object):
            if name == "acceptance_contract":
                raise ImportError("simulated missing validator")
            return original_import(name, *args, **kwargs)

        with mock.patch.object(builtins, "__import__", blocked_import):
            # A malformed acceptance payload has only its contract marker; a
            # missing helper must fail closed instead of silently downgrading.
            self.acceptance.write_bytes(json_bytes({"contract": "io.clayz.presentation.task-acceptance/1.0"}))
            artifact["acceptance_rules"] = file_ref(self.acceptance)
            artifact["record_sha256"] = independent_audit.canonical_record_sha256(artifact)
            with self.assertRaises(independent_audit.IndependentAuditError):
                independent_audit.validate_auditor_artifact(artifact)

    def test_supervisor_added_hard_commitment_must_appear_in_audit_coverage(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        # Establish a valid baseline first; otherwise a malformed Supervisor
        # rules file could hide whether the missing coverage was detected.
        artifact = self._create()
        supervisor = {
            "fixed_commitments": [
                {
                    "rule_id": "SUP-READ-RAW",
                    "statement": "Read the raw user request directly.",
                    "classification": "hard",
                },
                {
                    "rule_id": "SUP-NEW-HARD",
                    "statement": "Auditor must bind the final PPTX and render evidence.",
                    "classification": "hard",
                },
            ],
            "explicit_changes": [],
        }
        self.supervisor_rules.write_bytes(json_bytes(supervisor))
        artifact["supervisor_rules"] = file_ref(self.supervisor_rules)
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_failed_audit_finding_cannot_be_relabelled_clean(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        finding = {
            "finding_id": "F-01",
            "requirement_ids": ["REQ-VISUAL-QUALITY"],
            "rule_ids": [],
            "slide_ids": ["S1"],
            "owner_layer": "supervisor",
            "severity": "major",
            "statement": "The final slide has a visible issue.",
            "expected": "The final slide is visually complete.",
            "actual": "The final slide has a visible issue.",
            "impact": "A downstream user may misread the result.",
            "evidence_refs": [_evidence_ref(self.render)],
            "recommended_change": "Repair the final slide in a later run.",
        }
        artifact = self._create(findings=[finding])
        artifact["audit_status"] = "clean"
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_bound_quality_finding_is_deliverable_as_issues_found(self) -> None:
        from independent_audit import validate_auditor_artifact  # noqa: E402

        finding = {
            "finding_id": "F-QUALITY",
            "requirement_ids": ["REQ-VISUAL-QUALITY"],
            "rule_ids": [],
            "slide_ids": ["S1"],
            "owner_layer": "supervisor",
            "severity": "moderate",
            "statement": "The synthetic fixture does not establish native font acceptance.",
            "expected": "Native acceptance is either executed or clearly deferred.",
            "actual": "Only synthetic pixels were inspected.",
            "impact": "Native pixel compatibility remains unverified.",
            "evidence_refs": [_evidence_ref(self.render)],
            "recommended_change": "Run the selected native renderer in a later bounded run.",
        }
        artifact = self._create(findings=[finding])
        validate_auditor_artifact(artifact)
        self.assertEqual(artifact["audit_status"], "issues-found")

    def test_audit_after_final_pptx_mutation_is_stale(self) -> None:
        from independent_audit import IndependentAuditError, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        self.pptx.write_bytes(self.pptx.read_bytes() + b"mutated-after-audit")
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_task_request_hash_is_raw_bytes_and_wrong_task_is_rejected(self) -> None:
        from independent_audit import IndependentAuditError, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        other_task = write_json(self.work / "other-task.json", {"request": "Different task"})
        artifact["task_request"] = file_ref(other_task)
        artifact["task_request_sha256"] = sha256_file(other_task)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact, expected_task_request_sha256=self.task_sha)

    def test_nonempty_text_file_cannot_masquerade_as_final_pptx(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        fake = self.work / "fake.pptx"
        fake.write_text("this is not an OOXML package", encoding="utf-8")
        artifact["final_pptx"] = file_ref(fake)
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_invalid_json_source_cannot_masquerade_as_audited_package(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        fake = self.work / "invalid-package.json"
        fake.write_text("not JSON", encoding="utf-8")
        artifact["source_records"][0].update(file_ref(fake))
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_arbitrary_file_cannot_masquerade_as_render_evidence(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        fake = self.work / "random-render.png"
        fake.write_text("not a pixel image and not a native render", encoding="utf-8")
        artifact["render_evidence"] = [{"kind": "native-powerpoint-pass", **file_ref(fake)}]
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_synthetic_render_cannot_be_claimed_as_native_acceptance(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create()
        artifact["render_evidence"][0]["kind"] = "native-powerpoint-pass"
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_synthetic_pixel_cannot_satisfy_explicit_native_render_requirement(self) -> None:
        from acceptance_contract import acceptance_contract_digest  # noqa: E402
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        acceptance = _acceptance_contract()
        acceptance["requirements"].append(
            {
                "requirement_id": "REQ-NATIVE-PIXELS",
                "category": "compatibility",
                "statement": "Execute a native renderer for final pixel acceptance.",
                "owner_stage": "output",
                "verification_method": "native-render-artifact",
                "blocking": False,
                "classification": "soft",
            }
        )
        acceptance["contract_sha256"] = acceptance_contract_digest(acceptance)
        self.acceptance.write_bytes(json_bytes(acceptance))
        coverage = self._coverage()
        coverage["soft_requirement_ids"] = ["REQ-NATIVE-PIXELS", "REQ-VISUAL-QUALITY"]
        coverage["requirements"].append(
            {
                "requirement_id": "REQ-NATIVE-PIXELS",
                "classification": "soft",
                "status": "pass",
                "evidence_refs": ["render-01.png"],
                "observation": "The declared native-render-artifact check is marked pass.",
            }
        )
        artifact = self._create(coverage=coverage)
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_partial_render_coverage_cannot_be_reported_as_clean(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create(coverage=self._coverage(render_status="partial"))
        artifact["audit_status"] = "clean"
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)

    def test_separate_process_identity_string_alone_does_not_prove_native_independence(self) -> None:
        from independent_audit import IndependentAuditError, canonical_record_sha256, validate_auditor_artifact  # noqa: E402

        artifact = self._create(
            context={
                "execution_mode": "separate-process",
                "context_id": "auditor-process-001",
                "model_identity_disclosure": "provided-by-host",
                "limitations": [],
            }
        )
        artifact["record_sha256"] = canonical_record_sha256(artifact)
        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(artifact)


class FontAuditAdversarialTests(unittest.TestCase):
    """Ensure unresolved font inheritance is honest instead of false green."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="calibrated-audit-font-")
        self.work = Path(self.temp.name)
        self.config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        self.config["theme"]["typography"]["primary_fonts"] = ["Synthetic Approved Font"]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _config(self, path: Path) -> Path:
        output = self.work / f"{path.stem}-config.json"
        return write_json(output, self.config)

    def test_theme_font_alone_does_not_prove_unresolved_cjk_run(self) -> None:
        from audit_ppt_font_names import audit_font_names  # noqa: E402

        pptx = build_minimal_pptx(self.work / "theme-only.pptx", run_font=None, east_asian_font=None)
        patch_theme_east_asian_font(pptx, "Synthetic Approved Font")
        result = audit_font_names(pptx, self.config)
        # A correct theme does not prove which effective font a complex run
        # inherits.  The validator may report this as unknown/deferred, but it
        # must not claim a complete conforming pass.
        self.assertFalse(result.get("ok") is True, result)
        self.assertTrue(
            result.get("status") in {"deferred", "unknown", "incomplete-evidence"}
            or result.get("unresolved_cjk_chars", 0) > 0
            or result.get("inherited_cjk_chars", 0) > 0 and result.get("conforming_cjk_chars", 0) < result.get("visible_cjk_chars", 0),
            result,
        )

    def test_latin_only_run_does_not_count_as_east_asian_font_acceptance(self) -> None:
        from audit_ppt_font_names import audit_font_names  # noqa: E402

        pptx = build_minimal_pptx(
            self.work / "latin-only.pptx",
            run_font="Synthetic Approved Font",
            east_asian_font=None,
        )
        result = audit_font_names(pptx, self.config)
        self.assertFalse(result.get("ok") is True, result)
        self.assertTrue(
            result.get("status") in {"deferred", "unknown", "incomplete-evidence"}
            or result.get("unresolved_cjk_chars", 0) > 0
            or result.get("inherited_cjk_chars", 0) > 0,
            result,
        )


class CalibrationChainAdversarialTests(unittest.TestCase):
    """Exercise real stage/calibration bindings with task-byte hashes."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="calibrated-audit-calibration-")
        self.work = Path(self.temp.name)
        self.task = write_json(self.work / "raw-user-request.json", {"request": "Build the exact requested deck.", "revision": 1})
        self.acceptance = write_json(self.work / "acceptance-rules.json", _acceptance_contract(include_soft=False))
        self.shared_rules = write_json(
            self.work / "shared-rules.json",
            {
                "fixed_commitments": [
                    {
                        "rule_id": "SHARED-READ-RAW",
                        "statement": "Keep the raw request byte-bound.",
                        "classification": "hard",
                    }
                ],
                "explicit_changes": [],
            },
        )
        self.challenge = self._issue(self.task)
        self.run_id = self.challenge["run_id"]
        self.task_sha = self.challenge["task_request_sha256"]

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _issue(task: Path) -> dict[str, object]:
        from packages.runtime.preflight import issue_run_challenge  # noqa: E402

        return issue_run_challenge(task.read_bytes(), task_root=task.parent)

    def _artifact(self, name: str, value: object) -> Path:
        return write_json(self.work / name, value)

    def _draft(self, stage: str) -> dict[str, object]:
        return {
            "summary": f"Synthetic {stage} work with an explicit calibrated handoff.",
            "decisions": [f"Continue the {stage} stage."],
            "checks": [{"name": "source inspected", "status": "pass", "evidence_roles": ["artifact"]}],
            "open_issues": [],
        }

    def _stage_record(self, stage: str, previous: dict[str, object] | None, name: str) -> tuple[dict[str, object], Path]:
        from packages.validators.stage_work_records import create_record  # noqa: E402

        artifact = self._artifact(name, {"stage": stage, "synthetic": True})
        record = create_record(
            stage,
            self._draft(stage),
            self.challenge,
            {"artifact": artifact},
            previous,
            acceptance_contract=self.acceptance,
        )
        path = self.work / f"{stage}-record.json"
        path.write_bytes(json_bytes(record))
        return record, path

    def _calibration(
        self,
        step: str,
        source_path: Path,
        output_name: str,
        previous: dict[str, object] | None = None,
        findings: list[dict[str, object]] | None = None,
    ) -> tuple[dict[str, object], Path]:
        from packages.validators.stage_work_records import create_calibration_record  # noqa: E402

        output = self.work / output_name
        value = create_calibration_record(
            step,
            source_path,
            self.acceptance,
            self.shared_rules,
            findings or [],
            self.challenge,
            # The black-box chain uses the returned immutable object and
            # writes the exact bytes itself.  A separate test covers the
            # convenience writer path, which must not be allowed to fail with
            # an implementation NameError.
            output=None,
            previous_calibration=previous,
            recorded_at="2026-09-14T01:22:00Z",
        )
        output.write_bytes(json_bytes(value))
        return value, output

    def _build_calibration_chain(self) -> tuple[list[dict[str, object]], list[Path]]:
        """Materialize the three real calibration files used by report tests."""

        from packages.validators.stage_work_records import create_calibration_binding  # noqa: E402

        logic, logic_path = self._stage_record("logic", None, "logic-package.json")
        calibration_1, calibration_1_path = self._calibration("logic-to-copy", logic_path, "calibration-logic-copy.json")
        binding_1 = create_calibration_binding(calibration_1_path, [])
        copy_record, copy_path = self._stage_record("copy", logic, "copy-package.json")
        copy_record["calibration_bindings"] = [binding_1]
        copy_record["record_sha256"] = importlib.import_module("packages.validators.stage_work_records").canonical_record_sha256(copy_record)
        copy_path.write_bytes(json_bytes(copy_record))

        calibration_2, calibration_2_path = self._calibration("copy-to-art-direction", copy_path, "calibration-copy-ad.json", calibration_1)
        binding_2 = create_calibration_binding(calibration_2_path, [])
        art_record, art_path = self._stage_record("art-direction", copy_record, "art-plan.json")
        art_record["calibration_bindings"] = [binding_2]
        art_record["record_sha256"] = importlib.import_module("packages.validators.stage_work_records").canonical_record_sha256(art_record)
        art_path.write_bytes(json_bytes(art_record))

        calibration_3, calibration_3_path = self._calibration("art-direction-to-output", art_path, "calibration-ad-output.json", calibration_2)
        return [calibration_1, calibration_2, calibration_3], [calibration_1_path, calibration_2_path, calibration_3_path]

    def test_three_calibration_receipts_form_a_real_chain(self) -> None:
        from packages.validators.stage_work_records import (  # noqa: E402
            create_calibration_binding,
            validate_calibration_chain,
        )

        logic, logic_path = self._stage_record("logic", None, "logic-package.json")
        calibration_1, calibration_1_path = self._calibration("logic-to-copy", logic_path, "calibration-logic-copy.json")
        binding_1 = create_calibration_binding(calibration_1_path, [])
        copy_record, copy_path = self._stage_record("copy", logic, "copy-package.json")
        copy_record["calibration_bindings"] = [binding_1]
        copy_record["record_sha256"] = importlib.import_module("packages.validators.stage_work_records").canonical_record_sha256(copy_record)
        copy_path.write_bytes(json_bytes(copy_record))

        calibration_2, calibration_2_path = self._calibration("copy-to-art-direction", copy_path, "calibration-copy-ad.json", calibration_1)
        binding_2 = create_calibration_binding(calibration_2_path, [])
        art_record, art_path = self._stage_record("art-direction", copy_record, "art-plan.json")
        art_record["calibration_bindings"] = [binding_2]
        art_record["record_sha256"] = importlib.import_module("packages.validators.stage_work_records").canonical_record_sha256(art_record)
        art_path.write_bytes(json_bytes(art_record))

        calibration_3, calibration_3_path = self._calibration("art-direction-to-output", art_path, "calibration-ad-output.json", calibration_2)
        binding_3 = create_calibration_binding(calibration_3_path, [])
        output_record, output_path = self._stage_record("output", art_record, "final-output.json")
        output_record["calibration_bindings"] = [binding_3]
        output_record["record_sha256"] = importlib.import_module("packages.validators.stage_work_records").canonical_record_sha256(output_record)
        output_path.write_bytes(json_bytes(output_record))

        validate_calibration_chain(
            [calibration_1, calibration_2, calibration_3],
            self.run_id,
            self.task_sha,
        )
        self.assertEqual(calibration_1["source_records"][0]["sha256"], sha256_file(logic_path))
        self.assertEqual(calibration_3["source_stage"], "art-direction")

    def _build_issues_auditor(self, pptx: Path, render: Path) -> tuple[dict[str, object], Path]:
        from independent_audit import create_auditor_artifact  # noqa: E402

        # The Auditor reads the same raw acceptance and Supervisor rule files,
        # while each source record is a real JSON stage artifact.
        coverage = {
            "hard_requirement_ids": ["REQ-RAW-USER"],
            "soft_requirement_ids": [],
            "requirements": [
                {
                    "requirement_id": "REQ-RAW-USER",
                    "classification": "hard",
                    "status": "pass",
                    "evidence_refs": [_evidence_ref(self.task)],
                    "observation": "The independent Auditor opened the raw task bytes.",
                }
            ],
            "rules": [
                {
                    "rule_id": "SHARED-READ-RAW",
                    "source": "fixed_commitment",
                    "status": "pass",
                    "evidence_refs": [_evidence_ref(self.shared_rules)],
                    "observation": "The shared rule remains byte-bound.",
                }
            ],
            "render_status": "complete",
        }
        finding = {
            "finding_id": "AUD-F-QUALITY",
            "requirement_ids": [],
            "rule_ids": ["SHARED-READ-RAW"],
            "slide_ids": ["S1"],
            "owner_layer": "supervisor",
            "severity": "moderate",
            "statement": "Only synthetic pixels were inspected.",
            "expected": "Native acceptance is executed or clearly deferred.",
            "actual": "The fixture declares native rendering was not executed.",
            "impact": "Native compatibility remains unverified.",
            "evidence_refs": [_evidence_ref(render)],
            "recommended_change": "Run a selected native renderer in a later bounded run.",
        }
        audit_path = self.work / "auditor.json"
        artifact = create_auditor_artifact(
            task_request=self.task,
            acceptance_rules=self.acceptance,
            supervisor_rules=self.shared_rules,
            source_records={
                "package": self.work / "logic-package.json",
                "plan": self.work / "art-plan.json",
                "qa": self.work / "copy-package.json",
                "inventory": self.work / "final-output.json" if (self.work / "final-output.json").is_file() else self.shared_rules,
            },
            final_pptx=pptx,
            render_evidence={"synthetic-pixel-render": render},
            coverage=coverage,
            findings=[finding],
            independent_context={
                "execution_mode": "same-model-new-context",
                "context_id": "independent-auditor-context",
                "model_identity_disclosure": "same-model-possible",
                "limitations": ["Native Office rendering was not executed; the PNG is explicitly synthetic."],
            },
            run_id=self.run_id,
            task_request_sha256=self.task_sha,
            output=audit_path,
            audited_at="2026-09-14T01:30:00Z",
        )
        return artifact, audit_path

    def test_supervisor_cannot_promote_auditor_issues_to_unqualified_release(self) -> None:
        from packages.validators.validate_supervision_report import validate_calibrated_delivery  # noqa: E402

        calibrations, calibration_paths = self._build_calibration_chain()
        pptx = build_minimal_pptx(self.work / "final.pptx")
        render = build_synthetic_pixel_render(self.work / "render.png")
        auditor, auditor_path = self._build_issues_auditor(pptx, render)
        report = {
            "contract_version": "3.5",
            "run_id": self.run_id,
            "task_request_sha256": self.task_sha,
            "run_status": "issues-found",
            "calibration_artifacts": [
                {"step": value["step"], **file_ref(path)} for value, path in zip(calibrations, calibration_paths)
            ],
            "auditor_artifact": file_ref(auditor_path),
            "delivery_pair": {"pptx": {"sha256": sha256_file(pptx)}},
            "supervisor_release": {
                "status": "released-with-limitations",
                "released_at": "2026-09-14T01:31:00Z",
                "auditor_artifact_sha256": sha256_file(auditor_path),
                "pptx_sha256": sha256_file(pptx),
                "evidence": "Release preserves the independent Auditor's finding and deferred native check.",
            },
        }
        self.assertEqual(
            validate_calibrated_delivery({}, report, pptx, self.work / "report.json", evidence_root=self.work),
            [],
        )
        report["supervisor_release"]["status"] = "released"
        errors = validate_calibrated_delivery({}, report, pptx, self.work / "report.json", evidence_root=self.work)
        self.assertTrue(any("limitations" in error or "issues-found" in error for error in errors), errors)

    def test_auditor_release_must_preserve_deferred_status_in_report(self) -> None:
        from packages.validators.validate_supervision_report import validate_calibrated_delivery  # noqa: E402

        calibrations, calibration_paths = self._build_calibration_chain()
        pptx = build_minimal_pptx(self.work / "final.pptx")
        audit_path = self.work / "deferred-auditor.json"
        audit = {
            "contract": "io.clayz.presentation.independent-audit/1.0",
            "audit_status": "incomplete-evidence",
        }
        audit_path.write_bytes(json_bytes(audit))
        report = {
            "contract_version": "3.5",
            "run_id": self.run_id,
            "task_request_sha256": self.task_sha,
            "run_status": "issues-found",
            "calibration_artifacts": [
                {"step": value["step"], **file_ref(path)} for value, path in zip(calibrations, calibration_paths)
            ],
            "auditor_artifact": file_ref(audit_path),
            "delivery_pair": {"pptx": {"sha256": sha256_file(pptx)}},
            "supervisor_release": {
                "status": "released-with-limitations",
                "released_at": "2026-09-14T01:31:00Z",
                "auditor_artifact_sha256": sha256_file(audit_path),
                "pptx_sha256": sha256_file(pptx),
                "evidence": "Deferred audit evidence remains visible.",
            },
        }
        errors = validate_calibrated_delivery({}, report, pptx, self.work / "report.json", evidence_root=self.work)
        self.assertTrue(any("incomplete-evidence" in error for error in errors), errors)

    def test_mutated_upstream_record_invalidates_downstream_calibration(self) -> None:
        from packages.validators.stage_work_records import StageWorkRecordError, validate_calibration_record  # noqa: E402

        _, logic_path = self._stage_record("logic", None, "logic-package.json")
        calibration, _ = self._calibration("logic-to-copy", logic_path, "calibration.json")
        logic_path.write_bytes(logic_path.read_bytes() + b"\n")
        with self.assertRaises(StageWorkRecordError):
            validate_calibration_record(calibration)

    def test_wrong_task_bytes_cannot_reuse_a_valid_upstream_record(self) -> None:
        from packages.validators.stage_work_records import StageWorkRecordError, create_calibration_record  # noqa: E402

        _, logic_path = self._stage_record("logic", None, "logic-package.json")
        other_task = self._artifact("different-task.json", {"request": "Different original user requirements"})
        other_challenge = self._issue(other_task)
        with self.assertRaises(StageWorkRecordError):
            create_calibration_record(
                "logic-to-copy",
                logic_path,
                self.acceptance,
                self.shared_rules,
                [],
                other_challenge,
            )

    def test_calibration_writer_path_is_usable(self) -> None:
        from packages.validators.stage_work_records import create_calibration_record  # noqa: E402

        _, logic_path = self._stage_record("logic", None, "logic-package.json")
        output = self.work / "calibration-writer.json"
        create_calibration_record(
            "logic-to-copy",
            logic_path,
            self.acceptance,
            self.shared_rules,
            [],
            self.challenge,
            output=output,
        )
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)

    def test_downstream_must_explicitly_absorb_each_calibration_finding(self) -> None:
        from packages.validators.stage_work_records import (  # noqa: E402
            StageWorkRecordError,
            create_calibration_binding,
            create_calibration_record,
            create_record,
        )

        logic, logic_path = self._stage_record("logic", None, "logic-package.json")
        finding = {
            "finding_id": "CAL-F-01",
            "requirement_ids": ["REQ-RAW-USER"],
            "statement": "Preserve the raw request binding.",
            "recommendation": "Carry the exact task bytes into Copy.",
            "severity": "major",
            "blocking": False,
        }
        calibration, calibration_path = self._calibration(
            "logic-to-copy", logic_path, "calibration-with-finding.json", findings=[finding]
        )
        with self.assertRaises(StageWorkRecordError):
            create_calibration_binding(calibration_path, [])
        binding = create_calibration_binding(
            calibration_path,
            [{"finding_id": "CAL-F-01", "disposition": "declined", "reason": "It conflicts with the approved copy scope."}],
        )
        copy_record = create_record(
            "copy",
            self._draft("copy"),
            self.challenge,
            {"artifact": self._artifact("copy-package.json", {"stage": "copy"})},
            logic,
            calibration_bindings=[binding],
            acceptance_contract=self.acceptance,
        )
        self.assertEqual(copy_record["calibration_bindings"][0]["finding_dispositions"][0]["disposition"], "declined")

    def test_declined_calibration_finding_requires_a_nonempty_reason(self) -> None:
        from packages.validators.stage_work_records import StageWorkRecordError, create_calibration_binding  # noqa: E402

        _, logic_path = self._stage_record("logic", None, "logic-package.json")
        _, calibration_path = self._calibration(
            "logic-to-copy",
            logic_path,
            "calibration-with-finding.json",
            findings=[
                {
                    "finding_id": "CAL-F-01",
                    "requirement_ids": ["REQ-RAW-USER"],
                    "statement": "Preserve the raw request binding.",
                    "recommendation": "Carry the exact task bytes into Copy.",
                    "severity": "major",
                    "blocking": False,
                }
            ],
        )
        with self.assertRaises(StageWorkRecordError):
            create_calibration_binding(
                calibration_path,
                [{"finding_id": "CAL-F-01", "disposition": "declined", "reason": ""}],
            )

    def test_calibrated_records_without_absorption_are_not_release_ready(self) -> None:
        from packages.validators.stage_work_records import StageWorkRecordError, validate_records  # noqa: E402

        logic, _ = self._stage_record("logic", None, "logic-package.json")
        copy_record, _ = self._stage_record("copy", logic, "copy-package.json")
        art_record, _ = self._stage_record("art-direction", copy_record, "art-plan.json")
        output_record, _ = self._stage_record("output", art_record, "final-output.json")
        supervisor_record, _ = self._stage_record("supervisor", output_record, "supervisor.json")
        with self.assertRaises(StageWorkRecordError):
            validate_records(
                [logic, copy_record, art_record, output_record, supervisor_record],
                self.run_id,
                self.task_sha,
            )


class RealCliReleaseTests(unittest.TestCase):
    """Run record-calibration, record-audit, and publish through real CLIs."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="calibrated-audit-cli-")
        self.work = Path(self.temp.name)
        self.publisher = ROOT / "scripts" / "publish_supervised_pair.py"
        # Leave enough wall-clock room for the subprocess CLI calls while
        # keeping the challenge inside its fresh 24-hour validity window.
        self.base = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
        self.task = write_json(
            self.work / "raw-user-request.json",
            {
                "request": "Create the requested decision presentation and disclose any unverified render checks.",
                "revision": 1,
            },
        )
        self.package = json.loads((ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8"))
        self.plan = json.loads((ROOT / "tests" / "fixtures" / "synthetic-art-direction-plan.json").read_text(encoding="utf-8"))
        self._upgrade_acceptance()
        self._refresh_inventory_time()
        self.package_path = write_json(self.work / "ppt-design-package.json", self.package)
        self.plan_path = write_json(self.work / "ppt-art-direction-plan.json", self.plan)
        self.acceptance_path = write_json(self.work / "acceptance-rules.json", self.package["acceptance_contract"])
        self.supervisor_rules_path = write_json(
            self.work / "supervisor-rules.json",
            {
                "fixed_commitments": [
                    {
                        "rule_id": "RULE-RAW-REQUEST",
                        "statement": "The Auditor reads the exact raw user request.",
                        "classification": "hard",
                    }
                ],
                "explicit_changes": [],
            },
        )
        self.qa = {
            "contract_version": "4.0",
            "package_id": self.package["package_id"],
            "package_version": self.package["version"],
            "acceptance_contract": self.package["acceptance_contract"],
        }
        self.qa_path = write_json(self.work / "ppt-output-qa.json", self.qa)
        self.inventory_path = write_json(self.work / "inventory.json", {"inventory": "synthetic object inventory"})
        self.resource_inventory_path = write_json(self.work / "ppt-resource-inventory.json", self.package["resource_inventory"])
        copy_slide = self.package["copy_layer"]["slides"][0]
        title = next(unit["text"] for unit in copy_slide["copy_units"] if unit["role"] == "title")
        body = next(unit["text"] for unit in copy_slide["copy_units"] if unit["role"] == "storyline")
        self.pptx = build_minimal_pptx(self.work / "final.pptx", title_text=title, body_text=body)
        self.render_root = self.work / "render"
        self.render_root.mkdir()
        self.render = build_synthetic_pixel_render(self.render_root / "slide-01.png", label="synthetic pixel fixture")
        self.config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        self.config["renderer"]["required_capabilities"] = ["editable-text", "render-preview"]
        self.config_path = write_json(self.work / "config.json", self.config)
        self.challenge = self._write_challenge()
        self.preflight_path = self._write_preflight()
        self.empty_findings_path = write_json(self.work / "empty-findings.json", [])
        self.dispositions_path = write_json(self.work / "empty-dispositions.json", [])

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _canonical_hash(value: object) -> str:
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _upgrade_acceptance(self) -> None:
        from packages.validators.acceptance_contract import acceptance_contract_digest  # noqa: E402

        for requirement in self.package["acceptance_contract"]["requirements"]:
            requirement["classification"] = "hard" if requirement.get("blocking") is True else "soft"
        self.package["acceptance_contract"]["contract_sha256"] = acceptance_contract_digest(self.package["acceptance_contract"])
        self.plan["acceptance_contract"] = copy.deepcopy(self.package["acceptance_contract"])

    def _refresh_inventory_time(self) -> None:
        from packages.validators.resource_inventory import finalize_resource_inventory  # noqa: E402

        inventory = copy.deepcopy(self.package["resource_inventory"])
        inventory["created_at"] = self._iso(self.base)
        inventory["user_brief"]["presented_at"] = self._iso(self.base + timedelta(seconds=2))
        self.package["resource_inventory"] = finalize_resource_inventory(inventory)
        from packages.validators.resource_inventory import resource_inventory_signature  # noqa: E402

        self.plan["resource_inventory_lock"] = resource_inventory_signature(self.package["resource_inventory"])

    def _write_challenge(self) -> Path:
        from packages.runtime.preflight import issue_run_challenge  # noqa: E402

        challenge = issue_run_challenge(self.task.read_bytes(), task_root=self.work, now=self.base)
        return write_json(self.work / "challenge.json", challenge)

    def _write_preflight(self) -> Path:
        challenge = json.loads(self.challenge.read_text(encoding="utf-8"))
        challenge_sha = sha256_file(self.challenge)
        config_sha = sha256_file(self.config_path)
        binding = {
            **challenge,
            "challenge_sha256": challenge_sha,
            "binding_source": "script-issued-challenge",
            "issuance_receipt": str(self.work / ".clayz-run-challenges" / f"{challenge['run_id']}.issued.json"),
            "issuance_receipt_sha256": "a" * 64,
            "consumption_receipt": str(self.work / ".clayz-run-challenges" / "consumed" / f"{challenge_sha}.json"),
            "consumption_receipt_sha256": "b" * 64,
        }
        preflight = {
            "contract": "io.clayz.presentation.runtime-preflight/1.3",
            "scan_id": "runtime-calibrated-cli-smoke",
            "run_binding": binding,
            "config_binding": {"path": str(self.config_path.resolve()), "sha256": config_sha, "source": "public-default"},
            "component_version_gate": {
                "status": "installed",
                "all_components_current": True,
                "sha256": "c" * 64,
                "manifest_sha256": "d" * 64,
                "local_release_version": self.config["identity"]["version"],
                "latest_release_version": None,
            },
            "required_capabilities": ["editable-text", "render-preview"],
            "dependencies": {
                "host_tools": {
                    "available": False,
                    "observation": {
                        "run_id": challenge["run_id"],
                        "task_request_sha256": challenge["task_request_sha256"],
                        "challenge_sha256": challenge_sha,
                        "verification_status": "challenge-bound-host-declaration",
                        "assurance_level": "host-declared-unverified",
                        "route_eligible": False,
                    },
                }
            },
            "selected_route": {
                "route_id": "python-pptx+synthetic-test-render",
                "authoring_backend": "python-pptx",
                "render_backend": "synthetic-test-render",
                "available": False,
                "attemptable": False,
                "assurance_level": "insufficient",
                "missing_capabilities": [],
            },
            "target_application_checks": [
                {"application": app, "capability": f"{app}-reopen-render", "availability": "unavailable"}
                for app in ("powerpoint", "wps", "libreoffice")
            ],
        }
        return write_json(self.work / "runtime-preflight.json", preflight)

    def _ref(self, path: Path, *, fragment: str | None = None) -> str:
        suffix = f"#{fragment}" if fragment else ""
        return f"{path.name}{suffix} sha256={sha256_file(path)}"

    def _run_cli(self, *args: object, expected: int = 0) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT), env.get("PYTHONPATH", "")]))
        result = subprocess.run(
            [str(PYTHON), "-B", str(self.publisher), *[str(arg) for arg in args]],
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if expected == 0:
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def _run_target_script(self, script: Path, *args: object, expected: int = 0) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT), env.get("PYTHONPATH", "")]))
        result = subprocess.run(
            [str(PYTHON), "-B", str(script), *[str(arg) for arg in args]],
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if expected == 0:
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def _stage_draft(self, stage: str, roles: list[str]) -> Path:
        return write_json(
            self.work / f"{stage}-draft.json",
            {
                "summary": f"Recorded real CLI work for {stage} with task-local evidence.",
                "decisions": [f"Continue the {stage} stage."],
                "checks": [{"name": "source inspected", "status": "pass", "evidence_roles": roles}],
                "open_issues": [],
            },
        )

    def _record_stages_and_calibrations(self) -> dict[str, Path]:
        stages: dict[str, Path] = {}
        draft = self._stage_draft("logic", ["package"])
        logic_path = self.work / "logic-record.json"
        self._run_cli(
            "record-stage", "--stage", "logic", "--draft", draft, "--challenge", self.challenge,
            "--artifact", f"package={self.package_path}", "--acceptance-contract", self.acceptance_path, "--output", logic_path,
        )
        stages["logic"] = logic_path
        cal1 = self.work / "calibration-logic-copy.json"
        self._run_cli(
            "record-calibration", "--step", "logic-to-copy", "--source-record", logic_path,
            "--acceptance-contract", self.acceptance_path, "--shared-rules", self.supervisor_rules_path,
            "--findings", self.empty_findings_path, "--challenge", self.challenge, "--output", cal1,
        )
        stages["calibration_logic_copy"] = cal1
        draft = self._stage_draft("copy", ["package"])
        copy_path = self.work / "copy-record.json"
        self._run_cli(
            "record-stage", "--stage", "copy", "--draft", draft, "--challenge", self.challenge,
            "--previous-record", logic_path, "--artifact", f"package={self.package_path}",
            "--calibration", cal1, "--calibration-dispositions", self.dispositions_path,
            "--acceptance-contract", self.acceptance_path, "--output", copy_path,
        )
        stages["copy"] = copy_path
        cal2 = self.work / "calibration-copy-art-direction.json"
        self._run_cli(
            "record-calibration", "--step", "copy-to-art-direction", "--source-record", copy_path,
            "--acceptance-contract", self.acceptance_path, "--shared-rules", self.supervisor_rules_path,
            "--findings", self.empty_findings_path, "--challenge", self.challenge, "--previous-calibration", cal1, "--output", cal2,
        )
        stages["calibration_copy_art_direction"] = cal2
        draft = self._stage_draft("art-direction", ["plan"])
        art_path = self.work / "art-direction-record.json"
        self._run_cli(
            "record-stage", "--stage", "art-direction", "--draft", draft, "--challenge", self.challenge,
            "--previous-record", copy_path, "--artifact", f"plan={self.plan_path}",
            "--calibration", cal2, "--calibration-dispositions", self.dispositions_path,
            "--acceptance-contract", self.acceptance_path, "--output", art_path,
        )
        stages["art-direction"] = art_path
        cal3 = self.work / "calibration-art-direction-output.json"
        self._run_cli(
            "record-calibration", "--step", "art-direction-to-output", "--source-record", art_path,
            "--acceptance-contract", self.acceptance_path, "--shared-rules", self.supervisor_rules_path,
            "--findings", self.empty_findings_path, "--challenge", self.challenge, "--previous-calibration", cal2, "--output", cal3,
        )
        stages["calibration_art_direction_output"] = cal3
        draft = self._stage_draft("output", ["qa", "inventory", "pptx"])
        output_path = self.work / "output-record.json"
        self._run_cli(
            "record-stage", "--stage", "output", "--draft", draft, "--challenge", self.challenge,
            "--previous-record", art_path, "--artifact", f"qa={self.qa_path}", "--artifact", f"inventory={self.inventory_path}",
            "--artifact", f"pptx={self.pptx}", "--calibration", cal3, "--calibration-dispositions", self.dispositions_path,
            "--acceptance-contract", self.acceptance_path, "--output", output_path,
        )
        stages["output"] = output_path
        return stages

    def _write_audit_inputs(self, *, stages: dict[str, Path]) -> Path:
        coverage = {
            "hard_requirement_ids": sorted(
                req["requirement_id"] for req in self.package["acceptance_contract"]["requirements"] if req["classification"] == "hard"
            ),
            "soft_requirement_ids": sorted(
                req["requirement_id"] for req in self.package["acceptance_contract"]["requirements"] if req["classification"] == "soft"
            ),
            "requirements": [
                {
                    "requirement_id": req["requirement_id"],
                    "classification": req["classification"],
                    "status": "pass",
                    "evidence_refs": [self._ref(self.task)],
                    "observation": f"Auditor opened the raw task bytes for {req['requirement_id']}.",
                }
                for req in self.package["acceptance_contract"]["requirements"]
            ],
            "rules": [
                {
                    "rule_id": "RULE-RAW-REQUEST",
                    "source": "fixed_commitment",
                    "status": "pass",
                    "evidence_refs": [self._ref(self.supervisor_rules_path)],
                    "observation": "The shared Supervisor rule is present in the Auditor context.",
                }
            ],
            "render_status": "complete",
        }
        coverage_path = write_json(self.work / "audit-coverage.json", coverage)
        findings = [
            {
                "finding_id": "AUD-F-SYNTHETIC-RENDER",
                "requirement_ids": [],
                "rule_ids": [],
                "slide_ids": ["S01"],
                "owner_layer": "output",
                "severity": "moderate",
                "statement": "The supplied pixels are an explicit synthetic fixture.",
                "expected": "Native render acceptance is executed or deferred honestly.",
                "actual": "Native Office rendering was not executed in this smoke test.",
                "impact": "Native pixel compatibility remains unverified.",
                "evidence_refs": [self._ref(self.render)],
                "recommended_change": "Run the selected native renderer in a later bounded run.",
            }
        ]
        findings_path = write_json(self.work / "audit-findings.json", findings)
        context_path = write_json(
            self.work / "auditor-context.json",
            {
                "execution_mode": "same-model-new-context",
                "context_id": "real-cli-independent-auditor",
                "model_identity_disclosure": "same-model-possible",
                "limitations": ["Native Office render was not executed; the PNG is explicitly synthetic."],
            },
        )
        auditor_path = self.work / "auditor.json"
        source_args = [
            "--source-record", f"package={self.package_path}",
            "--source-record", f"plan={self.plan_path}",
            "--source-record", f"qa={self.qa_path}",
            "--source-record", f"inventory={self.inventory_path}",
        ]
        self._run_cli(
            "record-audit", "--task-request", self.task, "--acceptance-rules", self.acceptance_path,
            "--supervisor-rules", self.supervisor_rules_path, *source_args, "--pptx", self.pptx,
            "--render-evidence", f"synthetic-pixel-render={self.render}", "--coverage", coverage_path,
            "--findings", findings_path, "--independent-context", context_path,
            "--challenge", self.challenge, "--output", auditor_path,
        )
        return auditor_path

    def _build_report(self, *, stages: dict[str, Path], auditor_path: Path) -> Path:
        from packages.validators.resource_inventory import resource_inventory_signature  # noqa: E402

        preflight = json.loads(self.preflight_path.read_text(encoding="utf-8"))
        preflight_hash = sha256_file(self.preflight_path)
        challenge = json.loads(self.challenge.read_text(encoding="utf-8"))
        audit = json.loads(auditor_path.read_text(encoding="utf-8"))
        audit_at = datetime.fromisoformat(audit["audited_at"].replace("Z", "+00:00"))
        brief = self.package["resource_inventory"]["user_brief"]
        inventory_sig = resource_inventory_signature(self.package["resource_inventory"])
        snapshots = {
            "logic": {"brief": self.package["brief"], "logic_layer": self.package["logic_layer"]},
            "copy": self.package["copy_layer"],
            "art_direction": {key: self.plan.get(key) for key in ("communication_contract", "art_direction", "decision_log", "typography_contract", "deck_rhythm", "slides")},
        }
        artifact_paths = {
            "runtime_preflight": self.preflight_path.name,
            "resource_inventory": self.resource_inventory_path.name,
            "package": self.package_path.name,
            "art_direction_plan": self.plan_path.name,
            "pptx": self.pptx.name,
            "render_root": self.render_root.name,
            "output_qa": self.qa_path.name,
            "object_inventory": self.inventory_path.name,
            "build_deviation_log": "build-deviation.json",
            "font_environment_report": "font-environment.json",
            "font_name_audit_report": "font-name.json",
            "cjk_render_report": "cjk-render.json",
            "final_reopen_render_root": self.render_root.name,
            "size_audit_report": "size-audit.json",
        }
        lifecycle_events = [
            {
                "event_id": "CLI-E01",
                "occurred_at": self._iso(self.base),
                "phase": "root",
                "actor_role": "initiator",
                "action": "supervision-started",
                "status": "completed",
                "summary": "Started the calibrated supervision run from the current request.",
                "evidence_refs": [self._ref(self.resource_inventory_path)],
            },
            {
                "event_id": "CLI-E02",
                "occurred_at": self._iso(self.base + timedelta(seconds=1)),
                "phase": "preflight",
                "actor_role": "recorder",
                "action": "runtime-preflight-completed",
                "status": "completed",
                "summary": "Recorded the task-bound runtime preflight and route disposition.",
                "evidence_refs": [self._ref(self.preflight_path)],
            },
            {
                "event_id": "CLI-E03",
                "occurred_at": brief["presented_at"],
                "phase": "preflight",
                "actor_role": "recorder",
                "action": "resource-brief-presented",
                "status": "completed",
                "summary": "Presented the task resource inventory before Logic began.",
                "evidence_refs": [f"{self.resource_inventory_path.name}#user_brief content_sha256={brief['content_sha256']} sha256={sha256_file(self.resource_inventory_path)}"],
            },
            {
                "event_id": "CLI-E04",
                "occurred_at": self._iso(self.base + timedelta(seconds=3)),
                "phase": "logic",
                "actor_role": "recorder",
                "action": "logic-handoff-recorded",
                "status": "completed",
                "summary": "Recorded the Logic handoff and immutable design package.",
                "evidence_refs": [self._ref(self.package_path)],
            },
            {
                "event_id": "CLI-E05",
                "occurred_at": self._iso(self.base + timedelta(seconds=4)),
                "phase": "copy",
                "actor_role": "recorder",
                "action": "copy-handoff-recorded",
                "status": "completed",
                "summary": "Recorded the Copy handoff against the Logic package.",
                "evidence_refs": [self._ref(self.package_path, fragment="copy_layer")],
            },
            {
                "event_id": "CLI-E06",
                "occurred_at": self._iso(self.base + timedelta(seconds=5)),
                "phase": "art-direction",
                "actor_role": "recorder",
                "action": "art-direction-handoff-recorded",
                "status": "completed",
                "summary": "Recorded the Art Direction plan and handoff.",
                "evidence_refs": [self._ref(self.plan_path)],
            },
            {
                "event_id": "CLI-E07",
                "occurred_at": self._iso(self.base + timedelta(seconds=6)),
                "phase": "output",
                "actor_role": "recorder",
                "action": "output-handoff-recorded",
                "status": "completed",
                "summary": "Recorded the final editable PPTX and Output handoff.",
                "evidence_refs": [self._ref(self.pptx), self._ref(self.qa_path)],
            },
            {
                "event_id": "CLI-E08",
                "occurred_at": self._iso(audit_at),
                "phase": "supervision",
                "actor_role": "auditor",
                "action": "final-audit-completed",
                "status": "completed",
                "summary": "The independent Auditor completed the final byte-bound audit.",
                "evidence_refs": [self._ref(auditor_path)],
            },
            {
                "event_id": "CLI-E09",
                "occurred_at": self._iso(audit_at + timedelta(seconds=1)),
                "phase": "delivery",
                "actor_role": "recorder",
                "action": "delivery-pair-locked",
                "status": "completed",
                "summary": "Locked the final PPTX and supervision report as the delivery pair.",
                "evidence_refs": [self._ref(self.pptx), "ppt-supervision-report.json"],
            },
            {
                "event_id": "CLI-E10",
                "occurred_at": self._iso(audit_at + timedelta(seconds=2)),
                "phase": "delivery",
                "actor_role": "initiator",
                "action": "control-returned",
                "status": "returned",
                "summary": "Returned control to the main process or user after release.",
                "evidence_refs": ["ppt-supervision-report.json#control_returned_to"],
            },
        ]
        report: dict[str, object] = {
            # These four fields are the Supervisor's immutable stage draft;
            # assemble-report will add the generated contract, records, and
            # assembly envelope around them.
            "summary": "Prepared the complete calibrated report for the final CLI assembly.",
            "decisions": ["Release with the Auditor limitation preserved."],
            "checks": [{"name": "auditor binding", "status": "pass", "evidence_roles": ["draft", "pptx", "auditor"]}],
            "open_issues": [],
            "contract_version": "3.5",
            "origin_namespace": "io.clayz.presentation",
            "status": "supervised",
            "run_id": challenge["run_id"],
            "task_request_sha256": challenge["task_request_sha256"],
            "package_id": self.package["package_id"],
            "package_version": self.package["version"],
            "art_direction_plan_contract_version": self.plan["contract_version"],
            "output_qa_contract_version": self.qa["contract_version"],
            "supervised_at": self._iso(audit_at + timedelta(seconds=2)),
            "run_status": "incomplete-evidence",
            "artifact_paths": artifact_paths,
            "acceptance_contract": self.package["acceptance_contract"],
            "stage_snapshots": {
                stage: {
                    "artifact_sha256": sha256_file(self.plan_path if stage == "art_direction" else self.package_path),
                    "snapshot_sha256": self._canonical_hash(snapshot),
                    "snapshot": snapshot,
                }
                for stage, snapshot in snapshots.items()
            },
            "requirement_traceability": [
                {
                    "requirement_id": req["requirement_id"],
                    "logic_refs": [self._ref(self.package_path)],
                    "copy_refs": [self._ref(self.package_path)],
                    "art_direction_refs": [self._ref(self.plan_path)],
                    "output_refs": [self._ref(self.qa_path)],
                    "supervisor_refs": ["auditor.json sha256=" + sha256_file(auditor_path)],
                    "status": "pass",
                    "evidence": "The requirement is traced through every governed stage and the independent Auditor.",
                    "earliest_owner": req.get("owner_stage", "logic"),
                }
                for req in self.package["acceptance_contract"]["requirements"]
            ],
            "supervisor_roles": {
                "initiator": {
                    "status": "complete",
                    "summary": "Started the calibrated run from the current task request.",
                    "evidence_refs": [self._ref(self.resource_inventory_path), "ppt-supervision-report.json"],
                },
                "mediator": {
                    "status": "not-needed",
                    "summary": "No Supervisor mediation was needed for this smoke release.",
                    "evidence_refs": ["ppt-supervision-report.json#issues"],
                },
                "recorder": {
                    "status": "complete",
                    "summary": "Recorded the calibrated lifecycle and independent audit binding.",
                    "evidence_refs": ["ppt-supervision-report.json#lifecycle_events"],
                },
                "final_auditor": {
                    "status": "incomplete",
                    "summary": "Supervisor preserves the independent Auditor result without authoring it.",
                    "evidence_refs": [self._ref(auditor_path)],
                },
            },
            "lifecycle_events": lifecycle_events,
            "environment_observation": {
                "preflight": {
                    "artifact": self.preflight_path.name,
                    "scan_id": preflight["scan_id"],
                    "sha256": preflight_hash,
                    "run_id": challenge["run_id"],
                    "task_request_sha256": challenge["task_request_sha256"],
                    "config_sha256": sha256_file(self.config_path),
                    "nonce": challenge["nonce"],
                    "challenge_sha256": preflight["run_binding"]["challenge_sha256"],
                    "task_root_sha256": challenge["task_root_sha256"],
                    "issued_at": challenge["issued_at"],
                    "expires_at": challenge["expires_at"],
                    "issuance_receipt_sha256": preflight["run_binding"]["issuance_receipt_sha256"],
                    "consumption_receipt_sha256": preflight["run_binding"]["consumption_receipt_sha256"],
                },
                "route": {key: preflight["selected_route"][key] for key in ("route_id", "authoring_backend", "render_backend")} | {"status": "blocked"},
                "required_capabilities": {"configured": ["editable-text", "render-preview"], "satisfied": ["editable-text", "render-preview"], "declared_unverified": [], "missing": []},
                "target_applications": [
                    {
                        "application": item["application"],
                        "capability": item["capability"],
                        "availability": item["availability"],
                        "final_status": "deferred",
                        "authoring_gate": False,
                        "evidence_refs": [f"{self.preflight_path.name}#target_application_checks.{item['application']} sha256={preflight_hash}"],
                    }
                    for item in preflight["target_application_checks"]
                ],
                "compatibility_scope": "none",
                "attribution_summary": "Native target applications were unavailable; this release preserves the deferred status.",
            },
            "delivery_pair": {
                "status": "ready",
                "required_artifacts": ["pptx", "supervision-report"],
                "pptx": {"path": self.pptx.name, "sha256": sha256_file(self.pptx)},
                "supervision_report": {"path": "ppt-supervision-report.json"},
                "delivery_manifest": {"path": "delivery-manifest.json"},
                "publisher": "scripts/publish_supervised_pair.py",
                "evidence": "The final PPTX and supervision report are locked as one user handoff.",
            },
            "control_returned_to": "main-process-or-user",
            "calibration_artifacts": [
                {"step": json.loads(path.read_text(encoding="utf-8"))["step"], **file_ref(path)}
                for path in (stages["calibration_logic_copy"], stages["calibration_copy_art_direction"], stages["calibration_art_direction_output"])
            ],
            "auditor_artifact": file_ref(auditor_path),
            "supervisor_release": {
                "status": "released-with-limitations",
                "released_at": self._iso(audit_at + timedelta(seconds=3)),
                "auditor_artifact_sha256": sha256_file(auditor_path),
                "pptx_sha256": sha256_file(self.pptx),
                "evidence": "The release preserves the Auditor finding and the unexecuted native-render limitation.",
            },
            "workflow_contract": "io.clayz.presentation.calibrated-audit/1.0",
        }
        report_path = self.work / "supervisor-draft.json"
        write_json(report_path, report)
        return report_path

    def _record_supervisor(self, stages: dict[str, Path], draft_path: Path, auditor_path: Path) -> Path:
        supervisor_path = self.work / "supervisor-record.json"
        self._run_cli(
            "record-stage", "--stage", "supervisor", "--draft", draft_path, "--challenge", self.challenge,
            "--previous-record", stages["output"], "--artifact", f"draft={draft_path}",
            "--artifact", f"pptx={self.pptx}", "--artifact", f"auditor={auditor_path}",
            "--acceptance-contract", self.acceptance_path, "--output", supervisor_path,
        )
        stages["supervisor"] = supervisor_path
        return supervisor_path

    def _assemble_report(self, stages: dict[str, Path], draft_path: Path, auditor_path: Path) -> Path:
        report_path = self.work / "ppt-supervision-report.json"
        records = [stages[name] for name in ("logic", "copy", "art-direction", "output", "supervisor")]
        args: list[object] = ["assemble-report"]
        for record in records:
            args.extend(("--record", record))
        args.extend(
            (
                "--draft", draft_path,
                "--package", self.package_path,
                "--plan", self.plan_path,
                "--qa", self.qa_path,
                "--inventory", self.inventory_path,
                "--pptx", self.pptx,
                "--runtime-preflight", self.preflight_path,
                "--config", self.config_path,
                "--calibration-logic-copy", stages["calibration_logic_copy"],
                "--calibration-copy-art-direction", stages["calibration_copy_art_direction"],
                "--calibration-art-direction-output", stages["calibration_art_direction_output"],
                "--auditor", auditor_path,
                "--task-request", self.task,
                "--acceptance-contract", self.acceptance_path,
                "--supervisor-rules", self.supervisor_rules_path,
                "--render-root", self.render_root,
                "--output", report_path,
            )
        )
        self._run_cli(*args)
        self.assertTrue(report_path.is_file())
        return report_path

    def test_real_cli_produces_pptx_report_and_manifest_with_honest_limitations(self) -> None:
        stages = self._record_stages_and_calibrations()
        auditor_path = self._write_audit_inputs(stages=stages)
        draft_path = self._build_report(stages=stages, auditor_path=auditor_path)
        self._record_supervisor(stages, draft_path, auditor_path)
        report_path = self._assemble_report(stages, draft_path, auditor_path)
        output_dir = self.work / "published"
        result = self._run_cli(
            self.package_path, self.plan_path, self.qa_path, self.inventory_path, report_path,
            "--pptx", self.pptx, "--runtime-preflight", self.preflight_path, "--config", self.config_path,
            "--render-root", self.render_root, "--output-dir", output_dir,
        )
        manifest = json.loads((output_dir / "delivery-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual({path.name for path in output_dir.iterdir()}, {"final.pptx", "ppt-supervision-report.json", "work-report.md", "delivery-manifest.json"})
        self.assertEqual(manifest["validation"]["validated"], True)
        delivered_report = json.loads((output_dir / "ppt-supervision-report.json").read_text(encoding="utf-8"))
        self.assertEqual(delivered_report["supervisor_release"]["status"], "released-with-limitations")
        self.assertEqual(delivered_report["run_status"], "incomplete-evidence")
        self.assertIn("independent Auditor", delivered_report["supervisor_roles"]["final_auditor"]["summary"])
        # A user may copy the three-file delivery directory.  The report must
        # remain useful there even if the task-local Auditor source path is no
        # longer available, so retain the finding and its limitation in the
        # final JSON itself.
        moved = self.work / "moved-delivery"
        shutil.copytree(output_dir, moved)
        moved_report = json.loads((moved / "ppt-supervision-report.json").read_text(encoding="utf-8"))
        embedded_text = json.dumps(moved_report, ensure_ascii=False)
        self.assertIn("AUD-F-SYNTHETIC-RENDER", embedded_text)
        self.assertIn("Native Office render was not executed", embedded_text)

    def _assemble_calibrated_issue_case(self, *, omit_lifecycle_events: bool) -> Path:
        stages = self._record_stages_and_calibrations()
        auditor_path = self._write_audit_inputs(stages=stages)
        draft_path = self._build_report(stages=stages, auditor_path=auditor_path)
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        draft["issues"] = [{
            "issue_id": "AUD-F-SYNTHETIC-RENDER",
            "finding_code": "AUD-F-SYNTHETIC-RENDER",
            "slide_id": "S01",
            "severity": "moderate",
            "owner_layer": "output-qa",
            "confidence": "medium",
            "failed_checks": ["target_app_compatibility"],
            "source_artifacts": [self._ref(auditor_path), self._ref(self.render)],
            "evidence": "The independent Auditor records uncertain native render coverage for S01.",
            "expected": "Native Office rendering is complete or its limitation is retained explicitly.",
            "actual": "Native Office rendering was not executed; the compatibility status is uncertain.",
            "impact": "Native pixel compatibility remains unverified for this synthetic fixture.",
            "recommended_change": "Run the native renderer and inspect every page before quality sign-off.",
            "regression_rule": "Never publish incomplete native render coverage as a clean quality result.",
        }]
        if omit_lifecycle_events:
            draft.pop("lifecycle_events")
        else:
            draft["lifecycle_events"] = []
        write_json(draft_path, draft)
        self._record_supervisor(stages, draft_path, auditor_path)
        return self._assemble_report(stages, draft_path, auditor_path)

    def _assert_calibrated_issue_delivery(self, report_path: Path) -> None:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertTrue(report.get("issues"), "the calibrated fixture must retain its audit issue")
        self.assertEqual(report["issues"][0]["issue_id"], "AUD-F-SYNTHETIC-RENDER")
        self.assertEqual(report["run_status"], "incomplete-evidence")
        output_dir = self.work / "published-issue-case"
        result = self._run_cli(
            self.package_path, self.plan_path, self.qa_path, self.inventory_path, report_path,
            "--pptx", self.pptx, "--runtime-preflight", self.preflight_path, "--config", self.config_path,
            "--render-root", self.render_root, "--output-dir", output_dir,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        delivered = json.loads((output_dir / "ppt-supervision-report.json").read_text(encoding="utf-8"))
        self.assertIn("AUD-F-SYNTHETIC-RENDER", json.dumps(delivered, ensure_ascii=False))
        markdown = (output_dir / "work-report.md").read_text(encoding="utf-8")
        self.assertIn("AUD-F-SYNTHETIC-RENDER", markdown)

    def test_calibrated_issues_can_be_archived_without_legacy_mediation_event(self) -> None:
        report_path = self._assemble_calibrated_issue_case(omit_lifecycle_events=True)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertNotIn("lifecycle_events", report)
        self._assert_calibrated_issue_delivery(report_path)

    def test_calibrated_issues_can_be_archived_with_empty_lifecycle_events(self) -> None:
        report_path = self._assemble_calibrated_issue_case(omit_lifecycle_events=False)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report.get("lifecycle_events"), [])
        self._assert_calibrated_issue_delivery(report_path)

    def test_real_cli_rejects_calibrated_release_without_new_auditor_record(self) -> None:
        stages = self._record_stages_and_calibrations()
        auditor_path = self._write_audit_inputs(stages=stages)
        draft_path = self._build_report(stages=stages, auditor_path=auditor_path)
        self._record_supervisor(stages, draft_path, auditor_path)
        report_path = self._assemble_report(stages, draft_path, auditor_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report.pop("auditor_artifact")
        write_json(report_path, report)
        output_dir = self.work / "rejected-no-audit"
        result = self._run_cli(
            self.package_path, self.plan_path, self.qa_path, self.inventory_path, report_path,
            "--pptx", self.pptx, "--runtime-preflight", self.preflight_path, "--config", self.config_path,
            "--render-root", self.render_root, "--output-dir", output_dir, expected=1,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_dir.exists())
        self.assertIn("auditor", (result.stdout + result.stderr).casefold())

    def test_real_cli_rejects_post_audit_pptx_mutation(self) -> None:
        stages = self._record_stages_and_calibrations()
        auditor_path = self._write_audit_inputs(stages=stages)
        draft_path = self._build_report(stages=stages, auditor_path=auditor_path)
        self._record_supervisor(stages, draft_path, auditor_path)
        report_path = self._assemble_report(stages, draft_path, auditor_path)
        self.pptx.write_bytes(self.pptx.read_bytes() + b"mutated-after-audit")
        output_dir = self.work / "rejected-post-audit-mutation"
        result = self._run_cli(
            self.package_path, self.plan_path, self.qa_path, self.inventory_path, report_path,
            "--pptx", self.pptx, "--runtime-preflight", self.preflight_path, "--config", self.config_path,
            "--render-root", self.render_root, "--output-dir", output_dir, expected=1,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_dir.exists())
        self.assertRegex((result.stdout + result.stderr).casefold(), "hash|stale|pptx")

    def test_assemble_rejects_a_different_audit_file_with_the_same_final_pptx(self) -> None:
        from independent_audit import canonical_record_sha256  # noqa: E402

        stages = self._record_stages_and_calibrations()
        auditor_one = self._write_audit_inputs(stages=stages)
        auditor_two = self.work / "auditor-two.json"
        second = json.loads(auditor_one.read_text(encoding="utf-8"))
        second["audit_id"] = "AUDIT-DIFFERENT-SAME-PPTX"
        second["record_sha256"] = canonical_record_sha256(second)
        auditor_two.write_bytes(json_bytes(second))
        draft_path = self._build_report(stages=stages, auditor_path=auditor_two)
        # The fifth stage record is deliberately bound to auditor_one while
        # the assembly claims auditor_two.  Both files bind the same PPTX, so
        # only the real Supervisor-record closeout check can catch the swap.
        self._record_supervisor(stages, draft_path, auditor_one)
        output_report = self.work / "should-not-assemble.json"
        args: list[object] = ["assemble-report"]
        for name in ("logic", "copy", "art-direction", "output", "supervisor"):
            args.extend(("--record", stages[name]))
        args.extend(
            (
                "--draft", draft_path,
                "--package", self.package_path,
                "--plan", self.plan_path,
                "--qa", self.qa_path,
                "--inventory", self.inventory_path,
                "--pptx", self.pptx,
                "--runtime-preflight", self.preflight_path,
                "--config", self.config_path,
                "--calibration-logic-copy", stages["calibration_logic_copy"],
                "--calibration-copy-art-direction", stages["calibration_copy_art_direction"],
                "--calibration-art-direction-output", stages["calibration_art_direction_output"],
                "--auditor", auditor_two,
                "--task-request", self.task,
                "--acceptance-contract", self.acceptance_path,
                "--supervisor-rules", self.supervisor_rules_path,
                "--render-root", self.render_root,
                "--output", output_report,
            )
        )
        result = self._run_cli(*args, expected=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_report.exists())
        self.assertIn("auditor", (result.stdout + result.stderr).casefold())

    def test_calibrated_default_publish_rejects_hand_built_report_without_assembly(self) -> None:
        stages = self._record_stages_and_calibrations()
        auditor_path = self._write_audit_inputs(stages=stages)
        hand_built_report = self._build_report(stages=stages, auditor_path=auditor_path)
        # Deliberately skip Supervisor record and assemble-report.  The
        # selected default policy is calibrated, so a manually shaped report
        # must not be accepted as the new release route.
        output_dir = self.work / "rejected-unassembled"
        result = self._run_cli(
            self.package_path, self.plan_path, self.qa_path, self.inventory_path, hand_built_report,
            "--pptx", self.pptx, "--runtime-preflight", self.preflight_path, "--config", self.config_path,
            "--render-root", self.render_root, "--output-dir", output_dir, expected=1,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_dir.exists())
        self.assertRegex((result.stdout + result.stderr).casefold(), "assembl|work record|supervisor")

    def test_real_preflight_cli_allows_calibrated_no_render_as_deferred(self) -> None:
        from packages.personal_extension.resolver import prepare_unified_task_selection, validate_task_selection  # noqa: E402

        config_path = self.work / "task-config.json"
        config, selection = prepare_unified_task_selection(ROOT, config_path, library_enabled=False)
        config_path.write_bytes(json_bytes(config))
        selection_path = self.work / "task-selection.json"
        selection_path.write_bytes(json_bytes(selection))
        validate_task_selection(selection_path, config_path, ROOT, expected_mode="unified")
        component_path = self.work / "component-version-report.json"
        self._run_target_script(
            ROOT / "scripts" / "component_version_guard.py",
            "--root", ROOT,
            "--mode", "application",
            "--output", component_path,
        )
        challenge_path = self.work / "preflight-challenge.json"
        self._run_target_script(
            ROOT / "scripts" / "runtime_preflight.py",
            "--issue-challenge", "--task-request", self.task, "--output", challenge_path,
        )
        preflight_path = self.work / "preflight-report.json"
        self._run_target_script(
            ROOT / "scripts" / "runtime_preflight.py",
            "--task-request", self.task,
            "--challenge", challenge_path,
            "--task-selection", selection_path,
            "--config", config_path,
            "--component-version-report", component_path,
            "--output", preflight_path,
        )
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        selected = preflight["selected_route"]
        if selected.get("render_backend") == "none":
            self.assertTrue(selected.get("attemptable"), preflight)
            self.assertFalse(selected.get("available"), preflight)
            self.assertIn("render-preview", selected.get("missing_capabilities", []), preflight)
            self.assertIn("deferred", " ".join(preflight.get("warnings", [])).casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
