"""Focused regression tests for the calibrated delivery primitives."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import zipfile
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from packages.validators.independent_audit import (
    IndependentAuditError,
    create_auditor_artifact,
    validate_auditor_artifact,
)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class CalibratedAuditTests(unittest.TestCase):
    def _fixtures(self, root: Path) -> tuple[Path, Path, Path, dict[str, Path]]:
        task = root / "task-request.txt"
        task.write_text("Make a truthful presentation", encoding="utf-8")
        acceptance = {
            "contract": "io.clayz.presentation.task-acceptance/1.0",
            "requirements": [
                {
                    "requirement_id": "content",
                    "category": "content",
                    "statement": "Preserve the user request",
                    "owner_stage": "logic",
                    "verification_method": "read the task request",
                    "blocking": True,
                    "classification": "hard",
                },
                {
                    "requirement_id": "visual",
                    "category": "visual",
                    "statement": "Use an editable visual",
                    "owner_stage": "output",
                    "verification_method": "inspect the PPTX",
                    "blocking": False,
                    "classification": "soft",
                },
            ],
            "cover_policy": {"mode": "topic-only", "conclusion_allowed_roles": ["closing"]},
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
                "max_total_seconds": 1,
                "stage_seconds": {stage: 1 for stage in ("root", "preflight", "logic", "copy", "art-direction", "output", "supervisor", "delivery")},
                "max_receipts_per_stage": 1,
                "max_candidates_per_stage": 1,
                "max_selected_per_stage": 1,
                "max_write_count": 1,
                "max_render_count": 1,
                "max_repair_count": 0,
            },
        }
        acceptance["contract_sha256"] = _digest(acceptance)
        acceptance_path = root / "acceptance.json"
        acceptance_path.write_text(json.dumps(acceptance), encoding="utf-8")
        rules_path = root / "supervisor-rules.json"
        rules_path.write_text(json.dumps({
            "contract": "io.clayz.presentation.supervisor-rules/1.0",
            "fixed_commitments": [{"rule_id": "fixed-1", "statement": "Preserve task commitments", "classification": "hard"}],
            "explicit_changes": [{"rule_id": "change-1", "statement": "Deferred render is disclosed", "classification": "soft"}],
        }), encoding="utf-8")
        sources = {}
        for kind in ("package", "plan", "qa", "inventory"):
            path = root / f"{kind}.json"
            path.write_text(json.dumps({"kind": kind}), encoding="utf-8")
            sources[kind] = path
        return task, acceptance_path, rules_path, sources

    def test_no_render_is_an_honest_incomplete_audit(self) -> None:
        from tests.calibrated_audit_fixtures import build_minimal_pptx

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task, acceptance, rules, sources = self._fixtures(root)
            pptx = root / "final.pptx"
            build_minimal_pptx(pptx)
            ref = lambda path: f"{path.name} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}"
            hard = [
                {"requirement_id": "content", "classification": "hard", "status": "pass", "evidence_refs": [ref(task)], "observation": "Task request was read."},
                {"requirement_id": "visual", "classification": "soft", "status": "pass", "evidence_refs": [ref(pptx)], "observation": "PPTX is present."},
            ]
            coverage = {
                "hard_requirement_ids": ["content"],
                "soft_requirement_ids": ["visual"],
                "requirements": hard,
                "rules": [
                    {"rule_id": "fixed-1", "source": "fixed_commitment", "status": "pass", "evidence_refs": [ref(rules)], "observation": "Fixed rule read."},
                    {"rule_id": "change-1", "source": "explicit_change", "status": "pass", "evidence_refs": [ref(rules)], "observation": "Change read."},
                ],
                "render_status": "deferred",
            }
            audit = create_auditor_artifact(
                task_request=task,
                acceptance_rules=acceptance,
                supervisor_rules=rules,
                source_records=sources,
                final_pptx=pptx,
                coverage=coverage,
                findings=[],
                independent_context={
                    "execution_mode": "same-model-new-context",
                    "context_id": "audit-context-1",
                    "model_identity_disclosure": "not-attested",
                    "limitations": ["No render provider was available."],
                },
                run_id="run-1",
                task_request_sha256=hashlib.sha256(task.read_bytes()).hexdigest(),
            )
            self.assertEqual(audit["audit_status"], "incomplete-evidence")
            validate_auditor_artifact(audit)

    def test_tampered_source_bytes_are_rejected(self) -> None:
        from tests.calibrated_audit_fixtures import build_minimal_pptx

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task, acceptance, rules, sources = self._fixtures(root)
            pptx = root / "final.pptx"
            build_minimal_pptx(pptx)
            ref = lambda path: f"{path.name} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}"
            coverage = {
                "hard_requirement_ids": ["content"],
                "soft_requirement_ids": ["visual"],
                "requirements": [
                    {"requirement_id": "content", "classification": "hard", "status": "pass", "evidence_refs": [ref(task)], "observation": "Read."},
                    {"requirement_id": "visual", "classification": "soft", "status": "pass", "evidence_refs": [ref(pptx)], "observation": "Present."},
                ],
                "rules": [
                    {"rule_id": "fixed-1", "source": "fixed_commitment", "status": "pass", "evidence_refs": [ref(rules)], "observation": "Read."},
                    {"rule_id": "change-1", "source": "explicit_change", "status": "pass", "evidence_refs": [ref(rules)], "observation": "Read."},
                ],
                "render_status": "deferred",
            }
            kwargs = dict(
                task_request=task,
                acceptance_rules=acceptance,
                supervisor_rules=rules,
                source_records=sources,
                final_pptx=pptx,
                coverage=coverage,
                independent_context={"execution_mode": "same-model-new-context", "context_id": "c", "model_identity_disclosure": "not-attested", "limitations": ["render deferred"]},
                run_id="run-1",
                task_request_sha256=hashlib.sha256(task.read_bytes()).hexdigest(),
            )
            audit = create_auditor_artifact(**kwargs)
            sources["qa"].write_text("tampered", encoding="utf-8")
            with self.assertRaises(IndependentAuditError):
                validate_auditor_artifact(audit)

    def test_python_pptx_adapter_writes_east_asian_run_font_when_missing(self) -> None:
        from packages.adapters.python_pptx.render import render

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "render-manifest.json"
            output = root / "rendered.pptx"
            manifest.write_text(json.dumps({
                "contract": "io.clayz.presentation.render-manifest/1.0",
                "presentation": {"layout": "LAYOUT_WIDE"},
                "slides": [{"slide_id": "S01", "objects": [{
                    "object_id": "T01", "type": "text", "text": "中文 123",
                    "options": {"x": 1, "y": 1, "w": 4, "h": 1, "fontFace": "Aptos", "fontSize": 20},
                }]}],
            }, ensure_ascii=False), encoding="utf-8")
            render(manifest, output)
            with zipfile.ZipFile(output) as archive:
                slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertIn('ea typeface="Aptos"', slide_xml)

    def test_unsupported_complete_render_evidence_is_rejected(self) -> None:
        from tests.calibrated_audit_fixtures import build_minimal_pptx, build_synthetic_pixel_render

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task, acceptance, rules, sources = self._fixtures(root)
            pptx = build_minimal_pptx(root / "final.pptx")
            render = build_synthetic_pixel_render(root / "render.png")
            ref = lambda path: f"{path.name} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}"
            coverage = {
                "hard_requirement_ids": ["content"],
                "soft_requirement_ids": ["visual"],
                "requirements": [
                    {"requirement_id": "content", "classification": "hard", "status": "pass", "evidence_refs": [ref(task)], "observation": "Read."},
                    {"requirement_id": "visual", "classification": "soft", "status": "pass", "evidence_refs": [ref(render)], "observation": "Rendered."},
                ],
                "rules": [
                    {"rule_id": "fixed-1", "source": "fixed_commitment", "status": "pass", "evidence_refs": [ref(rules)], "observation": "Read."},
                    {"rule_id": "change-1", "source": "explicit_change", "status": "pass", "evidence_refs": [ref(rules)], "observation": "Read."},
                ],
                "render_status": "complete",
            }
            audit = create_auditor_artifact(
                task_request=task,
                acceptance_rules=acceptance,
                supervisor_rules=rules,
                source_records=sources,
                final_pptx=pptx,
                render_evidence={"render": render},
                coverage=coverage,
                findings=[],
                independent_context={"execution_mode": "same-model-new-context", "context_id": "c", "model_identity_disclosure": "not-attested", "limitations": []},
                run_id="run-1",
                task_request_sha256=hashlib.sha256(task.read_bytes()).hexdigest(),
            )
            bad_render = root / "render.txt"
            bad_render.write_text("not a rendered image", encoding="utf-8")
            audit["render_evidence"] = [{"kind": "render", "path": str(bad_render), "sha256": hashlib.sha256(bad_render.read_bytes()).hexdigest(), "bytes": bad_render.stat().st_size}]
            audit["record_sha256"] = hashlib.sha256(json.dumps({key: value for key, value in audit.items() if key != "record_sha256"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            with self.assertRaises(IndependentAuditError):
                validate_auditor_artifact(audit)

    def test_finalizer_reports_missing_requirement_classification_early(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "draft.json"
            output = root / "acceptance.json"
            draft.write_text(json.dumps({"requirements": [{"requirement_id": "REQ-1"}]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "scripts" / "finalize_task_acceptance.py"), str(draft), str(output)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing classification", result.stdout)

    def test_calibrated_record_cli_allows_quality_fail_without_blocking_flag(self) -> None:
        from packages.runtime.preflight import issue_run_challenge

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / "task.txt"
            task.write_text("quality-limited task", encoding="utf-8")
            challenge = issue_run_challenge(task.read_bytes(), task_root=root)
            challenge_path = root / "challenge.json"
            challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
            acceptance = root / "acceptance.json"
            acceptance.write_text("{}", encoding="utf-8")
            artifact = root / "package.json"
            artifact.write_text("{\"stage\": \"logic\"}", encoding="utf-8")
            draft = root / "logic-draft.json"
            draft.write_text(json.dumps({
                "summary": "Quality issue was observed and disclosed.",
                "decisions": ["Continue with a disclosed limitation."],
                "checks": [{"name": "visual quality", "status": "fail", "evidence_roles": ["package"]}],
                "open_issues": ["quality limitation remains"],
            }), encoding="utf-8")
            output = root / "logic-record.json"
            command = [
                sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "scripts" / "publish_supervised_pair.py"),
                "record-stage", "--stage", "logic", "--draft", str(draft), "--challenge", str(challenge_path),
                "--artifact", f"package={artifact}", "--acceptance-contract", str(acceptance), "--output", str(output),
            ]
            result = subprocess.run(
                command,
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(record["checks"][0]["blocking"])
            self.assertEqual(record["readiness"], "quality-limited")


if __name__ == "__main__":
    unittest.main()
