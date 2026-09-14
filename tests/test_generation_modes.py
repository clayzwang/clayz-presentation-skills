# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Regression coverage for Logic generation-mode and optional brief metadata."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from packages.index_runtime import IndexProvider  # noqa: E402
from packages.personal_extension import build_provider_manifest  # noqa: E402
from packages.validators.validate_logic_package import validate_package  # noqa: E402
from scripts.compose_personal_light import compose_personal_light  # noqa: E402
from tests.test_personal_extension import private_record, profile  # noqa: E402


class GenerationModeValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(
            (ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8")
        )

    def _package(self) -> dict:
        return copy.deepcopy(self.fixture)

    @staticmethod
    def _errors(package: dict) -> list[str]:
        return validate_package(package, "copy-approved")

    def test_existing_copy_approved_fixture_still_passes(self) -> None:
        self.assertEqual(self._errors(self.fixture), [])

    def test_preflight_taxonomy_confirmation_and_management_path_are_optional(self) -> None:
        package = self._package()
        preflight = package["brief"]["preflight"]
        for key in ("material_type", "management_stage", "narrative_archetype", "confirmation"):
            preflight.pop(key)
        package["logic_layer"]["narrative"].pop("management_stage_path")
        self.assertEqual(self._errors(package), [])

    def test_free_labels_and_management_path_values_are_accepted(self) -> None:
        package = self._package()
        preflight = package["brief"]["preflight"]
        preflight.update(
            {
                "material_type": "board memo for a newly formed team",
                "management_stage": "customer problem framing",
                "narrative_archetype": "evidence to decision",
                "confirmation": {
                    "audience": "user-provided",
                    "desired_outcome": "user-confirmed",
                    "generation_mode": "agent-inferred",
                },
            }
        )
        package["logic_layer"]["narrative"]["management_stage_path"] = [
            "current state to decision",
            "pilot follow-through",
        ]
        self.assertEqual(self._errors(package), [])

    def test_all_supported_generation_modes_pass_and_legacy_omission_passes(self) -> None:
        # The fixture above is the explicit legacy-omission check. Each mode
        # is exercised against the same complete package so this remains a
        # validator regression rather than a string-level semantics test.
        self.assertEqual(self._errors(self.fixture), [])
        for mode in ("execution", "research", "mixed"):
            with self.subTest(mode=mode):
                package = self._package()
                package["brief"]["preflight"]["generation_mode"] = mode
                self.assertEqual(self._errors(package), [])

    def test_audience_and_desired_outcome_remain_required(self) -> None:
        for key in ("audience", "desired_outcome"):
            with self.subTest(key=key):
                package = self._package()
                package["brief"]["preflight"].pop(key)
                errors = self._errors(package)
                self.assertTrue(any(f"brief.preflight.{key}" in error for error in errors), errors)

    def test_unknown_generation_mode_is_rejected(self) -> None:
        package = self._package()
        package["brief"]["preflight"]["generation_mode"] = "manual"
        errors = self._errors(package)
        self.assertTrue(any("brief.preflight.generation_mode" in error for error in errors), errors)

    def test_blank_or_non_string_optional_labels_are_rejected(self) -> None:
        for key, value in (
            ("material_type", "  "),
            ("management_stage", ""),
            ("narrative_archetype", 7),
        ):
            with self.subTest(key=key):
                package = self._package()
                package["brief"]["preflight"][key] = value
                errors = self._errors(package)
                self.assertTrue(any(f"brief.preflight.{key}" in error for error in errors), errors)

    def test_malformed_confirmation_values_are_rejected(self) -> None:
        for key, value in (
            ("audience", "inferred-by-someone"),
            ("desired_outcome", None),
            ("generation_mode", "manual"),
        ):
            with self.subTest(key=key):
                package = self._package()
                package["brief"]["preflight"]["confirmation"] = {key: value}
                errors = self._errors(package)
                self.assertTrue(any(f"confirmation.{key}" in error for error in errors), errors)

        package = self._package()
        package["brief"]["preflight"]["confirmation"] = "user-confirmed"
        errors = self._errors(package)
        self.assertTrue(any("brief.preflight.confirmation" in error for error in errors), errors)

    def test_management_stage_path_allows_empty_but_rejects_malformed_values(self) -> None:
        for value in ([], ["custom stage"]):
            with self.subTest(value=value):
                package = self._package()
                package["logic_layer"]["narrative"]["management_stage_path"] = value
                self.assertEqual(self._errors(package), [])

        for value in ([""], ["custom stage", 3], "custom stage"):
            with self.subTest(value=value):
                package = self._package()
                package["logic_layer"]["narrative"]["management_stage_path"] = value
                errors = self._errors(package)
                self.assertTrue(any("management_stage_path" in error for error in errors), errors)

    def test_existing_evidence_claim_source_and_content_requirements_remain_fail_closed(self) -> None:
        cases = {
            "missing claim": (lambda package: package["logic_layer"]["slides"][0].pop("claim"), "claim"),
            "missing source metadata": (
                lambda package: package["logic_layer"]["sources"][0].pop("resource_id"),
                "resource_id",
            ),
            "unresolved evidence source": (
                lambda package: package["logic_layer"]["slides"][0].update(source_ids=["SRC-MISSING"]),
                "unknown sources",
            ),
            "missing content requirement": (
                lambda package: package["acceptance_contract"].update(requirements=[]),
                "requirements",
            ),
        }
        for label, (mutate, token) in cases.items():
            with self.subTest(label=label):
                package = self._package()
                mutate(package)
                errors = self._errors(package)
                self.assertTrue(any(token in error for error in errors), errors)

    def test_composed_extracted_standalone_keeps_updated_validator(self) -> None:
        """A synthetic private Profile archive must execute the changed validator."""

        with tempfile.TemporaryDirectory(prefix="generation-modes-standalone-") as directory:
            task = Path(directory)
            config = profile((ROOT / "VERSION").read_text(encoding="utf-8").strip())
            config["mounts"][0]["bindings"]["chatgpt-personal"]["root"] = "GenerationModesLibrary"
            provider = IndexProvider.from_records(
                "example.private-library",
                [private_record("example.private-library")],
            )
            manifest = build_provider_manifest(
                provider,
                index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl",
            )
            profile_path = task / "synthetic-profile.json"
            provider_path = task / "synthetic-provider.json"
            archive_path = task / "standalone.zip"
            profile_path.write_text(json.dumps(config), encoding="utf-8")
            provider_path.write_text(json.dumps(manifest), encoding="utf-8")
            compose_personal_light(profile_path, [provider_path], archive_path)

            extracted = task / "extracted"
            extracted.mkdir()
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIn("packages/validators/validate_logic_package.py", archive.namelist())
                archive.extractall(extracted)

            package = self._package()
            preflight = package["brief"]["preflight"]
            for key in ("material_type", "management_stage", "narrative_archetype", "confirmation"):
                preflight.pop(key)
            preflight["generation_mode"] = "research"
            package["logic_layer"]["narrative"].pop("management_stage_path")
            package_path = extracted / "synthetic-logic-package.json"
            package_path.write_text(json.dumps(package), encoding="utf-8")

            # The extracted archive carries a private runtime whose Provider
            # lock is unrelated to this public fixture. Remove only those
            # temporary binding files so the standalone validator exercises
            # the package contract itself under the extracted module tree.
            for relative in (
                "runtime/personal-extension.json",
                "runtime/runtime-lock.json",
                "config/personal-extension-resolved.json",
            ):
                (extracted / relative).unlink(missing_ok=True)

            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUTF8"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(extracted / "packages/validators/validate_logic_package.py"),
                    str(package_path),
                    "--require-status",
                    "copy-approved",
                ],
                cwd=extracted,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
