# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from packages.index_runtime import INDEX_CONTRACT, IndexProvider
from packages.index_runtime.utils import sha256_json
from packages.personal_extension import (
    PERSONAL_EXTENSION_PROFILE_CONTRACT,
    PersonalExtensionError,
    build_provider_manifest,
    resolve_logical_uri,
    resolve_personal_extension,
    validate_personal_extension_runtime,
)
from scripts.compose_personal_light import compose_personal_light
from scripts import validate_all as validate_all_script
from scripts.validate_composite_skill_mount import inspect_composite_skill_mount
from packages.validators import index_evidence as index_evidence_validator


ROOT = Path(__file__).resolve().parents[1]


def private_record(provider_id: str, *, sha: str = "1" * 64) -> dict:
    return {
        "contract": INDEX_CONTRACT,
        "record_id": "example.private.reference",
        "record_type": "reference",
        "provider_id": provider_id,
        "title": "Synthetic private reference",
        "summary": "Synthetic owner-private metadata used only by a unit test.",
        "source": {
            "source_id": "synthetic-private-source",
            "source_uri": "library://example-presentation/references/logic/example.pdf",
            "source_revision": "1",
            "sha256": sha,
        },
        "governance": {
            "human_admitted": True,
            "quality_status": "admitted",
            "public_catalog_eligible": False,
            "deprecated": False,
        },
        "rights": {
            "license": "owner-private-test",
            "redistribution": "owner-private",
            "materialization": "owner-private",
            "commercial_use": None,
            "derivative_use": None,
            "attribution_required": False,
            "never_copy": ["source wording"],
        },
        "classification": {
            "stages": ["logic", "art-direction"],
            "task_modes": ["new-build"],
            "page_roles": ["comparison"],
            "semantic_relations": ["supports"],
            "purpose_tags": ["synthetic"],
            "languages": ["en-US", "zh-CN"],
            "failure_signals": [],
            "asset_class": "document",
            "brand_scope": "brand-specific",
        },
        "payload": {"kind": "uri", "ref": "library://example-presentation/references/logic/example.pdf"},
        "neighbors": {"physical": [], "semantic": []},
    }


def profile(core_version: str) -> dict:
    return {
        "contract": PERSONAL_EXTENSION_PROFILE_CONTRACT,
        "profile_id": "example.personal",
        "profile_version": "1.0.0",
        "compatibility": {
            "minimum_core_version": core_version,
            "maximum_core_version_exclusive": "0.9.0",
        },
        "overrides": [
            {"path": "theme.profile", "policy": "replace", "value": "owner-private-theme"},
            {"path": "theme.source", "policy": "replace", "value": "user-master"},
            {"path": "theme.master_path", "policy": "replace", "value": "library://example-presentation/assets/masters/official.pptx"},
            {"path": "theme.colors.accent", "policy": "replace", "value": "#F05A28"},
            {"path": "renderer.required_capabilities", "policy": "append_unique", "value": ["owner-private-library"]},
            {"path": "theme.typography.minimum_audience_text_pt", "policy": "stricter_only", "value": 14},
        ],
        "mounts": [
            {
                "mount_id": "private-library",
                "logical_root": "library://example-presentation/",
                "bindings": {
                    "local": {"adapter": "filesystem", "root": "${CLAYZ_PRESENTATION_LIBRARY_ROOT}"},
                    "chatgpt-personal": {"adapter": "host-library", "root": "PPT"},
                },
            }
        ],
        "providers": [
            {
                "provider_id": "example.private-library",
                "manifest_uri": "library://example-presentation/_extension/providers/private/provider.manifest.json",
                "mount_id": "private-library",
                "required": True,
                "stages": ["logic", "art-direction", "output", "supervisor"],
            }
        ],
    }


class PersonalExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        self.public_manifest = json.loads((ROOT / "catalog" / "provider-manifest.json").read_text(encoding="utf-8"))
        provider = IndexProvider.from_records("example.private-library", [private_record("example.private-library")])
        self.manifest = build_provider_manifest(
            provider,
            index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl",
        )

    def test_cloud_resolution_preserves_one_five_stage_workflow(self) -> None:
        resolved, runtime = resolve_personal_extension(
            self.base,
            profile(self.base["identity"]["version"]),
            host="chatgpt-personal",
            public_provider_manifests=[self.public_manifest],
            provider_manifests=[self.manifest],
        )
        self.assertEqual(runtime["core"]["workflow_stages"], ["logic", "copy", "art-direction", "output", "supervisor"])
        self.assertEqual(runtime["extension"]["decision_point"], "before-logic")
        self.assertTrue(runtime["guards"]["no_sixth_stage"])
        self.assertEqual(resolved["theme"]["master_path"], "library://example-presentation/assets/masters/official.pptx")
        self.assertEqual(resolved["theme"]["typography"]["minimum_audience_text_pt"], 14)
        self.assertIn("owner-private-library", resolved["renderer"]["required_capabilities"])
        self.assertEqual(runtime["mounts"][0]["adapter"], "bundle")
        self.assertEqual(runtime["mounts"][1]["adapter"], "host-library")
        self.assertEqual([item["visibility"] for item in runtime["providers"]], ["public", "owner-private"])
        self.assertEqual(len(runtime["origin_map"]), 6)

    def test_private_profile_can_preserve_one_font_identity_with_aliases(self) -> None:
        candidate = profile(self.base["identity"]["version"])
        font_validation = {
            "contract_version": "1.0",
            "mode": "preserve-name-defer-native",
            "deferred_font_identities": [
                {
                    "canonical_family": "华文楷体",
                    "aliases": ["STKaiti"],
                    "pptx_family": "华文楷体",
                }
            ],
            "preserve_requested_font_names": True,
            "silent_substitution_forbidden": True,
            "cloud_render_authority": "diagnostic-only",
            "cloud_pdf_pixel_equivalence": "not-required-when-deferred-font-missing",
            "native_reopen_required_for_final_font_acceptance": True,
            "missing_deferred_font_status": "font-validation-pending",
        }
        candidate["overrides"].append({
            "path": "theme.typography.font_validation",
            "policy": "replace",
            "value": font_validation,
        })
        resolved, _ = resolve_personal_extension(
            self.base,
            candidate,
            host="chatgpt-personal",
            public_provider_manifests=[self.public_manifest],
            provider_manifests=[self.manifest],
        )
        self.assertEqual(resolved["theme"]["typography"]["font_validation"], font_validation)

    def test_sealed_field_cannot_be_overridden(self) -> None:
        value = profile(self.base["identity"]["version"])
        value["overrides"].append({"path": "workflow.stages", "policy": "replace", "value": ["logic"]})
        with self.assertRaisesRegex(PersonalExtensionError, "sealed"):
            resolve_personal_extension(self.base, value, host="chatgpt-personal", public_provider_manifests=[self.public_manifest], provider_manifests=[self.manifest])

    def test_stricter_only_cannot_lower_threshold(self) -> None:
        value = profile(self.base["identity"]["version"])
        for override in value["overrides"]:
            if override["path"] == "theme.typography.minimum_audience_text_pt":
                override["value"] = 10
        with self.assertRaisesRegex(PersonalExtensionError, "cannot decrease"):
            resolve_personal_extension(self.base, value, host="chatgpt-personal", public_provider_manifests=[self.public_manifest], provider_manifests=[self.manifest])

    def test_same_logical_uri_maps_to_local_and_cloud_roots(self) -> None:
        value = profile(self.base["identity"]["version"])
        _, cloud = resolve_personal_extension(self.base, value, host="chatgpt-personal", public_provider_manifests=[self.public_manifest], provider_manifests=[self.manifest])
        _, local = resolve_personal_extension(self.base, value, host="local", public_provider_manifests=[self.public_manifest], provider_manifests=[self.manifest])
        uri = "library://example-presentation/references/logic/example.pdf"
        cloud_path = resolve_logical_uri(uri, cloud["mounts"][1])
        local_path = resolve_logical_uri(uri, local["mounts"][1], environment={"CLAYZ_PRESENTATION_LIBRARY_ROOT": "X:/synthetic-library"})
        self.assertEqual(cloud_path, "PPT/references/logic/example.pdf")
        self.assertTrue(local_path.replace("\\", "/").endswith("synthetic-library/references/logic/example.pdf"))

    def test_provider_snapshot_can_change_without_profile_change(self) -> None:
        changed = IndexProvider.from_records("example.private-library", [private_record("example.private-library", sha="2" * 64)])
        changed_manifest = build_provider_manifest(
            changed,
            index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl",
        )
        self.assertNotEqual(self.manifest["index"]["snapshot"]["digest"], changed_manifest["index"]["snapshot"]["digest"])
        self.assertEqual(
            self.manifest["index"]["uri"],
            changed_manifest["index"]["uri"],
        )

    def test_runtime_lock_detects_tampering(self) -> None:
        _, runtime = resolve_personal_extension(
            self.base,
            profile(self.base["identity"]["version"]),
            host="chatgpt-personal",
            public_provider_manifests=[self.public_manifest],
            provider_manifests=[self.manifest],
        )
        tampered = copy.deepcopy(runtime)
        tampered["extension"]["profile_version"] = "1.0.1"
        with self.assertRaisesRegex(PersonalExtensionError, "digest mismatch"):
            validate_personal_extension_runtime(tampered)

    def test_index_evidence_requires_every_runtime_required_provider(self) -> None:
        _, runtime = resolve_personal_extension(
            self.base,
            profile(self.base["identity"]["version"]),
            host="chatgpt-personal",
            public_provider_manifests=[self.public_manifest],
            provider_manifests=[self.manifest],
        )
        package = json.loads((ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8"))
        package["index_evidence"]["runtime_lock_digest"] = runtime["lock"]["digest"]
        errors: list[str] = []
        with mock.patch.object(index_evidence_validator, "_bound_personal_runtime", return_value=runtime):
            index_evidence_validator.validate_index_evidence(
                package["index_evidence"],
                ["logic", "copy", "art-direction", "output", "supervisor"],
                "package.index_evidence",
                errors,
            )
        self.assertTrue(any("example.private-library" in error for error in errors), errors)

    def test_index_evidence_requires_each_applicable_provider_to_be_selected(self) -> None:
        _, runtime = resolve_personal_extension(
            self.base,
            profile(self.base["identity"]["version"]),
            host="chatgpt-personal",
            public_provider_manifests=[self.public_manifest],
            provider_manifests=[self.manifest],
        )
        package = json.loads((ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8"))
        evidence = package["index_evidence"]
        evidence["runtime_lock_digest"] = runtime["lock"]["digest"]
        snapshots = evidence["provider_lock"]["snapshots"]
        snapshots.append({
            "provider_id": "example.private-library",
            "digest": self.manifest["index"]["snapshot"]["digest"],
            "record_count": self.manifest["index"]["snapshot"]["record_count"],
        })
        snapshots.sort(key=lambda item: item["provider_id"])
        evidence["provider_lock"]["lock_sha256"] = sha256_json(snapshots)
        for receipt in evidence["stage_receipts"]["logic"]:
            receipt["index_snapshot"] = copy.deepcopy(snapshots)
        errors: list[str] = []
        with mock.patch.object(index_evidence_validator, "_bound_personal_runtime", return_value=runtime):
            index_evidence_validator.validate_index_evidence(
                evidence,
                ["logic"],
                "package.index_evidence",
                errors,
            )
        self.assertTrue(any("must be selected" in error and "example.private-library" in error for error in errors), errors)

    def test_required_provider_snapshot_cannot_be_empty(self) -> None:
        _, runtime = resolve_personal_extension(
            self.base,
            profile(self.base["identity"]["version"]),
            host="chatgpt-personal",
            public_provider_manifests=[self.public_manifest],
            provider_manifests=[self.manifest],
        )
        package = json.loads((ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8"))
        evidence = package["index_evidence"]
        evidence["runtime_lock_digest"] = runtime["lock"]["digest"]
        snapshots = evidence["provider_lock"]["snapshots"]
        snapshots.append({"provider_id": "example.private-library", "digest": "9" * 64, "record_count": 0})
        snapshots.sort(key=lambda item: item["provider_id"])
        evidence["provider_lock"]["lock_sha256"] = sha256_json(snapshots)
        errors: list[str] = []
        with mock.patch.object(index_evidence_validator, "_bound_personal_runtime", return_value=runtime):
            index_evidence_validator.validate_index_evidence(
                evidence,
                ["logic"],
                "package.index_evidence",
                errors,
            )
        self.assertTrue(any("non-empty snapshot" in error for error in errors), errors)

    def test_cloud_composer_excludes_private_index_and_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            profile_path = temp / "personal-profile.json"
            manifest_path = temp / "provider.manifest.json"
            output = temp / "personal-cloud-light.zip"
            profile_path.write_text(json.dumps(profile(self.base["identity"]["version"]), ensure_ascii=False), encoding="utf-8")
            manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            compose_personal_light(profile_path, [manifest_path], output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn("SKILL.md", names)
                self.assertIn("agents/openai.yaml", names)
                self.assertIn("runtime/personal-extension.json", names)
                self.assertIn("runtime/skill-mount-contract.json", names)
                self.assertIn("config/personal-extension-resolved.json", names)
                self.assertIn("catalog/provider-manifest.json", names)
                self.assertNotIn(".codex-plugin/plugin.json", names)
                self.assertEqual([name for name in names if Path(name).name == "SKILL.md"], ["SKILL.md"])
                self.assertFalse(any(name.startswith("skills/") and Path(name).name == "SKILL.md" for name in names))
                self.assertIn(
                    "skills/clayz-presentation-art-direction/references/ab-and-regression.md",
                    names,
                )
                self.assertFalse(any("packages/runtime/packs/" in name for name in names))
                self.assertFalse(any("packages/adapters/" in name for name in names))
                self.assertFalse(any("_extension/providers/private/index/records.jsonl" in name for name in names))
                combined = b"\n".join(archive.read(name) for name in names if name.endswith((".json", ".md")))
                self.assertNotIn(b"Synthetic private reference", combined)
                root_skill = archive.read("SKILL.md").decode("utf-8")
                self.assertIn("name: clayz-presentation-personal", root_skill)
                self.assertIn("ppt-supervision-report.json", root_skill)
                self.assertIn("initiator, mediator, recorder, and final auditor", root_skill)
                mount = json.loads(archive.read("runtime/skill-mount-contract.json"))
                self.assertEqual(mount["publication_unit"], "single-skill")
                self.assertEqual(len(mount["stage_modules"]), 5)
                runtime_lock = json.loads(archive.read("runtime/runtime-lock.json"))
                self.assertEqual(runtime_lock["contract"], "io.clayz.presentation.runtime-pack-lock/1.2")
                self.assertEqual(
                    [item["provider_id"] for item in runtime_lock["required_provider_bindings"]],
                    ["builtin-catalog", "example.private-library"],
                )
                for stage_module in mount["stage_modules"]:
                    self.assertIn(stage_module, names)

                archive.extractall(temp / "extracted")
            report = inspect_composite_skill_mount(temp / "extracted")
            self.assertTrue(report["complete"], report)
            self.assertEqual(report["skill_files"], ["SKILL.md"])
            runtime_path = temp / "extracted" / "runtime" / "personal-extension.json"
            runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            runtime["providers"] = [item for item in runtime["providers"] if item["visibility"] == "public"]
            unlocked = copy.deepcopy(runtime)
            unlocked.pop("lock")
            runtime["lock"]["digest"] = sha256_json(unlocked)
            runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
            tampered_report = inspect_composite_skill_mount(temp / "extracted")
            self.assertFalse(tampered_report["complete"], tampered_report)
            self.assertTrue(any("required-provider" in error or "extension-digest" in error for error in tampered_report["errors"]))

    def test_cloud_composer_rejects_font_alias_as_second_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            candidate = profile(self.base["identity"]["version"])
            candidate["overrides"].extend([
                {
                    "path": "theme.typography.primary_fonts",
                    "policy": "replace",
                    "value": ["华文楷体", "STKaiti"],
                },
                {
                    "path": "theme.typography.font_validation",
                    "policy": "replace",
                    "value": {
                        "contract_version": "1.0",
                        "mode": "preserve-name-defer-native",
                        "deferred_font_identities": [
                            {
                                "canonical_family": "华文楷体",
                                "aliases": ["STKaiti"],
                                "pptx_family": "华文楷体",
                            }
                        ],
                        "preserve_requested_font_names": True,
                        "silent_substitution_forbidden": True,
                        "cloud_render_authority": "diagnostic-only",
                        "cloud_pdf_pixel_equivalence": "not-required-when-deferred-font-missing",
                        "native_reopen_required_for_final_font_acceptance": True,
                        "missing_deferred_font_status": "font-validation-pending",
                    },
                },
            ])
            profile_path = temp / "personal-profile.json"
            manifest_path = temp / "provider.manifest.json"
            output = temp / "personal-cloud-light.zip"
            profile_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(PersonalExtensionError, "must not appear in primary_fonts as a fallback"):
                compose_personal_light(profile_path, [manifest_path], output)

    def test_validate_all_dispatches_the_standalone_skill_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("---\nname: synthetic\n---\n", encoding="utf-8")
            with (
                mock.patch.object(validate_all_script, "ROOT", root),
                mock.patch.object(validate_all_script, "compile_sources") as compile_sources,
                mock.patch.object(validate_all_script, "validate_standalone_skill") as validate_standalone,
            ):
                self.assertEqual(validate_all_script.main(), 0)
            compile_sources.assert_called_once_with()
            validate_standalone.assert_called_once_with()

    def test_standalone_validation_uses_artifact_specific_mount_not_local_runtime_pack(self) -> None:
        with mock.patch.object(validate_all_script, "run") as run:
            validate_all_script.validate_standalone_skill()
        commands = [call.args for call in run.call_args_list]
        self.assertIn(("scripts/validate_composite_skill_mount.py", "--root", "."), commands)
        self.assertFalse(any("validate_runtime.py" in command for command in commands))
        self.assertFalse(any("validate_plugin_mount.py" in command for command in commands))
        self.assertFalse(any("validate_personal_extension_foundation.py" in command for command in commands))

    def test_cloud_composer_retains_explicit_marketplace_plugin_form(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            profile_path = temp / "personal-profile.json"
            manifest_path = temp / "provider.manifest.json"
            output = temp / "personal-plugin-light.zip"
            profile_path.write_text(json.dumps(profile(self.base["identity"]["version"]), ensure_ascii=False), encoding="utf-8")
            manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            compose_personal_light(
                profile_path,
                [manifest_path],
                output,
                plugin_name="clayz-presentation-skills-personal",
                artifact_kind="plugin",
            )
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn(".codex-plugin/plugin.json", names)
                self.assertIn("runtime/plugin-mount-contract.json", names)
                self.assertEqual(len([name for name in names if name.endswith("/SKILL.md")]), 5)
                manifest = json.loads(archive.read(".codex-plugin/plugin.json"))
                self.assertEqual(manifest["name"], "clayz-presentation-skills-personal")


if __name__ == "__main__":
    unittest.main()
