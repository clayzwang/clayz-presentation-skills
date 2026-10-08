# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Verify the uploaded bytes retain the shared cloud learning implementation."""
import json
import os
import posixpath
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from packages.index_runtime import IndexProvider
from packages.personal_extension import build_provider_manifest
from scripts.compose_personal_light import compose_personal_light, COMPOSITE_DEVELOPMENT_SCHEMAS
from tests.test_personal_extension import profile, private_record

ROOT = Path(__file__).resolve().parents[1]


class CloudUpgradePackageTests(unittest.TestCase):
    def test_art_composition_guidance_remains_readable_in_each_locale(self):
        for locale, suffix in (("en-US", ".md"), ("zh-CN", ".zh-CN.md")):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory(prefix="art-guidance-package-") as directory:
                task = Path(directory)
                config = profile((ROOT / "VERSION").read_text().strip())
                config["overrides"].append({"path": "locale.default", "policy": "replace", "value": locale})
                owner_provider = IndexProvider.from_records("example.private-library", [private_record("example.private-library")])
                manifest = build_provider_manifest(owner_provider, index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl")
                profile_path = task / "profile.json"
                provider_path = task / "provider.json"
                profile_path.write_text(json.dumps(config), encoding="utf-8")
                provider_path.write_text(json.dumps(manifest), encoding="utf-8")
                archive_path = compose_personal_light(profile_path, [provider_path], task / "guidance.zip")
                with zipfile.ZipFile(archive_path) as archive:
                    stage_path = "references/stages/art-direction/stage.md"
                    reference_path = "skills/clayz-presentation-art-direction/references/reader-centered-composition" + suffix
                    stage = archive.read(stage_path).decode("utf-8")
                    link = "../../../" + reference_path
                    self.assertIn("(" + link + ")", stage)
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(stage_path), link))
                    self.assertEqual(reference_path, resolved)
                    self.assertEqual((ROOT / reference_path).read_bytes(), archive.read(resolved))

    def test_same_name_global_skill_and_native_helper_survive_packaging(self):
        with tempfile.TemporaryDirectory(prefix="cloud-upgrade-test-") as directory:
            task = Path(directory)
            config = profile((ROOT / "VERSION").read_text().strip())
            config["mounts"][0]["bindings"]["chatgpt-personal"]["root"] = "OwnerLibrary"
            owner_provider = IndexProvider.from_records("example.private-library", [private_record("example.private-library")])
            manifest = build_provider_manifest(owner_provider, index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl")
            profile_path = task / "profile.json"
            provider_path = task / "provider.json"
            profile_path.write_text(json.dumps(config), encoding="utf-8")
            provider_path.write_text(json.dumps(manifest), encoding="utf-8")
            archive_path = compose_personal_light(profile_path, [provider_path], task / "upgrade.zip")
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertEqual([name for name in names if name.endswith("SKILL.md")], ["SKILL.md"])
                root_skill = archive.read("SKILL.md").decode("utf-8")
                self.assertIn("name: clayz-presentation-personal", root_skill)
                self.assertIn("Chat and Work", root_skill)
                self.assertIn("not tied to", root_skill)
                self.assertIn("native-library-workflow.md", root_skill)
                self.assertIn("allow_implicit_invocation: true", archive.read("agents/openai.yaml").decode("utf-8"))
                policy = json.loads(archive.read("runtime/native-library-policy.json"))
                self.assertEqual(policy["host_root"], "OwnerLibrary/_extension/confirmed-learning")
                self.assertEqual(policy["adapter"], "host-library")
                self.assertNotIn(".mcp.json", names)
                for schema in COMPOSITE_DEVELOPMENT_SCHEMAS:
                    self.assertNotIn(schema, names)
                    self.assertTrue((ROOT / schema).is_file())
                self.assertFalse(any("plugin-governance" in name for name in names))
                for relative in ("scripts/cloud_learning_cli.py", "packages/knowledge_session/discussion.py", "packages/knowledge_session/store.py"):
                    self.assertEqual(archive.read(relative), (ROOT / relative).read_bytes())
                archive.extractall(task / "mounted")
            result = subprocess.run([sys.executable, "-B", str(task / "mounted/scripts/cloud_learning_cli.py"), "--help"],
                                    cwd=task, capture_output=True, text=True,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("stage", result.stdout)
            self.assertIn("verify", result.stdout)


if __name__ == "__main__":
    unittest.main()
