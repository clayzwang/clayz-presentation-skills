#!/usr/bin/env python3
"""Regression tests for calibrated final-audit input bindings.

These tests build a valid calibrated CLI baseline first, then replace one
bound input with a second, internally self-consistent artifact.  A changed
hash alone is not the target: the replacement artifacts retain valid local
hashes and contracts, but must still be rejected when they are the wrong
upstream evidence for the assembled delivery.
"""

from __future__ import annotations

import hashlib
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "packages" / "validators") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages" / "validators"))

from tests.calibrated_audit_fixtures import (  # noqa: E402
    file_ref,
    json_bytes,
    sha256_file,
    write_json,
)
from tests import test_calibrated_audit_adversarial as adversarial  # noqa: E402


def _json_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class _CalibratedBaselineMixin:
    """Materialize one real CLI baseline without changing production files."""

    def _baseline(self) -> tuple[adversarial.RealCliReleaseTests, dict[str, Path], Path, dict[str, object]]:
        harness = adversarial.RealCliReleaseTests("test_real_cli_produces_pptx_report_and_manifest_with_honest_limitations")
        harness.setUp()
        self.addCleanup(harness.tearDown)
        stages = harness._record_stages_and_calibrations()
        auditor_path = harness._write_audit_inputs(stages=stages)
        draft_path = harness._build_report(stages=stages, auditor_path=auditor_path)
        harness._record_supervisor(stages, draft_path, auditor_path)
        report_path = harness._assemble_report(stages, draft_path, auditor_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return harness, stages, report_path, report


class CalibrationAssemblyBindingTests(_CalibratedBaselineMixin, unittest.TestCase):
    def test_assembly_rejects_valid_calibrations_that_were_not_consumed(self) -> None:
        """The report's three calibration files must be the files consumed downstream."""

        from packages.validators.stage_work_records import create_calibration_record
        from scripts.publish_supervised_pair import validate_work_record_assembly

        harness, stages, _report_path, report = self._baseline()
        challenge = json.loads(harness.challenge.read_text(encoding="utf-8"))
        acceptance_path = harness.acceptance_path
        rules_path = harness.supervisor_rules_path
        alternate: list[tuple[str, Path, dict[str, object]]] = []
        previous: dict[str, object] | None = None
        for step, source_key, output_name in (
            ("logic-to-copy", "logic", "alternate-calibration-logic-copy.json"),
            ("copy-to-art-direction", "copy", "alternate-calibration-copy-art.json"),
            ("art-direction-to-output", "art-direction", "alternate-calibration-art-output.json"),
        ):
            path = harness.work / output_name
            value = create_calibration_record(
                step,
                stages[source_key],
                acceptance_path,
                rules_path,
                [],
                challenge,
                output=None,
                calibration_id=f"ALT-{step}",
                previous_calibration=previous,
                recorded_at="2026-09-14T01:29:00Z",
            )
            path.write_bytes(json_bytes(value))
            alternate.append((step, path, value))
            previous = value

        calibration_input_names = (
            "calibration_logic_copy",
            "calibration_copy_art_direction",
            "calibration_art_direction_output",
        )
        report["calibration_artifacts"] = [
            {"step": step, **file_ref(path)} for step, path, _value in alternate
        ]
        for input_name, (_step, path, _value) in zip(calibration_input_names, alternate):
            report["assembly"]["inputs"][input_name] = file_ref(path)  # type: ignore[index]
        report["assembly"]["report_content_sha256"] = _json_hash(  # type: ignore[index]
            {key: value for key, value in report.items() if key != "assembly"}
        )

        # The stage records still consume the original calibration chain.  Each
        # alternate file is valid and forms its own valid three-record chain,
        # so a mere stale hash cannot explain this rejection.
        with self.assertRaises((ValueError, RuntimeError)):
            validate_work_record_assembly(report, harness.pptx)


class AuditorSourceBindingTests(_CalibratedBaselineMixin, unittest.TestCase):
    def test_assembly_rejects_auditor_package_and_plan_from_another_baseline(self) -> None:
        """Auditor source rows must be the package/plan being delivered."""

        from independent_audit import canonical_record_sha256
        from scripts.publish_supervised_pair import validate_work_record_assembly

        harness, _stages, _report_path, report = self._baseline()
        auditor_path = Path(report["auditor_artifact"]["path"])  # type: ignore[index]
        alternate_package = write_json(harness.work / "alternate-package.json", {"alternate": "package"})
        alternate_plan = write_json(harness.work / "alternate-plan.json", {"alternate": "plan"})
        alternate_auditor = json.loads(auditor_path.read_text(encoding="utf-8"))
        source_rows = alternate_auditor["source_records"]
        for row in source_rows:
            if row["kind"] == "package":
                row.update(file_ref(alternate_package))
            elif row["kind"] == "plan":
                row.update(file_ref(alternate_plan))
        alternate_auditor["record_sha256"] = canonical_record_sha256(alternate_auditor)
        alternate_auditor_path = write_json(harness.work / "alternate-auditor.json", alternate_auditor)

        report["auditor_artifact"] = file_ref(alternate_auditor_path)
        report["assembly"]["inputs"]["auditor"] = file_ref(alternate_auditor_path)  # type: ignore[index]
        report["supervisor_roles"]["final_auditor"]["evidence_refs"] = [  # type: ignore[index]
            f"{alternate_auditor_path.name} sha256={sha256_file(alternate_auditor_path)}"
        ]
        for event in report["lifecycle_events"]:  # type: ignore[index]
            if event.get("action") == "final-audit-completed":
                event["evidence_refs"] = [
                    f"{alternate_auditor_path.name} sha256={sha256_file(alternate_auditor_path)}"
                ]
        report["supervisor_release"]["auditor_artifact_sha256"] = sha256_file(alternate_auditor_path)  # type: ignore[index]
        report["assembly"]["report_content_sha256"] = _json_hash(  # type: ignore[index]
            {key: value for key, value in report.items() if key != "assembly"}
        )

        # The alternate Auditor is internally valid and binds the same final
        # PPTX/QA/inventory, but it inspected another package and plan.
        with self.assertRaises((ValueError, RuntimeError)):
            validate_work_record_assembly(report, harness.pptx)


class RenderEvidenceTruthfulnessTests(unittest.TestCase):
    def test_non_native_text_file_cannot_claim_complete_render_coverage(self) -> None:
        from independent_audit import IndependentAuditError, validate_auditor_artifact

        harness = adversarial.IndependentAuditAdversarialTests("test_valid_artifact_accepts_one_auditor_context_without_five_model_claim")
        harness.setUp()
        self.addCleanup(harness.tearDown)
        text_render = harness.work / "render.txt"
        text_render.write_text("this is not rendered pixels", encoding="utf-8")
        artifact = harness._create(render_evidence={"render": text_render})

        with self.assertRaises(IndependentAuditError):
            validate_auditor_artifact(
                artifact,
                expected_run_id=harness.run_id,
                expected_task_request_sha256=harness.task_sha,
                expected_pptx_sha256=sha256_file(harness.pptx),
            )


class TaskAcceptanceClassificationTests(unittest.TestCase):
    def test_finalize_task_acceptance_reports_missing_classification_before_final_audit(self) -> None:
        draft = adversarial._acceptance_contract(include_soft=False)
        draft["requirements"][0].pop("classification")  # type: ignore[index]
        with tempfile.TemporaryDirectory(prefix="final-audit-classification-") as directory:
            work = Path(directory)
            draft_path = write_json(work / "acceptance-draft.json", draft)
            output_path = work / "task-acceptance.json"
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT), env.get("PYTHONPATH", "")]))
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "finalize_task_acceptance.py"),
                    str(draft_path),
                    str(output_path),
                    "--config",
                    str(ROOT / "config" / "default.json"),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("classification", (result.stdout + result.stderr).casefold())
            self.assertFalse(output_path.exists())


class ReleaseConditionTests(_CalibratedBaselineMixin, unittest.TestCase):
    def test_explicit_no_delivery_condition_blocks_release(self) -> None:
        """A user release condition must be consumed by the final publication gate."""

        from packages.validators.acceptance_contract import acceptance_contract_digest
        from packages.validators.independent_audit import canonical_record_sha256

        harness = adversarial.RealCliReleaseTests("test_real_cli_produces_pptx_report_and_manifest_with_honest_limitations")
        harness.setUp()
        self.addCleanup(harness.tearDown)
        condition = {
            "condition_id": "COND-NO-DELIVERY-RAW",
            "requirement_id": "REQ-RAW-USER",
            "statement": "Do not deliver when the raw request requirement fails.",
            "source": "user-request",
            "action": "no-delivery",
        }
        acceptance = copy.deepcopy(harness.package["acceptance_contract"])
        acceptance["release_conditions"] = [condition]
        acceptance["contract_sha256"] = acceptance_contract_digest(acceptance)
        harness.package["acceptance_contract"] = copy.deepcopy(acceptance)
        harness.plan["acceptance_contract"] = copy.deepcopy(acceptance)
        harness.qa["acceptance_contract"] = copy.deepcopy(acceptance)
        harness.acceptance_path.write_bytes(json_bytes(acceptance))
        harness.package_path.write_bytes(json_bytes(harness.package))
        harness.plan_path.write_bytes(json_bytes(harness.plan))
        harness.qa_path.write_bytes(json_bytes(harness.qa))

        stages = harness._record_stages_and_calibrations()
        auditor_path = harness._write_audit_inputs(stages=stages)
        auditor = json.loads(auditor_path.read_text(encoding="utf-8"))
        auditor["coverage"]["requirements"] = [
            {
                **row,
                "status": "fail" if row["requirement_id"] == "REQ-RAW-USER" else row["status"],
            }
            for row in auditor["coverage"]["requirements"]
        ]
        auditor["findings"][0]["requirement_ids"] = ["REQ-RAW-USER"]
        auditor["audit_status"] = "issues-found"
        auditor["record_sha256"] = canonical_record_sha256(auditor)
        auditor_path.write_bytes(json_bytes(auditor))
        draft_path = harness._build_report(stages=stages, auditor_path=auditor_path)
        harness._record_supervisor(stages, draft_path, auditor_path)

        try:
            report_path = harness._assemble_report(stages, draft_path, auditor_path)
        except AssertionError as exc:
            # A correct implementation may reject at report assembly instead
            # of waiting for the final publisher.  The rejection must name the
            # explicit release condition, rather than an unrelated hash issue.
            self.assertRegex(str(exc).casefold(), r"release|no.?delivery|condition")
            return

        output_dir = harness.work / "blocked-by-explicit-condition"
        result = harness._run_cli(
            harness.package_path,
            harness.plan_path,
            harness.qa_path,
            harness.inventory_path,
            report_path,
            "--pptx",
            harness.pptx,
            "--runtime-preflight",
            harness.preflight_path,
            "--config",
            harness.config_path,
            "--render-root",
            harness.render_root,
            "--output-dir",
            output_dir,
            expected=1,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex((result.stdout + result.stderr).casefold(), r"release|no.?delivery|condition")
        self.assertFalse(output_dir.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
