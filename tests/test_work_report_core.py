"""Focused tests for the source-bound 3.6 work-report core."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from packages.validators.work_report import (
    PARTIAL_STATUS,
    WORK_REPORT_CONTRACT,
    WORK_REPORT_VERSION,
    artifact_snapshot,
    attach_work_report,
    canonical_sha256,
    inspect_pptx,
    render_work_report_markdown,
    validate_work_report,
)


class WorkReportCoreTests(unittest.TestCase):
    def test_snapshots_keep_json_and_text_but_only_metadata_for_binary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text('{"facts":["kept"],"order":2}\n', encoding="utf-8")
            note = root / "work-notes.md"
            note.write_text("full note\nwith a second line", encoding="utf-8")
            binary = root / "asset.bin"
            binary.write_bytes(b"\x00\xff\x01")
            json_snapshot = artifact_snapshot(source, role="package")
            text_snapshot = artifact_snapshot(note, role="work-notes")
            binary_snapshot = artifact_snapshot(binary, role="pptx")
            self.assertEqual(json_snapshot["content"]["facts"], ["kept"])
            self.assertEqual(json_snapshot["raw_text"], source.read_bytes().decode("utf-8-sig"))
            self.assertEqual(text_snapshot["content"], note.read_bytes().decode("utf-8-sig"))
            self.assertNotIn("content", binary_snapshot)
            self.assertEqual(binary_snapshot["content_status"], "metadata-only")

    def test_real_pptx_observation_has_slide_scope_and_title_source(self) -> None:
        from tests.calibrated_audit_fixtures import build_minimal_pptx

        with tempfile.TemporaryDirectory() as directory:
            pptx = build_minimal_pptx(Path(directory) / "deck.pptx")
            observed = inspect_pptx(pptx)
            self.assertEqual(observed["slide_count"], 1)
            self.assertEqual(observed["scope"]["slide_content"], "slide XML parts only")
            self.assertIn(observed["title_source"], {"cover-slide-first-text-candidate", "cover-slide-declared-title", "core-properties"})
            self.assertEqual(observed["media"]["media_count"], 0)
            self.assertEqual(observed["totals"]["pictures"], 0)

    def test_attached_report_is_deterministic_and_preserves_notes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "package.json"
            package.write_text(json.dumps({"logic_layer": {"sources": ["source-a"], "open_items": []}, "copy_layer": {"slides": []}}), encoding="utf-8")
            notes = root / "work-notes.md"
            notes.write_text("The full stage note is retained.", encoding="utf-8")
            notes_binding = {"path": str(notes.resolve()), "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(), "bytes": notes.stat().st_size}
            report = attach_work_report(
                {"run_id": "run-1", "task_request_sha256": "a" * 64},
                artifacts={"package": package},
                records=[{"stage": "copy", "artifacts": {"work-notes": notes_binding}}],
            )
            work = report["work_report"]
            self.assertEqual(work["contract"], WORK_REPORT_CONTRACT)
            self.assertEqual(work["version"], WORK_REPORT_VERSION)
            self.assertEqual(work["copy"]["notes"][0]["text"], notes.read_text(encoding="utf-8"))
            self.assertEqual(report["work_report_sha256"], canonical_sha256(work))
            self.assertEqual(validate_work_report(report), [])
            markdown = render_work_report_markdown(report)
            self.assertIn(report["work_report_sha256"], markdown)

    def test_partial_invalid_pptx_is_disclosed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pptx = root / "invalid.pptx"
            pptx.write_bytes(b"not an OOXML package")
            report = attach_work_report(
                {"run_id": "run-1", "task_request_sha256": "a" * 64},
                artifacts={"pptx": pptx},
                pptx=pptx,
            )
            self.assertEqual(report["work_report"]["actual_pptx"]["status"], PARTIAL_STATUS)
            self.assertEqual(validate_work_report(report, pptx=pptx), [])

    def test_verify_handoff_rejects_rehashed_report_without_top_level_assembly(self) -> None:
        """A self-consistent JSON/Markdown/manifest is still not a full handoff."""

        from tests.test_work_report_adversarial import _ReportRun, _read_json

        fixture = _ReportRun(subject="alpha", rich=True)
        try:
            stages = fixture.build_records_and_audit()
            bundle = fixture.publish(stages)
            report_path = bundle / "ppt-supervision-report.json"
            report = _read_json(report_path)
            report.pop("work_records", None)
            report.pop("assembly", None)
            report["work_report_sha256"] = canonical_sha256(report["work_report"])
            report_raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            report_path.write_bytes(report_raw)
            markdown_path = bundle / "work-report.md"
            markdown_raw = markdown_path.read_bytes()
            manifest_path = bundle / "delivery-manifest.json"
            manifest = _read_json(manifest_path)
            for item in manifest["files"]:
                if item.get("role") == "supervision-report":
                    item["sha256"] = hashlib.sha256(report_raw).hexdigest()
                    item["bytes"] = len(report_raw)
            for item in manifest["derived_files"]:
                if item.get("role") == "work-report-markdown":
                    item["sha256"] = hashlib.sha256(markdown_raw).hexdigest()
                    item["bytes"] = len(markdown_raw)
            manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
            result = fixture.verify(bundle, expected=1)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("assembly", (result.stdout + result.stderr).casefold())
        finally:
            fixture.close()

    def test_json_key_order_roundtrip_preserves_work_report_validation(self) -> None:
        from tests.test_work_report_adversarial import _ReportRun, _read_json

        fixture = _ReportRun(subject="alpha", rich=True)
        try:
            stages = fixture.build_records_and_audit()
            bundle = fixture.publish(stages)
            report = _read_json(bundle / "ppt-supervision-report.json")
            reordered = json.loads(json.dumps(report, ensure_ascii=False, sort_keys=True))
            self.assertEqual(validate_work_report(reordered, pptx=fixture.case.pptx), [])
        finally:
            fixture.close()

    def test_assembled_report_cannot_hide_empty_snapshots_and_refs(self) -> None:
        from tests.test_work_report_adversarial import _ReportRun, _read_json

        fixture = _ReportRun(subject="alpha", rich=True)
        try:
            stages = fixture.build_records_and_audit()
            bundle = fixture.publish(stages)
            report_path = bundle / "ppt-supervision-report.json"
            report = _read_json(report_path)
            work = report["work_report"]
            work["source_snapshots"] = []
            work["stage_record_refs"] = []
            work["stage_artifact_bindings"] = []
            for key in ("task", "substantive_content", "copy", "art_direction", "calibrations", "supervisor_reviews", "auditor", "release"):
                work[key] = {}
            report["work_report_sha256"] = canonical_sha256(work)
            report_raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            report_path.write_bytes(report_raw)
            markdown_path = bundle / "work-report.md"
            markdown_raw = render_work_report_markdown(report).encode("utf-8")
            markdown_path.write_bytes(markdown_raw)
            manifest_path = bundle / "delivery-manifest.json"
            manifest = _read_json(manifest_path)
            for item in manifest["files"]:
                if item.get("role") == "supervision-report":
                    item["sha256"] = hashlib.sha256(report_raw).hexdigest()
                    item["bytes"] = len(report_raw)
            for item in manifest["derived_files"]:
                if item.get("role") == "work-report-markdown":
                    item["sha256"] = hashlib.sha256(markdown_raw).hexdigest()
                    item["bytes"] = len(markdown_raw)
            manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
            result = fixture.verify(bundle, expected=1)
            self.assertNotEqual(result.returncode, 0)
            self.assertRegex((result.stdout + result.stderr).casefold(), "source|snapshot|record|assembly")
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
