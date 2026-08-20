# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import json
import os
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

    def test_all_public_cli_entrypoints_start(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        paths = [*sorted((ROOT / "scripts").glob("*.py")), *sorted((ROOT / "packages" / "validators").glob("*.py"))]
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
