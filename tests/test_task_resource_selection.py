# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""CLI regression tests for the unified task-resource selection contract."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_SELECTION_CONTRACT = "io.clayz.presentation.task-resource-selection/2.0"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.personal_extension import PersonalExtensionError  # noqa: E402
from packages.personal_extension.resolver import (  # noqa: E402
    TASK_RESOURCE_SELECTION_CONTRACT,
    canonical_task_selection_sha256,
    prepare_task_selection,
    validate_task_selection,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(value: dict[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


class TaskResourceSelectionTests(unittest.TestCase):
    def _run_cli(
        self,
        *args: object,
        ok: bool = True,
        cwd: Path = ROOT,
    ) -> tuple[dict[str, object] | None, subprocess.CompletedProcess[str]]:
        environment = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [sys.executable, "-B", str(cwd / "scripts" / "cloud_learning_cli.py"), *map(str, args)],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout), result
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        return None, result

    @staticmethod
    def _selection_files(output_dir: Path) -> tuple[Path, Path]:
        return output_dir / "task-config.json", output_dir / "task-selection.json"

    def _configure(self, output_dir: Path, *args: object, ok: bool = True) -> tuple[dict[str, object] | None, subprocess.CompletedProcess[str]]:
        return self._run_cli("configure-task", *args, "--output-dir", output_dir, ok=ok)

    def test_plain_pack_defaults_to_unified_public_selection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-selection-public-") as directory:
            output = Path(directory) / "first"
            selection, _ = self._configure(output)
            assert selection is not None
            config_path, selection_path = self._selection_files(output)
            default_config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
            derived_config = json.loads(config_path.read_text(encoding="utf-8"))

            self.assertEqual(selection["contract"], TASK_SELECTION_CONTRACT)
            self.assertEqual(selection["workflow"], "unified")
            self.assertNotIn("mode", selection)
            self.assertNotIn("visual_source", selection)
            self.assertFalse(selection["library_enabled"])
            self.assertEqual(selection["library_status"], "unconfigured")
            self.assertEqual(set(selection["layers"]), {"defaults", "personal", "task_overrides"})
            self.assertEqual(selection["layers"]["personal"]["snapshot"], {"config": {}, "preferences": {}})
            self.assertEqual(selection["layers"]["task_overrides"]["snapshot"], {"config": {}, "preferences": {}})
            self.assertEqual(derived_config, default_config)
            self.assertNotIn("owner-private-library", derived_config["renderer"]["required_capabilities"])
            self.assertEqual(selection["config_sha256"], _sha256(config_path))
            self.assertEqual(selection["selection_sha256"], canonical_task_selection_sha256(selection))
            self.assertEqual(selection_path.read_bytes()[-1:], b"\n")

    def test_legacy_cli_flags_are_rejected_but_v1_factory_has_negative_parse_coverage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-selection-legacy-") as directory:
            task = Path(directory)
            _, result = self._configure(task / "legacy-cli", "--mode", "public-core", ok=False)
            self.assertIn("legacy", result.stderr)
            self.assertIn("--with-library", result.stderr)

            legacy_config_path = task / "legacy-config.json"
            legacy_config, legacy_selection = prepare_task_selection(
                ROOT,
                "public-core",
                "public-default",
                legacy_config_path,
            )
            legacy_config_path.write_bytes(_canonical_json(legacy_config))
            legacy_selection_path = task / "legacy-selection.json"
            legacy_selection_path.write_bytes(_canonical_json(legacy_selection))
            validated = validate_task_selection(legacy_selection_path, legacy_config_path, ROOT)
            self.assertEqual(validated["contract"], TASK_RESOURCE_SELECTION_CONTRACT)

            malformed = copy.deepcopy(legacy_selection)
            malformed["selection_sha256"] = "0" * 64
            malformed_path = task / "malformed-v1.json"
            malformed_path.write_bytes(_canonical_json(malformed))
            with self.assertRaises(PersonalExtensionError):
                validate_task_selection(malformed_path, legacy_config_path, ROOT)

            v2_shaped_without_layers = copy.deepcopy(legacy_selection)
            v2_shaped_without_layers["contract"] = TASK_SELECTION_CONTRACT
            v2_shaped_path = task / "v2-shaped-v1.json"
            v2_shaped_path.write_bytes(_canonical_json(v2_shaped_without_layers))
            with self.assertRaises(PersonalExtensionError):
                validate_task_selection(v2_shaped_path, legacy_config_path, ROOT)

    def test_library_toggle_and_locator_revisions_preserve_unified_config(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-selection-locator-") as directory:
            task = Path(directory)
            personal = task / "personal.json"
            personal.write_text(
                json.dumps(
                    {
                        "config": {
                            "theme": {
                                "profile": "synthetic-master",
                                "source": "user-master",
                                "master_path": "library://synthetic/master.pptx",
                            }
                        },
                        "preferences": {"visual_identity": "synthetic-master"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            first, _ = self._configure(task / "first", "--personal-config", personal)
            assert first is not None
            first_config, first_selection = self._selection_files(task / "first")
            original_config = first_config.read_bytes()
            original_selection = first_selection.read_bytes()

            enabled, _ = self._configure(
                task / "enabled",
                "--with-library",
                "--previous-selection",
                first_selection,
            )
            assert enabled is not None
            enabled_config, enabled_selection = self._selection_files(task / "enabled")
            self.assertTrue(enabled["library_enabled"])
            self.assertEqual(enabled["library_status"], "enabled-pending-verification")
            self.assertEqual(enabled_config.read_bytes(), original_config)
            self.assertEqual(json.loads(enabled_config.read_text(encoding="utf-8"))["theme"], json.loads(first_config.read_text(encoding="utf-8"))["theme"])

            located, _ = self._configure(
                task / "located",
                "--library-locator",
                "PPT",
                "--previous-selection",
                enabled_selection,
            )
            assert located is not None
            located_config, located_selection = self._selection_files(task / "located")
            self.assertTrue(located["library_enabled"])
            self.assertEqual(located["library_status"], "locator-pending-verification")
            self.assertEqual(located["library_locator"], "PPT")
            self.assertEqual(located_config.read_bytes(), original_config)

            changed, _ = self._configure(
                task / "changed",
                "--library-locator",
                "OwnerLibrary",
                "--previous-selection",
                located_selection,
            )
            assert changed is not None
            changed_config, changed_selection = self._selection_files(task / "changed")
            self.assertEqual(changed["library_locator"], "OwnerLibrary")
            self.assertEqual(changed["library_status"], "locator-pending-verification")
            self.assertEqual(changed_config.read_bytes(), original_config)

            disabled, _ = self._configure(
                task / "disabled",
                "--without-library",
                "--previous-selection",
                changed_selection,
            )
            assert disabled is not None
            disabled_config, disabled_selection = self._selection_files(task / "disabled")
            self.assertFalse(disabled["library_enabled"])
            self.assertEqual(disabled["library_status"], "unconfigured")
            self.assertNotIn("library_locator", disabled)
            self.assertEqual(disabled_config.read_bytes(), original_config)

            reenabled, _ = self._configure(
                task / "reenabled",
                "--with-library",
                "--previous-selection",
                disabled_selection,
            )
            assert reenabled is not None
            reenabled_config, _ = self._selection_files(task / "reenabled")
            self.assertTrue(reenabled["library_enabled"])
            self.assertEqual(reenabled["library_status"], "enabled-pending-verification")
            self.assertEqual(reenabled_config.read_bytes(), original_config)
            self.assertEqual(first_config.read_bytes(), original_config)
            self.assertEqual(first_selection.read_bytes(), original_selection)

    def test_tampered_v2_selection_or_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-selection-tamper-") as directory:
            task = Path(directory)
            selection, _ = self._configure(task / "first")
            assert selection is not None
            config_path, selection_path = self._selection_files(task / "first")
            original_config = config_path.read_bytes()

            tampered_selection = copy.deepcopy(selection)
            tampered_selection["workflow"] = "legacy"
            tampered_selection_path = task / "tampered-selection.json"
            tampered_selection_path.write_bytes(_canonical_json(tampered_selection))
            _, result = self._configure(
                task / "reject-selection",
                "--previous-selection",
                tampered_selection_path,
                ok=False,
            )
            self.assertIn("selection_sha256", result.stderr)

            altered_config = json.loads(original_config)
            altered_config["theme"]["profile"] = "tampered"
            config_path.write_bytes(_canonical_json(altered_config))
            _, result = self._configure(
                task / "reject-config",
                "--previous-selection",
                selection_path,
                ok=False,
            )
            self.assertIn("config", result.stderr)
            config_path.write_bytes(original_config)


if __name__ == "__main__":
    unittest.main()
