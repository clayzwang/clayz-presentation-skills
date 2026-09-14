# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Check the actual local installable archive, including code and knowledge routes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.build_runtime_packs import build_light, ROOT
from packages.runtime.plugin_session import inspect_plugin


class LocalPluginPackageTests(unittest.TestCase):
    def test_archive_closure_and_integrity(self):
        with tempfile.TemporaryDirectory(prefix="clayz-package-") as temporary:
            root = Path(temporary)
            archive_path = build_light(root, (ROOT / "VERSION").read_text().strip(), "local")
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                prefix = "clayz-presentation-skills/"
                required = [
                    ".codex-plugin/plugin.json", "scripts/plugin_cli.py", "config/tool-catalog.json",
                    "packages/knowledge_session/discussion.py", "packages/knowledge_session/store.py",
                    "packages/runtime/plugin_session.py", "packages/contracts/plugin-system.md",
                    "docs/plugin-system.md", "docs/plugin-system.zh-CN.md",
                ]
                for name in required:
                    self.assertIn(prefix + name, names)
                self.assertFalse(any("plugin-governance" in name for name in names))
                self.assertFalse(any("/snapshots/" in name or "/.git/" in name or "/tests/" in name for name in names))
                manifest_name = prefix + "runtime/plugin-content-manifest.json"
                manifest = json.loads(archive.read(manifest_name))
                expected = {name.removeprefix(prefix) for name in names if name != manifest_name}
                self.assertEqual(set(manifest["files"]), expected)
                for relative, digest in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(archive.read(prefix + relative)).hexdigest(), digest)
                archive.extractall(root / "extracted")
            installed = root / "extracted" / "clayz-presentation-skills"
            self.assertEqual(inspect_plugin(installed)["status"], "ready")
            (installed / "host-note.txt").write_text("Host-generated observation", encoding="utf-8")
            self.assertEqual(inspect_plugin(installed)["status"], "ready")
            target = installed / "packages/knowledge_session/discussion.py"
            original = target.read_bytes()
            target.write_bytes(original + b"\n# Changed after packaging\n")
            self.assertEqual(inspect_plugin(installed)["status"], "blocked")
            target.write_bytes(original)
            (installed / "runtime/plugin-content-manifest.json").unlink()
            self.assertEqual(inspect_plugin(installed)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
