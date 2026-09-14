"""Stage-record handoff/assembly tests; synthetic files do not claim visual QA."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from packages.runtime.preflight import issue_run_challenge
from packages.validators.stage_work_records import create_record, validate_records, canonical_record_sha256, STAGES

ROOT = Path(__file__).resolve().parents[1]


class WorkRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.challenge = issue_run_challenge(b"Synthetic record test", task_root=self.root)
        spec = importlib.util.spec_from_file_location("record_publisher_test", ROOT / "scripts/publish_supervised_pair.py")
        self.publisher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.publisher)
        self.paths = {}
        legacy_config = json.loads((ROOT / "config/default.json").read_text(encoding="utf-8"))
        # Historical assembly tests exercise the pre-3.5 collector only.  Use
        # an explicit legacy delivery policy so the calibrated default cannot
        # be silently bypassed by a compatibility fixture.
        legacy_config["workflow"]["delivery_policy"]["mode"] = "legacy"
        for role, value in {
            "logic": {"brief": {"purpose": "synthetic"}, "logic_layer": {}},
            "package": {"brief": {"purpose": "synthetic"}, "logic_layer": {}, "copy_layer": {},
                        "package_id": "test", "version": "1", "origin_namespace": "io.clayz.presentation"},
            "plan": {}, "qa": {}, "inventory": {}, "config": legacy_config,
            "runtime_preflight": {"run_binding": self.challenge},
            "supervisor_draft": {"run_status": "clean", "deck_findings": ["synthetic test only"]},
        }.items():
            self.paths[role] = self.write(role + ".json", value)
        self.paths["pptx"] = self.root / "test.pptx"
        self.paths["pptx"].write_bytes(b"synthetic fixture; not a valid presentation")
        self.render = self.root / "render.txt"
        self.render.write_text("synthetic render evidence, not an actual rendering")
        self.records = []
        self.record_paths = []
        roles = [{"package": self.paths["logic"]}, {"package": self.paths["package"]},
                 {"plan": self.paths["plan"]}, {k: self.paths[k] for k in ("qa", "inventory", "pptx")},
                 {"draft": self.paths["supervisor_draft"], "pptx": self.paths["pptx"]}]
        roles[3]["render-1"] = self.render
        for stage, artifacts in zip(STAGES, roles):
            draft = {"summary": "Synthetic " + stage, "decisions": ["Fixture decision"],
                     "checks": [{"name": "Fixture check", "status": "pass", "evidence_roles": list(artifacts)}],
                     "open_issues": []}
            record = create_record(stage, draft, self.challenge, artifacts, self.records[-1] if self.records else None)
            self.records.append(record)
            self.record_paths.append(self.write(stage + "-record.json", record))

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def validate(self, records=None):
        validate_records(self.records if records is None else records, self.challenge["run_id"], self.challenge["task_request_sha256"])

    def assemble_args(self):
        args = ["assemble-report"]
        for path in self.record_paths:
            args += ["--record", str(path)]
        for flag, role in (("draft", "supervisor_draft"), ("package", "package"), ("plan", "plan"),
                           ("qa", "qa"), ("inventory", "inventory"), ("pptx", "pptx"),
                           ("runtime-preflight", "runtime_preflight"), ("config", "config")):
            args += ["--" + flag, str(self.paths[role])]
        return args + ["--output", str(self.root / "report.json")]

    def test_five_actual_file_records_pass(self):
        self.validate()
        self.assertEqual(len(self.records), 5)

    def test_handoff_verifies_available_prefix_and_rejects_wrong_order(self):
        challenge = self.write("challenge.json", self.challenge)
        args = ["check-records", "--challenge", str(challenge)]
        for path in self.record_paths[:2]:
            args += ["--record", str(path)]
        self.assertEqual(self.publisher._record_commands(args), 0)
        self.assertEqual(self.publisher._record_commands(["check-records", "--challenge", str(challenge), "--record", str(self.record_paths[1])]), 1)

    def test_record_cli_exclusive_output_and_real_hash(self):
        draft = self.write("record-draft.json", {"summary": "Read and organized source material", "checks": [{"name": "source inspected", "status": "pass", "evidence_roles": ["package"]}]})
        challenge = self.write("record-challenge.json", self.challenge)
        output = self.root / "cli-record.json"
        args = ["record-stage", "--stage", "logic", "--draft", str(draft), "--challenge", str(challenge),
                "--artifact", "package=" + str(self.paths["logic"]), "--output", str(output)]
        self.assertEqual(self.publisher._record_commands(args), 0)
        self.assertEqual(json.loads(output.read_text())["artifacts"]["package"]["sha256"], self.publisher.sha256_file(self.paths["logic"]))
        self.assertEqual(self.publisher._record_commands(args), 1)

    def test_missing_duplicate_reordered_records_rejected(self):
        for records in (self.records[:4], self.records + [self.records[-1]], list(reversed(self.records))):
            with self.subTest(count=len(records)), self.assertRaises(ValueError):
                self.validate(records)

    def test_changed_file_and_changed_record_rejected(self):
        mutated = copy.deepcopy(self.records)
        mutated[0]["summary"] = "Altered without doing the work"
        with self.assertRaises(ValueError):
            self.validate(mutated)
        self.paths["pptx"].write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.validate()

    def test_other_task_and_stale_predecessor_rejected(self):
        changed = copy.deepcopy(self.records)
        changed[2]["previous_record_sha256"] = "a" * 64
        changed[2]["record_sha256"] = canonical_record_sha256(changed[2])
        with self.assertRaises(ValueError):
            self.validate(changed)
        with self.assertRaises(ValueError):
            validate_records(self.records, "different-run", self.challenge["task_request_sha256"])

    def test_failure_is_recordable_but_cannot_handoff_or_publish(self):
        draft = {"summary": "Found problem", "checks": [{"name": "visible defect", "status": "fail", "evidence_roles": ["package"]}], "open_issues": ["fix required"]}
        record = create_record("logic", draft, self.challenge, {"package": self.paths["logic"]})
        with self.assertRaises(ValueError):
            create_record("copy", draft, self.challenge, {"package": self.paths["package"]}, record)

    def test_summary_cannot_be_assembled_as_a_valid_report(self):
        self.assertEqual(self.publisher._record_commands(self.assemble_args()), 1)
        self.assertFalse((self.root / "report.json").exists())

    def test_assembly_is_deterministic_collection_not_semantic_qa(self):
        # Isolate collection mechanics only; the preceding test uses the real validator.
        with mock.patch.object(self.publisher, "validate_report", return_value=[]), mock.patch.object(self.publisher, "REPORT_REQUIRED_FIELDS", set()):
            self.assertEqual(self.publisher._record_commands(self.assemble_args()), 0)
        path = self.root / "report.json"
        report = json.loads(path.read_text())
        self.assertEqual(report["work_records"], self.records)
        self.assertEqual(report["package_version"], "1")
        self.publisher.validate_work_record_assembly(report, self.paths["pptx"])
        report["deck_findings"] = ["Rewritten success"]
        with self.assertRaises(ValueError):
            self.publisher.validate_work_record_assembly(report, self.paths["pptx"])
        with self.assertRaises(FileExistsError):
            self.publisher._write_new(path, {})

    def test_new_runtime_rejects_manual_report_before_publication(self):
        report_path = self.write("manual.json", {"run_id": self.challenge["run_id"]})
        with mock.patch.object(self.publisher, "_records_required", return_value=True), self.assertRaises(ValueError):
            self.publisher.publish_supervised_pair(package={}, plan={}, qa={}, inventory={},
                report=json.loads(report_path.read_text()), report_path=report_path, pptx=self.paths["pptx"],
                runtime_preflight={}, runtime_preflight_sha256="a"*64, resolved_config={},
                resolved_config_sha256="b"*64, config_path=self.paths["config"], output_dir=self.root/"delivered")
        self.assertFalse((self.root/"delivered").exists())


if __name__ == "__main__":
    unittest.main()
