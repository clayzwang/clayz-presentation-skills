# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoreTests(unittest.TestCase):
    def test_config(self) -> None:
        module = load_module("validate_config", ROOT / "scripts" / "validate_config.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        self.assertEqual(module.validate(config), [])
        self.assertEqual(config["identity"]["brand"], "clayz")

    def test_release_versions_are_consistent(self) -> None:
        module = load_module("validate_version", ROOT / "scripts" / "validate_version.py")
        self.assertEqual(module.validate(ROOT), [])
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(config["identity"]["version"], version)
        self.assertEqual(config["identity"]["attribution"]["custom_properties"]["ClayzVersion"], version)
        self.assertEqual(plugin["version"], version)
        self.assertIn(f"version: {version}", (ROOT / "CITATION.cff").read_text(encoding="utf-8"))
        pptxgenjs = config["renderer"]["adapters"]["pptxgenjs"]
        self.assertFalse(pptxgenjs["enabled"])
        self.assertEqual(len(pptxgenjs["blocked_advisories"]), 2)

    def test_version_validator_rejects_drift(self) -> None:
        module = load_module("validate_version_drift", ROOT / "scripts" / "validate_version.py")
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary)
            for relative in module.REQUIRED_FILES:
                source = ROOT / relative
                target = snapshot / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            plugin_path = snapshot / ".codex-plugin" / "plugin.json"
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
            plugin["version"] = "9.9.9"
            plugin_path.write_text(json.dumps(plugin, indent=2) + "\n", encoding="utf-8")
            errors = module.validate(snapshot)
            self.assertTrue(any(".codex-plugin/plugin.json" in error for error in errors))

    def test_prepare_release_updates_current_surfaces_only(self) -> None:
        scripts_root = ROOT / "scripts"
        sys.path.insert(0, str(scripts_root))
        try:
            validator = load_module("validate_version_prepare", scripts_root / "validate_version.py")
            preparer = load_module("prepare_release_test", scripts_root / "prepare_release.py")
        finally:
            sys.path.remove(str(scripts_root))
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary)
            required = set(validator.REQUIRED_FILES) | set(preparer.TEXT_SURFACES)
            for relative in required:
                source = ROOT / relative
                target = snapshot / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            changelog_path = snapshot / "CHANGELOG.md"
            changelog = changelog_path.read_text(encoding="utf-8").replace(
                "## Unreleased\n\n- Nothing yet.",
                "## Unreleased\n\n- Synthetic patch release note.",
                1,
            )
            changelog_path.write_text(changelog, encoding="utf-8")
            current = (snapshot / "VERSION").read_text(encoding="utf-8").strip()
            major, minor, patch = (int(part) for part in current.split("."))
            next_patch = f"{major}.{minor}.{patch + 1}"
            preparer.prepare(snapshot, next_patch, "2026-08-23")
            self.assertEqual((snapshot / "VERSION").read_text(encoding="utf-8").strip(), next_patch)
            self.assertEqual(validator.validate(snapshot), [])
            self.assertIn("## 0.2.0 — 2026-08-20", changelog_path.read_text(encoding="utf-8"))

    def test_all_json_files_parse(self) -> None:
        for path in sorted(ROOT.rglob("*.json")):
            if ".git" in path.parts or "node_modules" in path.parts or path.name == "search-cache.json":
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_public_adoption_boundary_is_explicit(self) -> None:
        manifest = (ROOT / "provenance" / "manifest.yaml").read_text(encoding="utf-8")
        boundary = (ROOT / "docs" / "source-adoption.md").read_text(encoding="utf-8")
        for source in (
            "ppt-master", "pptagent", "deeppresenter", "pom", "vascar", "postero",
            "posterlayout", "scan-and-print", "creatiposter", "pptxgenjs",
        ):
            self.assertIn(f'id: "{source}"', manifest)
        for excluded in ("reveal.js", "Marp", "PosterLlama", "Typst/Paged"):
            self.assertIn(excluded, boundary)

    def test_architecture_research_library_is_real_and_method_driven(self) -> None:
        module = load_module(
            "validate_architecture_research_library",
            ROOT / "scripts" / "validate_architecture_research_library.py",
        )
        reference_root = ROOT / "skills" / "clayz-presentation-art-direction" / "references"
        index = json.loads((reference_root / "architecture-source-index.json").read_text(encoding="utf-8"))
        pattern_text = (reference_root / "architecture-pattern-library.md").read_text(encoding="utf-8")
        method_texts = [
            (reference_root / "reference-architecture-house.md").read_text(encoding="utf-8"),
            (reference_root / "reference-architecture-house.zh-CN.md").read_text(encoding="utf-8"),
        ]
        self.assertEqual(module.validate(index, pattern_text, method_texts), [])
        self.assertEqual(len(index["sources"]), 76)
        self.assertEqual(len({source["publisher"] for source in index["sources"]}), 10)

    def test_visual_regression_suite_has_fixed_capability_coverage(self) -> None:
        module = load_module(
            "validate_visual_regression_suite",
            ROOT / "scripts" / "validate_visual_regression_suite.py",
        )
        suite = json.loads(
            (ROOT / "tests" / "fixtures" / "visual-regression-suite.json").read_text(encoding="utf-8")
        )
        self.assertEqual(module.validate(suite), [])
        self.assertEqual(
            {case["case_id"]: case["category"] for case in suite["cases"]},
            module.REQUIRED_CASES,
        )

    def test_art_direction_requires_observed_canvas_and_licensed_assets(self) -> None:
        validator_root = ROOT / "packages" / "validators"
        sys.path.insert(0, str(validator_root))
        try:
            module = load_module(
                "validate_art_direction_plan_contract_14",
                validator_root / "validate_art_direction_plan.py",
            )
        finally:
            sys.path.remove(str(validator_root))
        package = json.loads(
            (ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8")
        )
        plan = json.loads(
            (ROOT / "tests" / "fixtures" / "synthetic-art-direction-plan.json").read_text(encoding="utf-8")
        )
        slide = plan["slides"][0]
        plan["art_direction"]["dominant_media_sequence"] = ["photo-or-screenshot"]
        slide["dominant_medium"] = "photo-or-screenshot"
        slide["medium_execution_contract"].update({
            "structure_type": "photo-or-screenshot",
            "mapping_mode": "mixed",
            "required_object_types": ["picture", "shape"],
            "minimum_object_counts": {"picture": 1, "shape": 2},
            "semantic_axes": ["subject to proposition"],
            "render_recognition_criteria": ["subject remains visible and gaze supports the proposition"],
        })
        slide["content_aware_canvas"] = {
            "enabled": True,
            "canvas_type": "photo",
            "subject_protection_zones": [
                {"zone_id": "SUBJECT-01", "role": "synthetic product", "protection": "hard", "reason": "primary evidence"}
            ],
            "candidate_placement_zones": [
                {
                    "zone_id": "PLACE-01",
                    "suitability": "primary",
                    "anchor_edges": ["left", "top"],
                    "supports_copy_ids": ["C-S01-01", "C-S01-02"],
                    "reason": "stable contrast with a gaze-led reading path",
                }
            ],
            "crop_strategy": "focal-crop",
            "contrast_strategy": "native",
            "directional_flow": "synthetic subject gaze leads toward the proposition",
            "overlay_policy": "none",
            "evidence_basis": "full-size synthetic image review with real copy footprint",
        }
        slide["asset_strategy"] = {
            "template_mode": "derive-not-clone",
            "icon_policy": "semantic-only",
            "required_roles": ["channel"],
            "candidate_asset_ids": ["ICON-SYNTHETIC-01"],
            "selected_asset_ids": ["ICON-SYNTHETIC-01"],
            "selection_rationale": "The synthetic icon distinguishes the channel faster than repeated copy.",
            "family_consistency": "single-family",
            "license_records": [
                {"asset_id": "ICON-SYNTHETIC-01", "source": "synthetic fixture", "license": "Apache-2.0", "attribution_required": False}
            ],
            "never_copy": ["reference wording", "reference brand identity", "reference coordinates"],
        }
        self.assertEqual(module.validate_plan(package, plan), [])

        missing_canvas = copy.deepcopy(plan)
        missing_canvas["slides"][0]["content_aware_canvas"]["enabled"] = False
        self.assertTrue(any("content_aware_canvas" in error for error in module.validate_plan(package, missing_canvas)))

        missing_license = copy.deepcopy(plan)
        missing_license["slides"][0]["asset_strategy"]["license_records"] = []
        self.assertTrue(any("license_records" in error for error in module.validate_plan(package, missing_license)))

    def test_stamp_custom_properties(self) -> None:
        module = load_module("stamp_pptx_metadata", ROOT / "scripts" / "stamp_pptx_metadata.py")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "input.pptx"
            output = Path(temporary) / "output.pptx"
            content_types = b'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'
            rels = b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("[Content_Types].xml", content_types)
                archive.writestr("_rels/.rels", rels)
                archive.writestr("ppt/presentation.xml", b"<presentation/>")
            values = {"ClayzBrand": "clayz", "ClayzNamespace": "io.clayz.presentation"}
            module.stamp(source, output, values)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("docProps/custom.xml", archive.namelist())
                root = ET.fromstring(archive.read("docProps/custom.xml"))
                text = " ".join(value for value in root.itertext() if value)
                self.assertIn("clayz", text)
                self.assertIn("io.clayz.presentation", text)

            cleaned = Path(temporary) / "cleaned.pptx"
            module.remove_stamp(output, cleaned, set(values))
            with zipfile.ZipFile(cleaned) as archive:
                self.assertNotIn("docProps/custom.xml", archive.namelist())

    def test_skill_tree(self) -> None:
        module = load_module("validate_skill_tree", ROOT / "scripts" / "validate_skill_tree.py")
        self.assertEqual(module.validate(ROOT), [])

    def test_knowledge_scaffold(self) -> None:
        module = load_module("validate_knowledge_scaffold", ROOT / "scripts" / "validate_knowledge_scaffold.py")
        self.assertEqual(module.validate(ROOT), [])

    def test_reference_configuration_points_to_scaffold(self) -> None:
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        references = config["references"]
        self.assertEqual(references["public_provider_manifest"], "catalog/provider-manifest.json")
        self.assertEqual(references["public_index"], "catalog/records.jsonl")
        self.assertEqual(references["index"]["role"], "derived-local-search-cache")
        self.assertEqual(references["learning"]["stages"], ["logic", "copy", "art-direction", "output"])
        self.assertFalse(references["learning"]["auto_promote"])
        self.assertNotIn("supervisor", references["learning"]["stages"])
        for relative in [*references["roots"], references["registry"], references["admission_registry"], references["learning"]["root"], references["learning"]["contract"]]:
            self.assertTrue((ROOT / relative).exists(), relative)
        self.assertTrue((ROOT / references["index"]["path"]).parent.is_dir())

    def test_relative_layout_solver(self) -> None:
        module = load_module("solve_relative_layout", ROOT / "packages" / "layout" / "solve_relative_layout.py")
        document = json.loads((ROOT / "examples" / "synthetic-business-review" / "layout-tree.json").read_text(encoding="utf-8"))
        resolved = module.solve(document)
        self.assertEqual(resolved["contract"], "io.clayz.presentation.layout-resolution/1.0")
        nodes = {node["id"]: node for node in resolved["boxes"]}
        self.assertEqual(set(nodes), {"slide-body", "evidence-region", "chart-region", "source-region", "implication-region", "signal-one", "signal-two", "decision-boundary"})
        self.assertAlmostEqual(nodes["slide-body"]["w"], 12.23)
        self.assertLess(nodes["evidence-region"]["x"], nodes["implication-region"]["x"])
        self.assertEqual(resolved["diagnostics"], [])

    def test_knowledge_requires_separate_human_admission(self) -> None:
        module = load_module("knowledge_cli", ROOT / "scripts" / "knowledge_cli.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            shutil.copy2(ROOT / "config" / "default.json", root / "config" / "default.json")
            source = root / "knowledge" / "sources" / "documents" / "sample.md"
            source.parent.mkdir(parents=True)
            source.write_text("Evidence before recommendation. 证据先于建议。", encoding="utf-8")
            for path in [
                root / "knowledge" / "registry" / "asset-registry.jsonl",
                root / "knowledge" / "registry" / "admitted-references.jsonl",
            ]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            for stage in ("logic", "copy", "art-direction", "output"):
                path = root / "knowledge" / "learning" / stage / "learning-records.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")

            settings = module.load_settings(root, root / "config" / "default.json")
            asset = module.register_asset(
                settings,
                source,
                asset_id="asset-synthetic",
                kind="document",
                source_uri="synthetic-test",
                license_name="CC0-1.0",
                language="mul",
                purpose_tags=["narrative-structure"],
                physical_neighbors=[],
                semantic_neighbors=[],
                notes="Synthetic fixture",
            )
            self.assertFalse(asset["human_admitted"])
            self.assertEqual(module.build_index(settings)["document_count"], 0)
            with self.assertRaises(module.KnowledgeError):
                module.admit_reference(
                    settings,
                    "asset",
                    "asset-synthetic",
                    admitted_by="test-maintainer",
                    use_for=["narrative-structure"],
                    never_copy=["wording"],
                    decision_notes="Synthetic test only",
                    confirmed=False,
                )
            module.admit_reference(
                settings,
                "asset",
                "asset-synthetic",
                admitted_by="test-maintainer",
                use_for=["narrative-structure"],
                never_copy=["wording"],
                decision_notes="Synthetic test only",
                confirmed=True,
            )
            index = module.build_index(settings)
            self.assertEqual(index["document_count"], 1)
            self.assertEqual(module.search_index(index, "evidence recommendation", purpose="narrative-structure", limit=5)[0]["asset_id"], "asset-synthetic")
            self.assertEqual(module.search_index(index, "证据 建议", purpose=None, limit=5)[0]["asset_id"], "asset-synthetic")
            source.write_text("Changed after admission.", encoding="utf-8")
            self.assertEqual(module.build_index(settings)["document_count"], 0)

    def test_execution_ledger_is_bounded_and_hashes_artifacts(self) -> None:
        module = load_module("execution_ledger", ROOT / "scripts" / "execution_ledger.py")
        self.assertEqual(module.configured_maximum_cycles(ROOT / "config" / "default.json"), 3)
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "artifact.json"
            artifact.write_text('{"synthetic": true}\n', encoding="utf-8")
            ledger = module.initialize("synthetic-run", 2)
            event = module.append_event(
                ledger,
                cycle=1,
                stage="output",
                tool="synthetic-renderer",
                status="succeeded",
                inputs=[artifact],
                outputs=[artifact],
                evidence_refs=["synthetic-proof"],
                error_code=None,
                message="No real case data.",
            )
            self.assertEqual(len(event["inputs"][0]["sha256"]), 64)
            with self.assertRaises(module.LedgerError):
                module.append_event(
                    ledger,
                    cycle=3,
                    stage="output",
                    tool="synthetic-renderer",
                    status="failed",
                    inputs=[],
                    outputs=[],
                    evidence_refs=[],
                    error_code="OUTSIDE_BOUND",
                    message="",
                )
            module.close(ledger, "pass")
            self.assertEqual(ledger["final_status"], "pass")

    def test_all_public_cli_entrypoints_start(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        paths = [
            *sorted((ROOT / "scripts").glob("*.py")),
            *sorted((ROOT / "packages" / "validators").glob("*.py")),
            *sorted((ROOT / "packages" / "layout").glob("*.py")),
            *sorted((ROOT / "packages" / "patterns").glob("*.py")),
        ]
        for path in paths:
            if path.name in {"validate_all.py", "__init__.py"}:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                result = subprocess.run(
                    [sys.executable, str(path), "--help"],
                    cwd=ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_synthetic_approved_handoff_chain(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        fixture_root = ROOT / "tests" / "fixtures"
        commands = [
            ["packages/validators/validate_logic_package.py", "tests/fixtures/synthetic-copy-package.json", "--require-status", "copy-approved"],
            ["packages/validators/validate_ppt_package.py", "tests/fixtures/synthetic-copy-package.json"],
            [
                "packages/validators/validate_art_direction_plan.py",
                "tests/fixtures/synthetic-copy-package.json",
                "tests/fixtures/synthetic-art-direction-plan.json",
                "--config",
                "config/default.json",
            ],
        ]
        self.assertTrue((fixture_root / "synthetic-copy-package.json").is_file())
        self.assertTrue((fixture_root / "synthetic-art-direction-plan.json").is_file())
        for command in commands:
            with self.subTest(command=command[0]):
                result = subprocess.run(
                    [sys.executable, *command],
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
