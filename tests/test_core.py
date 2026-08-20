# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
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
        version = "0.2.0"
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(config["identity"]["version"], version)
        self.assertEqual(config["identity"]["attribution"]["custom_properties"]["ClayzVersion"], version)
        self.assertEqual(plugin["version"], version)
        self.assertIn(f"version: {version}", (ROOT / "CITATION.cff").read_text(encoding="utf-8"))
        pptxgenjs = config["renderer"]["adapters"]["pptxgenjs"]
        self.assertFalse(pptxgenjs["enabled"])
        self.assertEqual(len(pptxgenjs["blocked_advisories"]), 2)

    def test_all_json_files_parse(self) -> None:
        for path in sorted(ROOT.rglob("*.json")):
            if ".git" in path.parts or "node_modules" in path.parts or path.name == "search-index.json":
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_public_adoption_boundary_is_explicit(self) -> None:
        manifest = (ROOT / "provenance" / "manifest.yaml").read_text(encoding="utf-8")
        boundary = (ROOT / "docs" / "source-adoption.md").read_text(encoding="utf-8")
        for source in ("pptagent", "deeppresenter", "pom", "vascar", "postero", "pptxgenjs"):
            self.assertIn(f'id: "{source}"', manifest)
        for excluded in ("reveal.js", "Marp", "PosterLlama", "Typst/Paged"):
            self.assertIn(excluded, boundary)

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
        ]
        for path in paths:
            if path.name == "validate_all.py":
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
