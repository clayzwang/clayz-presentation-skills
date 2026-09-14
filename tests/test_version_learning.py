from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
import sys
from unittest import mock
from pathlib import Path

from scripts.bootstrap_owner_learning import VersionLearningError, bootstrap
from scripts.component_version_guard import build_report, build_application_report, main as guard_main, VersionGuardError


ROOT = Path(__file__).resolve().parents[1]


class ComponentVersionGuardTests(unittest.TestCase):
    def test_application_cli_is_offline_and_ignores_development_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            candidate = Path(directory) / "expired.json"
            candidate.write_text('{"expires_at":"2000-01-01T00:00:00Z"}', encoding="utf-8")
            with mock.patch("urllib.request.urlopen", side_effect=AssertionError("authoring must not use network")), mock.patch.object(
                sys, "argv", ["guard", "--candidate-manifest-json", str(candidate), "--output", str(output)]
            ):
                self.assertEqual(guard_main(), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "installed")
            self.assertIsNone(report["latest_release"])
            from scripts.runtime_preflight import _validate_component_version_report
            from packages.runtime.preflight import _component_version_gate
            config = json.loads((ROOT / "config/default.json").read_text(encoding="utf-8"))
            gate = _validate_component_version_report(output, config)
            self.assertEqual(_component_version_gate(config, gate)["status"], "installed")
            report["components"][0]["actual_version"] = "999.0.0"
            output.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                _validate_component_version_report(output, config)

    def test_application_does_not_consult_newer_or_older_official_release(self) -> None:
        for remote_version in ("0.8.0", "99.0.0"):
            with self.subTest(remote=remote_version), mock.patch(
                "scripts.component_version_guard.fetch_official_latest", return_value={"version": remote_version}
            ) as remote:
                report = build_application_report(ROOT)
                self.assertEqual(report["status"], "installed")
                remote.assert_not_called()

    def test_application_still_rejects_internal_drift_and_incomplete_table(self) -> None:
        from scripts.component_version_guard import _collect_actual
        actual, personal = _collect_actual(ROOT)
        with mock.patch("scripts.component_version_guard._collect_actual", return_value=({**actual, "copy-package": "999.0"}, personal)):
            self.assertEqual(build_application_report(ROOT)["status"], "blocked")
        with mock.patch("scripts.component_version_guard._collect_actual", return_value=({**actual, "unexpected": "1.0"}, personal)):
            with self.assertRaises(VersionGuardError):
                build_application_report(ROOT)
        with mock.patch("scripts.component_version_guard._collect_actual", return_value=(actual, {"core_version": "99.0.0"})):
            self.assertIn("PERSONAL_RUNTIME_VERSION_DRIFT", build_application_report(ROOT)["error_codes"])

    def _official_manifest(self) -> dict[str, object]:
        return json.loads((ROOT / "config" / "component-versions.json").read_text(encoding="utf-8"))

    def test_current_release_and_every_component_are_reported(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        report = build_report(ROOT, {
            "version": version,
            "tag_name": f"v{version}",
            "html_url": f"https://github.com/clayzwang/clayz-presentation-skills/releases/tag/v{version}",
            "observed_at": "2026-09-01T00:00:00+00:00",
            "source": "official-host-fetched-github-response",
        }, self._official_manifest())
        self.assertEqual(report["status"], "latest")
        self.assertEqual(report["error_codes"], [])
        self.assertGreaterEqual(len(report["components"]), 10)
        self.assertTrue(all(item["status"] == "current" for item in report["components"]))

    def test_non_latest_release_fails_closed(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        report = build_report(ROOT, {
            "version": "1.0.0",
            "tag_name": "v1.0.0",
            "html_url": "https://github.com/clayzwang/clayz-presentation-skills/releases/tag/v1.0.0",
            "observed_at": "2026-09-01T00:00:00+00:00",
            "source": "official-host-fetched-github-response",
        }, {**self._official_manifest(), "release_version": "1.0.0"})
        self.assertEqual(report["status"], "blocked")
        self.assertIn("NON_LATEST_COMPONENT", report["error_codes"])

    def test_newer_candidate_requires_hash_bound_staged_manifest(self) -> None:
        local = self._official_manifest()
        candidate = {
            "contract": "io.clayz.presentation.component-candidate-manifest/1.0",
            "repository": "clayzwang/clayz-presentation-skills",
            "status": "staged-candidate",
            "candidate_version": local["release_version"],
            "base_latest_version": "0.8.0",
            "candidate_commit": "a" * 40,
            "component_manifest_sha256": hashlib.sha256((ROOT / "config" / "component-versions.json").read_bytes()).hexdigest(),
            "expires_at": "2099-01-01T00:00:00+00:00",
        }
        official = json.loads(json.dumps(local))
        official["release_version"] = "0.8.0"
        for key in ("public-core", "plugin-manifest", "central-config"):
            official["components"][key] = "0.8.0"
        report = build_report(ROOT, {
            "version": "0.8.0", "tag_name": "v0.8.0",
            "html_url": "https://github.com/clayzwang/clayz-presentation-skills/releases/tag/v0.8.0",
            "observed_at": "2026-09-01T00:00:00+00:00",
            "source": "official-host-fetched-github-response",
        }, official, candidate)
        self.assertEqual(report["status"], "candidate")
        self.assertEqual(report["error_codes"], [])


class VersionPrivateLearningTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[dict[str, object], dict[str, Path]]:
        specs = [
            ("knowledge", "private-knowledge"),
            ("template", "template"),
            ("standard", "standard"),
            ("method", "method"),
        ]
        sources = []
        bindings: dict[str, Path] = {}
        for source_id, kind in specs:
            path = root / f"{source_id}.jsonl"
            path.write_text(json.dumps({
                "title": f"{kind} title",
                "summary": f"substantive {kind} content",
                "purpose_tags": [kind],
            }) + "\n", encoding="utf-8")
            bindings[source_id] = path
            sources.append({
                "source_id": source_id,
                "library_uri": f"library://example-presentation/{source_id}.jsonl",
                "format": "jsonl",
                "record_type": "knowledge" if kind == "private-knowledge" else "reference",
                "stages": ["logic", "copy", "art-direction", "output", "supervisor"],
                "required": True,
                "purpose_tags": ["version-learning-test"],
                "knowledge_kinds": [kind],
            })
        return {
            "contract": "io.clayz.presentation.owner-learning-sources/1.0",
            "provider_id": "task-private-learning",
            "inventory_uri": "runtime-input://synthetic-inventory",
            "admission_basis": "synthetic admitted owner learning",
            "sources": sources,
        }, bindings

    def test_first_run_builds_audited_index_and_second_run_reuses_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, bindings = self._fixture(root)
            state_root = root / "state"
            first = bootstrap(manifest, bindings, core_version="0.7.1", state_root=state_root)
            second = bootstrap(manifest, bindings, core_version="0.7.1", state_root=state_root)
            self.assertEqual(first["mode"], "first-run")
            self.assertEqual(second["mode"], "reused-version-index")
            self.assertEqual(first["learning_key"], second["learning_key"])
            self.assertEqual(first["audit_sha256"], second["audit_sha256"])
            audit = json.loads(Path(first["audit_path"]).read_text(encoding="utf-8"))
            self.assertEqual(audit["status"], "complete")
            self.assertEqual(audit["missing_knowledge_kinds"], [])
            self.assertTrue(all(probe["status"] == "pass" for probe in audit["retrieval_probes"]))

    def test_source_change_creates_revision_and_reuses_unchanged_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, bindings = self._fixture(root)
            state_root = root / "state"
            first = bootstrap(manifest, bindings, core_version="0.7.1", state_root=state_root)
            bindings["method"].write_text('{"title":"changed","summary":"changed method"}\n', encoding="utf-8")
            second = bootstrap(manifest, bindings, core_version="0.7.1", state_root=state_root)
            self.assertNotEqual(first["learning_key"], second["learning_key"])
            self.assertTrue(Path(first["audit_path"]).is_file())
            audit = json.loads(Path(second["audit_path"]).read_text(encoding="utf-8"))
            materialization = json.loads(Path(audit["index"]["materialization_report"]).read_text(encoding="utf-8"))
            states = {x["source_id"]: x["cache_status"] for x in materialization["materialized_sources"]}
            self.assertEqual(states["method"], "parsed")
            self.assertEqual(sum(value == "reused" for value in states.values()), len(states) - 1)


if __name__ == "__main__":
    unittest.main()
