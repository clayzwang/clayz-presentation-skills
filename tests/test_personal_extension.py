# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from packages.index_runtime import INDEX_CONTRACT, IndexProvider
from packages.personal_extension import (
    PERSONAL_EXTENSION_PROFILE_CONTRACT,
    PersonalExtensionError,
    build_provider_manifest,
    resolve_logical_uri,
    resolve_personal_extension,
    validate_personal_extension_runtime,
)
from scripts.compose_personal_light import compose_personal_light


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
            "maximum_core_version_exclusive": "0.7.0",
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
                "required": False,
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
                self.assertIn("runtime/personal-extension.json", names)
                self.assertIn("runtime/plugin-mount-contract.json", names)
                self.assertIn("config/personal-extension-resolved.json", names)
                self.assertIn("catalog/provider-manifest.json", names)
                self.assertFalse(any("packages/runtime/packs/" in name for name in names))
                self.assertFalse(any("packages/adapters/" in name for name in names))
                self.assertFalse(any("_extension/providers/private/index/records.jsonl" in name for name in names))
                combined = b"\n".join(archive.read(name) for name in names if name.endswith((".json", ".md")))
                self.assertNotIn(b"Synthetic private reference", combined)
                manifest = json.loads(archive.read(".codex-plugin/plugin.json"))
                self.assertEqual(manifest["name"], "clayz-presentation-skills-personal")


if __name__ == "__main__":
    unittest.main()
