from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_owner_learning import VersionLearningError, bootstrap
from scripts.component_version_guard import build_report


ROOT = Path(__file__).resolve().parents[1]


class ComponentVersionGuardTests(unittest.TestCase):
    def _official_manifest(self) -> dict[str, object]:
        return json.loads((ROOT / "config" / "component-versions.json").read_text(encoding="utf-8"))

    def test_current_release_and_every_component_are_reported(self) -> None:
        report = build_report(ROOT, {
            "version": "0.8.0",
            "tag_name": "v0.8.0",
            "html_url": "https://github.com/clayzwang/clayz-presentation-skills/releases/tag/v0.8.0",
            "observed_at": "2026-09-01T00:00:00+00:00",
            "source": "official-host-fetched-github-response",
        }, self._official_manifest())
        self.assertEqual(report["status"], "latest")
        self.assertEqual(report["error_codes"], [])
        self.assertGreaterEqual(len(report["components"]), 10)
        self.assertTrue(all(item["status"] == "current" for item in report["components"]))

    def test_non_latest_release_fails_closed(self) -> None:
        report = build_report(ROOT, {
            "version": "0.9.0",
            "tag_name": "v0.9.0",
            "html_url": "https://github.com/clayzwang/clayz-presentation-skills/releases/tag/v0.9.0",
            "observed_at": "2026-09-01T00:00:00+00:00",
            "source": "official-host-fetched-github-response",
        }, {**self._official_manifest(), "release_version": "0.9.0"})
        self.assertEqual(report["status"], "blocked")
        self.assertIn("NON_LATEST_COMPONENT", report["error_codes"])


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

    def test_source_change_under_same_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, bindings = self._fixture(root)
            state_root = root / "state"
            bootstrap(manifest, bindings, core_version="0.7.1", state_root=state_root)
            bindings["method"].write_text('{"title":"changed","summary":"changed method"}\n', encoding="utf-8")
            with self.assertRaisesRegex(VersionLearningError, "PRIVATE_LEARNING_SOURCE_DRIFT"):
                bootstrap(manifest, bindings, core_version="0.7.1", state_root=state_root)


if __name__ == "__main__":
    unittest.main()
