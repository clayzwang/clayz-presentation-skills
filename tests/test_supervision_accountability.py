#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Regression tests for Supervisor role, lifecycle, preflight, and delivery evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from validate_supervision_report import CONTRACT_VERSION, validate_supervisor_accountability  # noqa: E402


BRIEF_DIGEST = "a" * 64
RUN_ID = "run-supervision-test"
TASK_REQUEST_SHA256 = "b" * 64
RUN_NONCE = "c" * 64
RUN_CHALLENGE_SHA256 = "d" * 64
RUN_CONSUMPTION_SHA256 = "e" * 64
RUN_ISSUED_AT = "2026-08-29T01:00:00+00:00"
# Keep the synthetic challenge valid independently of the wall clock. Expiry
# behaviour itself is covered by the runtime preflight regression tests.
RUN_EXPIRES_AT = "2099-01-01T00:00:00+00:00"
RESOLVED_CONFIG = {"renderer": {"required_capabilities": ["editable-text", "render-preview"]}}
RESOLVED_CONFIG_SHA256 = hashlib.sha256(
    json.dumps(RESOLVED_CONFIG, ensure_ascii=False, sort_keys=True).encode("utf-8")
).hexdigest()


def _publisher_module():
    path = ROOT / "scripts" / "publish_supervised_pair.py"
    spec = importlib.util.spec_from_file_location("publish_supervised_pair_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _preflight() -> dict:
    return {
        "contract": "io.clayz.presentation.runtime-preflight/1.2",
        "scan_id": "runtime-synthetic-audit",
        "run_binding": {
            "run_id": RUN_ID,
            "task_request_sha256": TASK_REQUEST_SHA256,
            "nonce": RUN_NONCE,
            "issued_at": RUN_ISSUED_AT,
            "expires_at": RUN_EXPIRES_AT,
            "challenge_sha256": RUN_CHALLENGE_SHA256,
            "task_root_sha256": "6" * 64,
            "binding_source": "script-issued-challenge",
            "issuance_receipt": ".clayz-run-challenges/run-issued.json",
            "issuance_receipt_sha256": "7" * 64,
            "consumption_receipt": ".clayz-run-challenges/consumed/run.json",
            "consumption_receipt_sha256": RUN_CONSUMPTION_SHA256,
        },
        "config_binding": {"path": "config/personal-extension-resolved.json", "sha256": RESOLVED_CONFIG_SHA256, "source": "personal-resolved"},
        "required_capabilities": ["editable-text", "render-preview"],
        "dependencies": {
            "host_tools": {
                "available": True,
                "observation": {
                    "run_id": RUN_ID,
                    "task_request_sha256": TASK_REQUEST_SHA256,
                    "challenge_sha256": RUN_CHALLENGE_SHA256,
                    "verification_status": "challenge-bound-host-declaration",
                    "assurance_level": "host-declared-unverified",
                    "route_eligible": False,
                    "evidence_receipts": [{"artifact": "host-tool-inventory.json", "sha256": "f" * 64}],
                },
            }
        },
        "selected_route": {
            "route_id": "native-presentation-tool+libreoffice",
            "authoring_backend": "native-presentation-tool",
            "render_backend": "libreoffice",
            "available": False,
            "attemptable": True,
            "assurance_level": "host-declared-unverified",
            "missing_capabilities": [],
        },
        "target_application_checks": [
            {"application": "powerpoint", "capability": "powerpoint-reopen-render", "availability": "unavailable"},
            {"application": "wps", "capability": "wps-reopen-render", "availability": "unavailable"},
            {"application": "libreoffice", "capability": "libreoffice-reopen-render", "availability": "available"},
        ],
    }


def _preflight_digest() -> str:
    payload = _json_bytes(_preflight())
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _hashed_ref(root: Path, relative: str, fragment: str | None = None, extra: str | None = None) -> str:
    artifact = root / relative
    reference = relative + (f"#{fragment}" if fragment else "")
    reference += f" sha256={hashlib.sha256(artifact.read_bytes()).hexdigest()}"
    if extra:
        reference += f" {extra}"
    return reference


def _environment_observation(root: Path) -> dict:
    return {
        "preflight": {
            "artifact": "runtime-preflight.json",
            "scan_id": "runtime-synthetic-audit",
            "sha256": _preflight_digest(),
            "run_id": RUN_ID,
            "task_request_sha256": TASK_REQUEST_SHA256,
            "config_sha256": RESOLVED_CONFIG_SHA256,
            "nonce": RUN_NONCE,
            "challenge_sha256": RUN_CHALLENGE_SHA256,
            "task_root_sha256": "6" * 64,
            "issued_at": RUN_ISSUED_AT,
            "expires_at": RUN_EXPIRES_AT,
            "issuance_receipt_sha256": "7" * 64,
            "consumption_receipt_sha256": RUN_CONSUMPTION_SHA256,
        },
        "route": {
            "route_id": "native-presentation-tool+libreoffice",
            "authoring_backend": "native-presentation-tool",
            "render_backend": "libreoffice",
            "status": "provisional",
        },
        "required_capabilities": {
            "configured": ["editable-text", "render-preview"],
            "satisfied": [],
            "declared_unverified": ["editable-text", "render-preview"],
            "missing": [],
        },
        "target_applications": [
            {
                "application": "powerpoint",
                "capability": "powerpoint-reopen-render",
                "availability": "unavailable",
                "final_status": "deferred",
                "authoring_gate": False,
                "evidence_refs": [_hashed_ref(root, "runtime-preflight.json", "target_application_checks.powerpoint")],
            },
            {
                "application": "wps",
                "capability": "wps-reopen-render",
                "availability": "unavailable",
                "final_status": "deferred",
                "authoring_gate": False,
                "evidence_refs": [_hashed_ref(root, "runtime-preflight.json", "target_application_checks.wps")],
            },
            {
                "application": "libreoffice",
                "capability": "libreoffice-reopen-render",
                "availability": "available",
                "final_status": "pass",
                "authoring_gate": False,
                "evidence_refs": [_hashed_ref(root, "output/final-reopen-render/libreoffice/target-application-check.json")],
            },
        ],
        "compatibility_scope": "partial",
        "attribution_summary": "LibreOffice acceptance passed; PowerPoint and WPS native acceptance remain deferred.",
    }


def _package() -> dict:
    return {
        "contract_version": "2.3",
        "package_id": "synthetic-supervision-test",
        "version": "1.0.0",
        "status": "copy-approved",
        "copy_layer": {"status": "copy-approved"},
        "resource_inventory": {
            "contract": "io.clayz.presentation.resource-inventory/1.0",
            "user_brief": {
                "status": "presented",
                "presented_at": "2026-08-29T09:01:00+08:00",
                "content_sha256": BRIEF_DIGEST,
            }
        }
    }


def _event(number: int, phase: str, role: str, action: str, *, minute: int, root: Path) -> dict:
    evidence = {
        "supervision-started": [_hashed_ref(root, "ppt-resource-inventory.json")],
        "runtime-preflight-completed": [_hashed_ref(root, "runtime-preflight.json")],
        "resource-brief-presented": [_hashed_ref(root, "ppt-resource-inventory.json", "user_brief")],
        "logic-handoff-recorded": [_hashed_ref(root, "ppt-design-package.json")],
        "copy-handoff-recorded": [_hashed_ref(root, "ppt-design-package.json", "copy_layer")],
        "art-direction-handoff-recorded": [_hashed_ref(root, "ppt-art-direction-plan.json")],
        "output-handoff-recorded": [_hashed_ref(root, "final.pptx"), _hashed_ref(root, "ppt-output-qa.json")],
        "final-audit-completed": [_hashed_ref(root, "ppt-output-qa.json"), "ppt-supervision-report.json#slides"],
        "delivery-pair-locked": [_hashed_ref(root, "final.pptx"), "ppt-supervision-report.json"],
        "control-returned": ["ppt-supervision-report.json#control_returned_to"],
    }
    return {
        "event_id": f"SUP-E{number:02d}",
        "occurred_at": f"2026-08-29T09:{minute:02d}:00+08:00",
        "phase": phase,
        "actor_role": role,
        "action": action,
        "status": "returned" if action == "control-returned" else "completed",
        "summary": f"Recorded {action} with task-local evidence.",
        "evidence_refs": evidence[action],
    }


def _report(pptx: Path, report_path: Path) -> dict:
    root = report_path.parent
    events = [
        _event(1, "root", "initiator", "supervision-started", minute=0, root=root),
        _event(2, "preflight", "recorder", "runtime-preflight-completed", minute=0, root=root),
        _event(3, "preflight", "recorder", "resource-brief-presented", minute=1, root=root),
        _event(4, "logic", "recorder", "logic-handoff-recorded", minute=2, root=root),
        _event(5, "copy", "recorder", "copy-handoff-recorded", minute=3, root=root),
        _event(6, "art-direction", "recorder", "art-direction-handoff-recorded", minute=4, root=root),
        _event(7, "output", "recorder", "output-handoff-recorded", minute=5, root=root),
        _event(8, "supervision", "final_auditor", "final-audit-completed", minute=6, root=root),
        _event(9, "delivery", "recorder", "delivery-pair-locked", minute=7, root=root),
        _event(10, "delivery", "initiator", "control-returned", minute=8, root=root),
    ]
    events[2]["evidence_refs"] = [
        _hashed_ref(root, "ppt-resource-inventory.json", "user_brief", f"content_sha256={BRIEF_DIGEST}")
    ]
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": RUN_ID,
        "task_request_sha256": TASK_REQUEST_SHA256,
        "supervised_at": "2026-08-30T00:08:00+00:00",
        "run_status": "complete-with-deferred-acceptance",
        "issues": [],
        "slides": [],
        "control_returned_to": "main-process-or-user",
        "environment_observation": _environment_observation(root),
        "supervisor_roles": {
            "initiator": {"status": "complete", "summary": "Started the governed run and returned control.", "evidence_refs": [_hashed_ref(root, "ppt-resource-inventory.json"), "ppt-supervision-report.json"]},
            "mediator": {"status": "not-needed", "summary": "No conflict or finding required mediation.", "evidence_refs": ["ppt-supervision-report.json#issues"]},
            "recorder": {"status": "complete", "summary": "Recorded preflight, stage handoffs, audit, and delivery.", "evidence_refs": ["ppt-supervision-report.json#lifecycle_events"]},
            "final_auditor": {"status": "complete", "summary": "Completed the independent final audit.", "evidence_refs": [_hashed_ref(root, "ppt-output-qa.json"), "ppt-supervision-report.json#slides"]},
        },
        "lifecycle_events": events,
        "delivery_pair": {
            "status": "ready",
            "required_artifacts": ["pptx", "supervision-report"],
            "pptx": {"path": pptx.name, "sha256": hashlib.sha256(pptx.read_bytes()).hexdigest()},
            "supervision_report": {"path": report_path.name},
            "delivery_manifest": {"path": "delivery-manifest.json"},
            "publisher": "scripts/publish_supervised_pair.py",
            "evidence": "The final PPTX hash and this report path are locked for the same user handoff.",
        },
    }


class SupervisionAccountabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.pptx = self.root / "final.pptx"
        self.pptx.write_bytes(b"synthetic final pptx payload")
        self.report_path = self.root / "ppt-supervision-report.json"
        self.report_path.write_text("{}", encoding="utf-8")
        (self.root / "runtime-preflight.json").write_bytes(_json_bytes(_preflight()))
        (self.root / "ppt-resource-inventory.json").write_bytes(_json_bytes(_package()["resource_inventory"]))
        (self.root / "ppt-design-package.json").write_bytes(_json_bytes(_package()))
        (self.root / "ppt-art-direction-plan.json").write_bytes(_json_bytes({
            "contract_version": "1.6",
            "status": "art-direction-approved",
            "package_id": _package()["package_id"],
            "package_version": _package()["version"],
        }))
        (self.root / "ppt-output-qa.json").write_bytes(_json_bytes({
            "contract_version": "3.9",
            "package_id": _package()["package_id"],
            "package_version": _package()["version"],
        }))
        target_receipt = self.root / "output" / "final-reopen-render" / "libreoffice" / "target-application-check.json"
        target_receipt.parent.mkdir(parents=True)
        target_receipt.write_bytes(_json_bytes({
            "contract": "io.clayz.presentation.target-application-check/1.0",
            "application": "libreoffice",
            "run_id": RUN_ID,
            "task_request_sha256": TASK_REQUEST_SHA256,
            "executed": True,
            "status": "pass",
            "observed_at": "2026-08-29T09:05:30+08:00",
            "pptx_sha256": hashlib.sha256(self.pptx.read_bytes()).hexdigest(),
            "evidence": "LibreOffice reopened and rendered the final PPTX without a compatibility finding.",
        }))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def validate(self, report: dict) -> list[str]:
        self.report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        return validate_supervisor_accountability(
            _package(),
            report,
            self.pptx,
            self.report_path,
            _preflight(),
            _preflight_digest(),
            RESOLVED_CONFIG,
            RESOLVED_CONFIG_SHA256,
            self.root,
        )

    def test_valid_accountability_record(self) -> None:
        self.assertEqual(self.validate(_report(self.pptx, self.report_path)), [])

    def test_missing_role_is_rejected(self) -> None:
        report = _report(self.pptx, self.report_path)
        del report["supervisor_roles"]["recorder"]
        self.assertTrue(any("recorder" in error for error in self.validate(report)))

    def test_missing_preflight_or_user_brief_event_is_rejected(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["lifecycle_events"] = [event for event in report["lifecycle_events"] if event["action"] != "runtime-preflight-completed"]
        self.assertTrue(any("runtime-preflight-completed" in error for error in self.validate(report)))

        report = _report(self.pptx, self.report_path)
        report["lifecycle_events"][2]["evidence_refs"] = ["ppt-resource-inventory.json#user_brief"]
        self.assertTrue(any("content_sha256" in error for error in self.validate(report)))

    def test_generic_lifecycle_reference_cannot_substitute_for_the_governed_artifact(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["lifecycle_events"][6]["evidence_refs"] = ["evidence/output-handoff-recorded.json"]
        self.assertTrue(any("concrete evidence tokens" in error for error in self.validate(report)))

    def test_hash_valid_but_different_design_package_cannot_substitute(self) -> None:
        report = _report(self.pptx, self.report_path)
        substituted = _package()
        substituted["package_id"] = "different-package"
        (self.root / "ppt-design-package.json").write_bytes(_json_bytes(substituted))
        reference = _hashed_ref(self.root, "ppt-design-package.json")
        report["lifecycle_events"][3]["evidence_refs"] = [reference]
        report["lifecycle_events"][4]["evidence_refs"] = [
            _hashed_ref(self.root, "ppt-design-package.json", "copy_layer")
        ]
        self.assertTrue(any("must match the package" in error for error in self.validate(report)))

    def test_role_placeholders_and_missing_event_artifacts_are_rejected(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["supervisor_roles"]["initiator"]["summary"] = "ok"
        report["supervisor_roles"]["initiator"]["evidence_refs"] = ["placeholder"]
        report["lifecycle_events"][3]["evidence_refs"] = ["missing/ppt-design-package.json"]
        errors = self.validate(report)
        self.assertTrue(any("concrete accountability summary" in error for error in errors))
        self.assertTrue(any("concrete role evidence tokens" in error for error in errors))
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_missing_environment_observation_is_rejected(self) -> None:
        report = _report(self.pptx, self.report_path)
        del report["environment_observation"]
        self.assertTrue(any("environment_observation" in error for error in self.validate(report)))

    def test_unavailable_target_application_must_be_deferred_not_blocking(self) -> None:
        report = _report(self.pptx, self.report_path)
        target = report["environment_observation"]["target_applications"][0]
        target["final_status"] = "fail"
        target["authoring_gate"] = True
        errors = self.validate(report)
        self.assertTrue(any("unavailable target must be deferred" in error for error in errors))
        self.assertTrue(any("must not block authoring" in error for error in errors))

    def test_issue_requires_mediation(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["issues"] = [{"issue_id": "SUP-001"}]
        self.assertTrue(any("mediation" in error for error in self.validate(report)))

    def test_lifecycle_topology_uniqueness_and_action_mapping_are_enforced(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["lifecycle_events"][1], report["lifecycle_events"][8] = (
            report["lifecycle_events"][8],
            report["lifecycle_events"][1],
        )
        for minute, event in enumerate(report["lifecycle_events"]):
            event["occurred_at"] = f"2026-08-29T09:{minute:02d}:00+08:00"
        self.assertTrue(any("canonical order" in error for error in self.validate(report)))

        report = _report(self.pptx, self.report_path)
        duplicate = dict(report["lifecycle_events"][3])
        duplicate["event_id"] = "SUP-DUPLICATE"
        duplicate["occurred_at"] = "2026-08-29T09:02:30+08:00"
        report["lifecycle_events"].insert(4, duplicate)
        self.assertTrue(any("actions must be unique" in error for error in self.validate(report)))

        report = _report(self.pptx, self.report_path)
        report["lifecycle_events"][1]["phase"] = "logic"
        report["lifecycle_events"][1]["actor_role"] = "initiator"
        report["lifecycle_events"][1]["status"] = "blocked"
        errors = self.validate(report)
        self.assertTrue(any("requires preflight" in error for error in errors))
        self.assertTrue(any("requires recorder" in error for error in errors))
        self.assertTrue(any("requires completed" in error for error in errors))

    def test_empty_checkpoint_cannot_complete_mediation(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["issues"] = [{"issue_id": "SUP-001"}]
        checkpoint = self.root / "ppt-supervision-checkpoint.json"
        checkpoint.write_bytes(b"")
        checkpoint_ref = _hashed_ref(self.root, checkpoint.name)
        report["supervisor_roles"]["mediator"] = {
            "status": "complete",
            "summary": "Recorded and mediated the concrete audit finding.",
            "evidence_refs": [checkpoint_ref, "ppt-supervision-report.json#issues"],
        }
        report["lifecycle_events"].insert(7, {
            "event_id": "SUP-EM1",
            "occurred_at": "2026-08-29T09:05:30+08:00",
            "phase": "mediation",
            "actor_role": "mediator",
            "action": "mediation-recorded",
            "status": "completed",
            "summary": "Recorded mediation against the concrete checkpoint.",
            "evidence_refs": [checkpoint_ref],
        })
        self.assertTrue(any("must not be empty" in error for error in self.validate(report)))

    def test_checkpoint_must_bind_run_issues_and_mediation_time(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["issues"] = [{"issue_id": "SUP-001"}]
        checkpoint = self.root / "ppt-supervision-checkpoint.json"
        checkpoint.write_bytes(_json_bytes({
            "checkpoint_version": "1.1",
            "checkpoint_id": "CP-01",
            "run_id": RUN_ID,
            "task_request_sha256": TASK_REQUEST_SHA256,
            "recorded_at": "2026-08-29T09:05:30+08:00",
            "stage": "output-to-supervision",
            "status": "continue",
            "related_issue_ids": ["SUP-001"],
            "conflicts": [{
                "conflict_id": "CF-01",
                "issue_ids": ["SUP-001"],
                "severity": "major",
                "cause": "The final render differs from the approved visual plan.",
                "decision_impact": "The intended management relationship is not visible.",
                "evidence": ["ppt-output-qa.json"],
                "approved_baseline": "Preserve the approved visual hierarchy.",
                "downstream_challenge": "The written slide changed the dominant visual.",
                "alternatives": ["Repair the slide and rerun Output QA."],
                "user_decision": "Continue with a bounded repair.",
            }],
            "questions_for_user": [],
            "assumptions_if_continue": ["Do not change approved business content."],
            "same_conflict_previously_escalated": False,
            "control_returned_to": "root-supervisor",
        }))
        checkpoint_ref = _hashed_ref(self.root, checkpoint.name)
        report["supervisor_roles"]["mediator"] = {
            "status": "complete",
            "summary": "Recorded and mediated the concrete audit finding.",
            "evidence_refs": [checkpoint_ref, "ppt-supervision-report.json#issues"],
        }
        report["lifecycle_events"].insert(7, {
            "event_id": "SUP-EM1",
            "occurred_at": "2026-08-29T09:05:30+08:00",
            "phase": "mediation",
            "actor_role": "mediator",
            "action": "mediation-recorded",
            "status": "completed",
            "summary": "Recorded mediation against the concrete checkpoint.",
            "evidence_refs": [checkpoint_ref],
        })
        self.assertEqual(self.validate(report), [])

        invalid = json.loads(checkpoint.read_text(encoding="utf-8"))
        invalid["related_issue_ids"] = ["SUP-999"]
        checkpoint.write_bytes(_json_bytes(invalid))
        bad_ref = _hashed_ref(self.root, checkpoint.name)
        report["supervisor_roles"]["mediator"]["evidence_refs"][0] = bad_ref
        report["lifecycle_events"][7]["evidence_refs"] = [bad_ref]
        self.assertTrue(any("exactly cover" in error for error in self.validate(report)))

    def test_target_application_pass_requires_a_hash_bound_execution_receipt(self) -> None:
        report = _report(self.pptx, self.report_path)
        receipt = self.root / "output" / "final-reopen-render" / "libreoffice" / "target-application-check.json"
        receipt.write_text("{}", encoding="utf-8")
        report["environment_observation"]["target_applications"][2]["evidence_refs"] = [
            _hashed_ref(self.root, "output/final-reopen-render/libreoffice/target-application-check.json")
        ]
        self.assertTrue(any("target-application receipt" in error for error in self.validate(report)))

    def test_target_application_receipt_time_must_be_current_and_pre_audit(self) -> None:
        receipt = self.root / "output" / "final-reopen-render" / "libreoffice" / "target-application-check.json"
        value = json.loads(receipt.read_text(encoding="utf-8"))
        value["observed_at"] = "1999-01-01T00:00:00+00:00"
        receipt.write_bytes(_json_bytes(value))
        report = _report(self.pptx, self.report_path)
        errors = self.validate(report)
        self.assertTrue(any("run-challenge window" in error for error in errors))
        self.assertTrue(any("between Output handoff and final audit" in error for error in errors))

    def test_wrong_pptx_hash_is_rejected(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["delivery_pair"]["pptx"]["sha256"] = "0" * 64
        self.assertTrue(any("must match the final PPTX" in error for error in self.validate(report)))

    def test_run_and_task_binding_must_match_preflight(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["run_id"] = "run-replayed"
        self.assertTrue(any("report.run_id" in error for error in self.validate(report)))

    def test_direct_api_binding_cannot_authorize_final_delivery(self) -> None:
        preflight = _preflight()
        preflight["run_binding"]["binding_source"] = "direct-api-unattested"
        errors = validate_supervisor_accountability(
            _package(),
            _report(self.pptx, self.report_path),
            self.pptx,
            self.report_path,
            preflight,
            _preflight_digest(),
            RESOLVED_CONFIG,
            RESOLVED_CONFIG_SHA256,
        )
        self.assertTrue(any("script-issued challenge" in error for error in errors))

    def test_self_verified_host_observation_is_rejected(self) -> None:
        preflight = _preflight()
        preflight["dependencies"]["host_tools"]["observation"]["verified"] = True
        errors = validate_supervisor_accountability(
            _package(),
            _report(self.pptx, self.report_path),
            self.pptx,
            self.report_path,
            preflight,
            _preflight_digest(),
            RESOLVED_CONFIG,
            RESOLVED_CONFIG_SHA256,
        )
        self.assertTrue(any("self-verified" in error for error in errors))

    def test_resolved_config_requirements_cannot_be_omitted(self) -> None:
        preflight = _preflight()
        preflight["required_capabilities"] = ["editable-text"]
        errors = validate_supervisor_accountability(
            _package(),
            _report(self.pptx, self.report_path),
            self.pptx,
            self.report_path,
            preflight,
            _preflight_digest(),
            RESOLVED_CONFIG,
            RESOLVED_CONFIG_SHA256,
        )
        self.assertTrue(any("cannot omit resolved-config requirements" in error for error in errors))

    def test_delivery_pair_requires_executable_publisher(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["delivery_pair"]["publisher"] = "manual-handoff"
        self.assertTrue(any("publish_supervised_pair.py" in error for error in self.validate(report)))

    def test_incomplete_evidence_blocks_delivery_pair(self) -> None:
        report = _report(self.pptx, self.report_path)
        report["run_status"] = "incomplete-evidence"
        self.assertTrue(any("expected blocked" in error for error in self.validate(report)))

    def test_publisher_materializes_only_the_validated_pair_and_manifest(self) -> None:
        module = _publisher_module()
        self.report_path.write_text(json.dumps(_report(self.pptx, self.report_path)), encoding="utf-8")
        output_dir = self.root / "published"
        with mock.patch.object(module, "validate_report", return_value=[]):
            manifest = module.publish_supervised_pair(
                package={},
                plan={},
                qa={},
                inventory={},
                report=_report(self.pptx, self.report_path),
                report_path=self.report_path,
                pptx=self.pptx,
                runtime_preflight=_preflight(),
                runtime_preflight_sha256=_preflight_digest(),
                resolved_config=RESOLVED_CONFIG,
                resolved_config_sha256=RESOLVED_CONFIG_SHA256,
                config_path=ROOT / "config" / "default.json",
                output_dir=output_dir,
            )
        self.assertEqual(manifest["required_artifacts"], ["pptx", "supervision-report"])
        self.assertEqual(
            {path.name for path in output_dir.iterdir()},
            {"final.pptx", "ppt-supervision-report.json", "delivery-manifest.json"},
        )
        self.assertEqual(module.validate_published_bundle(output_dir), [])

    def test_publisher_never_materializes_a_failed_report(self) -> None:
        module = _publisher_module()
        self.report_path.write_text("{}", encoding="utf-8")
        output_dir = self.root / "rejected"
        with mock.patch.object(module, "validate_report", return_value=["synthetic validation failure"]):
            with self.assertRaisesRegex(RuntimeError, "synthetic validation failure"):
                module.publish_supervised_pair(
                    package={},
                    plan={},
                    qa={},
                    inventory={},
                    report={"run_id": RUN_ID, "task_request_sha256": TASK_REQUEST_SHA256},
                    report_path=self.report_path,
                    pptx=self.pptx,
                    runtime_preflight=_preflight(),
                    runtime_preflight_sha256=_preflight_digest(),
                    resolved_config=RESOLVED_CONFIG,
                    resolved_config_sha256=RESOLVED_CONFIG_SHA256,
                    config_path=ROOT / "config" / "default.json",
                    output_dir=output_dir,
                )
        self.assertFalse(output_dir.exists())

    def test_personal_publisher_requires_runtime_declared_resolved_config(self) -> None:
        module = _publisher_module()
        bundle = self.root / "personal-bundle"
        expected = bundle / "config" / "personal-extension-resolved.json"
        expected.parent.mkdir(parents=True)
        expected.write_text(json.dumps(RESOLVED_CONFIG), encoding="utf-8")
        runtime_path = bundle / "runtime" / "personal-extension.json"
        runtime_path.parent.mkdir(parents=True)
        runtime_path.write_text(
            json.dumps({"config": {"path": "config/personal-extension-resolved.json"}}),
            encoding="utf-8",
        )
        (runtime_path.parent / "runtime-lock.json").write_text("{}", encoding="utf-8")
        preflight = _preflight()
        with (
            mock.patch.object(module, "ROOT", bundle),
            mock.patch.object(module, "validate_personal_extension_runtime", return_value={}),
        ):
            module.validate_personal_runtime_binding(expected, RESOLVED_CONFIG, preflight)
            with self.assertRaisesRegex(RuntimeError, "requires resolved config"):
                module.validate_personal_runtime_binding(bundle / "config" / "other.json", RESOLVED_CONFIG, preflight)

    def test_personal_publisher_rejects_unbound_preflight_config_path(self) -> None:
        module = _publisher_module()
        bundle = self.root / "personal-bundle"
        expected = bundle / "config" / "personal-extension-resolved.json"
        expected.parent.mkdir(parents=True)
        expected.write_text(json.dumps(RESOLVED_CONFIG), encoding="utf-8")
        runtime_path = bundle / "runtime" / "personal-extension.json"
        runtime_path.parent.mkdir(parents=True)
        runtime_path.write_text(
            json.dumps({"config": {"path": "config/personal-extension-resolved.json"}}),
            encoding="utf-8",
        )
        (runtime_path.parent / "runtime-lock.json").write_text("{}", encoding="utf-8")
        preflight = _preflight()
        preflight["config_binding"]["path"] = "config/other.json"
        with (
            mock.patch.object(module, "ROOT", bundle),
            mock.patch.object(module, "validate_personal_extension_runtime", return_value={}),
        ):
            with self.assertRaisesRegex(RuntimeError, "config_binding.path"):
                module.validate_personal_runtime_binding(expected, RESOLVED_CONFIG, preflight)


if __name__ == "__main__":
    unittest.main()
