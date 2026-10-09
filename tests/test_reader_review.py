"""Synthetic reader/host observations test transport, not language quality."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, PngImagePlugin
from packages.validators import reader_review as rr
from tests.calibrated_audit_fixtures import build_minimal_pptx

ROOT = Path(__file__).resolve().parents[1]


class ReaderReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.package = self.put("copy.json", {
            "run_binding": {"run_id": "reader-test", "task_request_sha256": "a" * 64},
            "research": {"private": "HIDDEN-AUTHOR-ANSWER"},
            "copy_layer": {"semantic_preservation_review": "HIDDEN-AUTHOR-APPROVAL", "slides": [{
                "slide_id": "S01", "speaker_notes": ["HIDDEN-SPEAKER-NOTES"],
                "content_relationships": {"purpose": "HIDDEN-DESIGN-INTENT"},
                "copy_units": [
                    {"copy_id": "T", "role": "title", "text": "The two regions have different rules"},
                    {"copy_id": "B", "role": "body", "text": "Region A publishes a payment deadline; region B describes timing principles."},
                    {"copy_id": "A", "role": "annotation", "text": "Synthetic example; other rules are unknown."}
                ]}]}})
        self.brief = self.put("brief.json", {"audience": "A new reader", "purpose": "Understand the rules", "task": "Explain this synthetic comparison"})
        self.pptx = build_minimal_pptx(self.root / "actual.pptx")
        image = Image.new("RGB", (120, 90), "purple")
        meta = PngImagePlugin.PngInfo()
        meta.add_text("AuthorRationale", "HIDDEN-PNG-NOTES")
        self.png = self.root / "render.png"
        image.save(self.png, pnginfo=meta)
        self.renders = self.put("renders.json", {"pptx_sha256": rr.ref(self.pptx)["sha256"],
            "slides": [{"slide_id": "S01", **rr.ref(self.png)}]})

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def packet(self, phase="copy", name=None):
        name = name or phase
        path = self.root / f"{name}-packet.json"
        rr.prepare_packet(phase=phase, package=self.package, brief=self.brief,
            directory=self.root / f"{name}-input", output=path,
            pptx=self.pptx if phase == "final" else None, renders=self.renders if phase == "final" else None)
        return path

    def context(self, packet, name, shared=False):
        manifest = rr.read(packet)
        raw = self.put(name + "-raw-host.json", {"synthetic_test_fixture": True, "tool": "fixture-dispatch", "context": name})
        receipt = self.put(name + "-host.json", {"host_tool": "fixture-dispatch",
            "context_id": name, "production_context_id": "author", "history_inherited": False,
            "access_scope": "instruction-only", "input_files": [manifest["input"], *manifest["assets"]], "raw_receipt": rr.ref(raw)})
        return self.put(name + "-context.json", {"execution_mode": "same-context-limited" if shared else "same-model-new-context",
            "context_id": "author" if shared else name, "production_context_id": "author", "history_inherited": shared,
            "access_scope": "instruction-only", "host_receipt": None if shared else rr.ref(receipt),
            "limitations": ["Synthetic regression fixture; no real host or reader was invoked."]})

    def response(self, gaps=False):
        return {"assessment": "understanding-gaps" if gaps else "understood",
            "title_reading": "The title announces a difference without identifying it.",
            "understanding": [{"question": "What differs?", "answer": "A states a deadline; B describes timing principles.",
                "slide_ids": ["S01"], "visible_evidence": "payment deadline; timing principles", "uncertainty": "Other requirements are unknown."}],
            "findings": [{"finding_id": "TITLE-ANSWER", "slide_ids": ["S01"], "copy_ids": ["T"],
                "statement": "The title does not state the available difference.", "reader_impact": "Titles alone do not answer the comparison."}] if gaps else []}

    def review(self, phase="copy", *, gaps=False, shared=False, not_run=False, name=None, previous=()):
        name = name or phase
        packet = self.packet(phase, name)
        context = self.context(packet, name, shared)
        response = None if not_run else self.put(name + "-response.json", self.response(gaps))
        first = self.root / (name + "-first.json")
        rr.record_first(packet=packet, context=context, response=response, reason="Unavailable in synthetic test" if not_run else None, output=first)
        dispositions = [{"finding_id": "TITLE-ANSWER", "owner_layer": "copy", "status": "open",
                         "explanation": "Promote the supported comparison into the title.", "evidence_refs": [rr.ref(self.package)]}] if gaps else []
        path = self.root / (name + "-review.json")
        rr.record_review(first_read=first, dispositions=self.put(name + "-dispositions.json", dispositions),
                         evidence=[self.package], output=path, previous_reviews=list(previous))
        return path

    def audit(self, reviews):
        return {"run_id": "reader-test", "task_request_sha256": "a" * 64,
                "final_pptx": rr.ref(self.pptx), "audited_at": rr.now(),
                "source_records": [{"kind": "package", **rr.ref(self.package)}, *[
                    {"kind": "reader-review-" + phase, **rr.ref(path)} for phase, path in reviews.items()]]}

    def test_copy_projection_excludes_author_evidence_preserves_visible_qualifier(self):
        packet = rr.read(self.packet())
        payload = rr.validate_packet(packet)
        text = json.dumps(payload)
        self.assertNotIn("HIDDEN", text)
        self.assertIn("other rules are unknown", text)
        self.assertEqual(set(payload), {"brief", "instruction", "pages"})

    def test_declared_hidden_fields_or_extra_input_files_are_rejected(self):
        packet = rr.read(self.packet())
        payload = rr.load_ref(packet["input"])
        payload["author_answer"] = "An injected answer"
        self.put("copy-input/reader-input.json", payload)
        packet["input"] = rr.ref(self.root / "copy-input/reader-input.json")
        with self.assertRaisesRegex(ValueError, "unauthorized"):
            rr.validate_packet(packet)
        packet = rr.read(self.packet(name="clean"))
        self.put("clean-input/private.json", {"notes": "excluded"})
        with self.assertRaisesRegex(ValueError, "undeclared"):
            rr.validate_packet(packet)

    def test_final_images_are_exact_pixels_without_metadata(self):
        packet = rr.read(self.packet("final"))
        payload = rr.validate_packet(packet)
        self.assertNotIn("text", payload["pages"][0])
        with Image.open(packet["assets"][0]["path"]) as image:
            self.assertEqual(image.info, {})
            self.assertEqual(image.tobytes(), Image.open(self.png).tobytes())

    def test_final_wrong_pptx_or_missing_page_is_rejected(self):
        render = rr.read(self.renders)
        render["pptx_sha256"] = "b" * 64
        self.put("renders.json", render)
        with self.assertRaisesRegex(ValueError, "different PPTX"):
            self.packet("final")
        render["pptx_sha256"] = rr.ref(self.pptx)["sha256"]
        render["slides"] = []
        self.put("renders.json", render)
        with self.assertRaisesRegex(ValueError, "every page"):
            self.packet("final", name="missing")

    def test_inherited_history_and_fabricated_context_label_are_rejected(self):
        packet = self.packet()
        context_path = self.context(packet, "reader")
        context = rr.read(context_path)
        context["history_inherited"] = True
        with self.assertRaisesRegex(ValueError, "inherit"):
            rr.validate_context(context, rr.read(packet))
        context["history_inherited"] = False
        context["host_receipt"] = None
        with self.assertRaises(ValueError):
            rr.validate_context(context, rr.read(packet))

    def test_shared_context_and_not_run_cannot_become_quality_passes(self):
        path = self.review(shared=True)
        self.assertEqual("incomplete-evidence", rr.reader_status(rr.audit_reviews(self.audit({"copy": path}))))
        path = self.review("final", not_run=True)
        value = rr.validate_review(rr.read(path))
        self.assertEqual("not-run", value["assessment"])
        self.assertIsNone(value["first_read"]["response"])

    def test_frozen_first_read_cannot_be_rewritten_during_reconciliation(self):
        path = self.review(gaps=True)
        value = rr.read(path)
        first = rr.load_ref(value["first_read"])
        first["response"]["findings"] = []
        self.put("copy-first.json", first)
        with self.assertRaisesRegex(ValueError, "bound bytes"):
            rr.validate_review(value)

    def test_findings_cannot_disappear_or_be_resolved_on_old_bytes(self):
        value = rr.read(self.review(gaps=True))
        saved = copy.deepcopy(value)
        value["dispositions"] = []
        with self.assertRaisesRegex(ValueError, "every first-read finding"):
            rr.validate_review(value)
        saved["dispositions"][0]["status"] = "resolved"
        with self.assertRaisesRegex(ValueError, "new reading"):
            rr.validate_review(saved)

    def test_stale_review_and_late_copy_review_are_rejected(self):
        path = self.review()
        with self.assertRaisesRegex(ValueError, "stale"):
            rr.validate_review(rr.read(path), package_sha256="b" * 64)
        with self.assertRaisesRegex(ValueError, "precede Copy-to-Art"):
            rr.validate_copy_review_order(self.audit({"copy": path}), {"recorded_at": "2020-01-01T00:00:00Z"})

    def test_current_policy_requires_both_reviews_and_distinct_contexts(self):
        with self.assertRaisesRegex(ValueError, "reader-review-copy"):
            rr.audit_reviews(self.audit({}), required=True)
        a, b = self.review(), self.review("final")
        self.assertEqual({"copy", "final"}, set(rr.audit_reviews(self.audit({"copy": a, "final": b}), required=True)))
        # Pointing final at a Copy review cannot fake the second checkpoint.
        with self.assertRaisesRegex(ValueError, "binding"):
            rr.audit_reviews(self.audit({"copy": a, "final": a}), required=True)

    def test_previous_findings_remain_linked_after_new_review(self):
        before = self.review(gaps=True, name="before")
        after = self.review(name="after", previous=[before])
        result = rr.validate_review(rr.read(after))
        prior = rr.load_ref(result["review"]["previous_reviews"][0])
        self.assertEqual("TITLE-ANSWER", rr.load_ref(prior["first_read"])["response"]["findings"][0]["finding_id"])

    def test_missing_final_renders_can_be_disclosed_without_fabrication(self):
        packet = self.root / "unavailable.json"
        rr.prepare_packet(phase="final", package=self.package, brief=self.brief, directory=self.root / "unavailable-input",
                          output=packet, pptx=self.pptx, unavailable_reason="No native renderer in synthetic fixture")
        context = self.context(packet, "unavailable", shared=True)
        with self.assertRaisesRegex(ValueError, "without final renders"):
            rr.record_first(packet=packet, context=context, response=self.put("response.json", self.response()), output=self.root / "invalid.json")
        rr.record_first(packet=packet, context=context, reason="No render", output=self.root / "not-run.json")

    def test_cli_and_report_preserve_actual_reader_observations(self):
        path = self.review(gaps=True)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/reader_review.py"), "validate", str(path)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("understanding-gaps", json.loads(result.stdout)["assessment"])
        from packages.validators.work_report import _auditor, _render_auditor
        audit = self.audit({"copy": path})
        section = _auditor(audit, {}, snapshots=[], ids=set())
        lines = []
        _render_auditor(lines, {"auditor": section})
        output = "\n".join(lines)
        self.assertIn("Titles alone do not answer", output)
        self.assertIn("Promote the supported comparison", output)
        self.assertIn("instruction-only", output)

    def test_final_audit_collects_reader_findings_and_rejects_their_removal(self):
        from tests.test_calibrated_audit import CalibratedAuditTests
        from tests.calibrated_audit_fixtures import build_synthetic_pixel_render
        from packages.validators.independent_audit import (create_auditor_artifact,
            validate_auditor_artifact, canonical_record_sha256, IndependentAuditError)
        fixture = self.root / "audit-fixture"
        fixture.mkdir()
        task, acceptance, rules, sources = CalibratedAuditTests()._fixtures(fixture)
        package = rr.read(self.package)
        package["run_binding"]["task_request_sha256"] = rr.ref(task)["sha256"]
        self.put("copy.json", package)
        sources["package"] = self.package
        sources["reader-review-copy"] = self.review(gaps=True)
        sources["reader-review-final"] = self.review("final", not_run=True)
        render = build_synthetic_pixel_render(self.root / "audit-render.png", label="synthetic reader regression")
        coverage = {"hard_requirement_ids": ["content"], "soft_requirement_ids": ["visual"],
            "requirements": [{"requirement_id": name, "classification": level, "status": "pass",
                              "evidence_refs": [f"package sha256={rr.ref(self.package)['sha256']}"], "observation": "Synthetic audit transport fixture"}
                             for name, level in [("content", "hard"), ("visual", "soft")]],
            "rules": [{"rule_id": name, "source": source, "status": "pass",
                       "evidence_refs": [f"package sha256={rr.ref(self.package)['sha256']}"], "observation": "Synthetic fixture"}
                      for name, source in [("fixed-1", "fixed_commitment"), ("change-1", "explicit_change")]],
            "render_status": "complete"}
        audit = create_auditor_artifact(task_request=task, acceptance_rules=acceptance, supervisor_rules=rules,
            source_records=sources, expected_source_kinds=list(sources), final_pptx=self.pptx,
            render_evidence={"synthetic-render": render}, coverage=coverage,
            independent_context={"execution_mode": "same-context-limited", "context_id": "fixture",
                "model_identity_disclosure": "not-attested", "limitations": ["Synthetic test, not a reader effectiveness experiment"]},
            run_id="reader-test", task_request_sha256=rr.ref(task)["sha256"])
        self.assertEqual("incomplete-evidence", audit["audit_status"])
        self.assertEqual("READER-copy-TITLE-ANSWER", audit["findings"][0]["finding_id"])
        validate_auditor_artifact(audit)
        audit["findings"] = []
        audit["record_sha256"] = canonical_record_sha256(audit)
        with self.assertRaisesRegex(IndependentAuditError, "reader finding"):
            validate_auditor_artifact(audit)

    def test_final_reader_cannot_reuse_the_copy_reader_context(self):
        a, b = self.review(), self.review("final")
        final_review = rr.read(b)
        first = rr.load_ref(final_review["first_read"])
        context = first["context"]
        receipt = rr.load_ref(context["host_receipt"])
        context["context_id"] = receipt["context_id"] = "copy"
        host_path = self.put("final-host.json", receipt)
        context["host_receipt"] = rr.ref(host_path)
        first_path = self.put("final-first.json", first)
        final_review["first_read"] = rr.ref(first_path)
        self.put("final-review.json", final_review)
        with self.assertRaisesRegex(ValueError, "new context"):
            rr.audit_reviews(self.audit({"copy": a, "final": b}), required=True)


if __name__ == "__main__":
    unittest.main()
