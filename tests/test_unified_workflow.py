# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Behavioral coverage for the unified task configuration workflow."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST_ATTESTATION_CONTRACT = "io.clayz.presentation.host-capability-attestation/1.0"
HOST_INVENTORY_CONTRACT = "io.clayz.presentation.host-tool-inventory/1.0"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider  # noqa: E402
from packages.index_runtime.utils import sha256_json  # noqa: E402
from packages.personal_extension import build_provider_manifest  # noqa: E402
from packages.personal_extension.resolver import (  # noqa: E402
    TASK_RESOURCE_SELECTION_V2_CONTRACT,
    prepare_unified_task_selection,
    validate_task_selection,
)
from packages.validators.index_evidence import validate_index_evidence  # noqa: E402
from packages.validators.resource_inventory import (  # noqa: E402
    finalize_resource_inventory,
    validate_resource_inventory,
)
from scripts.compose_personal_light import compose_personal_light  # noqa: E402
from scripts.publish_supervised_pair import validate_personal_runtime_binding  # noqa: E402
from tests.test_personal_extension import private_record, profile  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: dict[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


class UnifiedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = json.loads(
            (ROOT / "tests" / "fixtures" / "synthetic-copy-package.json").read_text(encoding="utf-8")
        )

    @staticmethod
    def _write_layer(path: Path, value: dict[str, object]) -> Path:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def _prepare(
        self,
        bundle_root: Path,
        output_dir: Path,
        *,
        personal: Path | None = None,
        task: Path | None = None,
        library_enabled: bool | None = None,
        library_locator: str | None = None,
        previous: dict[str, object] | None = None,
    ) -> tuple[dict[str, object], dict[str, object], Path, Path]:
        output_dir.mkdir(parents=True)
        config_path = output_dir / "task-config.json"
        config, selection = prepare_unified_task_selection(
            bundle_root,
            config_path,
            personal_config_path=personal,
            task_overrides_path=task,
            library_enabled=library_enabled,
            library_locator=library_locator,
            previous_selection=previous,
        )
        selection_path = output_dir / "task-selection.json"
        config_path.write_bytes(_canonical(config))
        selection_path.write_bytes(_canonical(selection))
        validate_task_selection(selection_path, config_path, bundle_root, expected_mode="unified")
        return config, selection, config_path, selection_path

    def _compose_personal(self, destination: Path) -> Path:
        config = profile((ROOT / "VERSION").read_text(encoding="utf-8").strip())
        config["mounts"][0]["bindings"]["chatgpt-personal"]["root"] = "UnifiedWorkflowLibrary"
        provider = IndexProvider.from_records(
            "example.private-library",
            [private_record("example.private-library")],
        )
        manifest = build_provider_manifest(
            provider,
            index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl",
        )
        profile_path = destination / "synthetic-profile.json"
        provider_path = destination / "synthetic-provider.json"
        archive_path = destination / "personal-light.zip"
        profile_path.write_text(json.dumps(config), encoding="utf-8")
        provider_path.write_text(json.dumps(manifest), encoding="utf-8")
        compose_personal_light(profile_path, [provider_path], archive_path)
        extracted = destination / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extracted)
        return extracted

    def test_layer_precedence_admits_only_visual_sections_and_preserves_json_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-layers-") as directory:
            task_root = Path(directory)
            personal = self._write_layer(
                task_root / "personal.json",
                {
                    "config": {
                        "theme": {"profile": "synthetic-personal", "colors": {"accent": "#112233"}},
                        "layout": {"column_count": 3},
                        "locale": {"default": "zh-CN"},
                    },
                    "preferences": {
                        "reading": {"density": "detailed"},
                        "records": [{"record_id": "row-1", "value": "保留原始 JSON"}],
                    },
                },
            )
            task = self._write_layer(
                task_root / "task-overrides.json",
                {
                    "config": {
                        "theme": {"colors": {"accent": "#AABBCC"}},
                        "layout": {"column_count": 7},
                        "locale": {"default": "en-US"},
                    },
                    "preferences": {"reading": {"density": "compact"}, "task_only": {"keep": True}},
                },
            )
            personal_raw = personal.read_bytes()
            task_raw = task.read_bytes()
            config, selection, _, _ = self._prepare(
                ROOT,
                task_root / "output",
                personal=personal,
                task=task,
                library_enabled=False,
            )
            default = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
            self.assertEqual(selection["contract"], TASK_RESOURCE_SELECTION_V2_CONTRACT)
            self.assertEqual(selection["workflow"], "unified")
            self.assertNotIn("mode", selection)
            self.assertNotIn("visual_source", selection)
            self.assertEqual(set(selection["layers"]), {"defaults", "personal", "task_overrides"})
            self.assertEqual(config["theme"]["profile"], "synthetic-personal")
            self.assertEqual(config["theme"]["colors"]["accent"], "#AABBCC")
            self.assertEqual(config["layout"]["column_count"], 7)
            self.assertEqual(config["locale"]["default"], "en-US")
            self.assertEqual(config["renderer"], default["renderer"])
            self.assertNotIn("owner-private-library", config["renderer"]["required_capabilities"])
            self.assertEqual(
                selection["preferences"],
                {
                    "reading": {"density": "compact"},
                    "records": [{"record_id": "row-1", "value": "保留原始 JSON"}],
                    "task_only": {"keep": True},
                },
            )
            self.assertEqual(personal.read_bytes(), personal_raw)
            self.assertEqual(task.read_bytes(), task_raw)
            self.assertEqual(selection["layers"]["personal"]["source_sha256"], hashlib.sha256(personal_raw).hexdigest())
            self.assertEqual(selection["layers"]["task_overrides"]["source_sha256"], hashlib.sha256(task_raw).hexdigest())

    def test_profile_free_defaults_and_bundled_personal_visual_do_not_add_private_render_caps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-visual-") as directory:
            task_root = Path(directory)
            plain_config, plain_selection, _, _ = self._prepare(ROOT, task_root / "plain")
            default = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
            self.assertEqual(plain_config, default)
            self.assertEqual(plain_selection["layers"]["personal"]["snapshot"], {"config": {}, "preferences": {}})
            self.assertFalse(plain_selection["library_enabled"])
            self.assertEqual(plain_selection["library_status"], "unconfigured")

            extracted = self._compose_personal(task_root)
            runtime_lock = json.loads((extracted / "runtime" / "runtime-lock.json").read_text(encoding="utf-8"))
            self.assertTrue(runtime_lock["unified_workflow_required"])
            config, selection, _, _ = self._prepare(extracted, task_root / "installed")
            personal = json.loads((extracted / "config" / "personal-extension-resolved.json").read_text(encoding="utf-8"))
            self.assertEqual(
                Path(selection["layers"]["personal"]["source_path"]).resolve(),
                (extracted / "config" / "personal-extension-resolved.json").resolve(),
            )
            self.assertEqual(config["theme"], personal["theme"])
            self.assertEqual(config["layout"], personal["layout"])
            self.assertEqual(config["locale"], personal["locale"])
            default_capabilities = default["renderer"]["required_capabilities"]
            self.assertEqual(config["renderer"]["required_capabilities"][: len(default_capabilities)], default_capabilities)
            self.assertNotIn("owner-private-library", config["renderer"]["required_capabilities"])
            for capability in ("master-preservation", "layout-inheritance", "east-asian-font-name"):
                self.assertIn(capability, config["renderer"]["required_capabilities"])
            self.assertFalse(selection["library_enabled"])

    def test_explicit_personal_update_changes_layer_while_task_overrides_still_win(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-update-") as directory:
            task_root = Path(directory)
            personal_v1 = self._write_layer(
                task_root / "personal-v1.json",
                {"config": {"theme": {"profile": "personal-v1", "colors": {"accent": "#111111"}}}, "preferences": {"revision": 1}},
            )
            task = self._write_layer(
                task_root / "task.json",
                {"config": {"theme": {"colors": {"accent": "#AAAAAA"}}}, "preferences": {}},
            )
            first_config, first, _, _ = self._prepare(
                ROOT,
                task_root / "first",
                personal=personal_v1,
                task=task,
                library_enabled=False,
            )
            personal_v2 = self._write_layer(
                task_root / "personal-v2.json",
                {"config": {"theme": {"profile": "personal-v2", "colors": {"accent": "#222222"}}}, "preferences": {"revision": 2}},
            )
            second_config, second, _, _ = self._prepare(
                ROOT,
                task_root / "second",
                personal=personal_v2,
                previous=first,
                library_enabled=False,
            )
            self.assertNotEqual(first["layers"]["personal"]["source_sha256"], second["layers"]["personal"]["source_sha256"])
            self.assertNotEqual(first_config["theme"]["profile"], second_config["theme"]["profile"])
            self.assertEqual(second_config["theme"]["colors"]["accent"], "#AAAAAA")
            self.assertEqual(second["preferences"]["revision"], 2)

            third_config, third, _, _ = self._prepare(
                ROOT,
                task_root / "third",
                personal=personal_v2,
                task=task,
                previous=second,
                library_enabled=False,
            )
            self.assertEqual(third_config["theme"]["colors"]["accent"], "#AAAAAA")
            self.assertEqual(third["layers"]["task_overrides"], second["layers"]["task_overrides"])

    def test_previous_selection_reuses_personal_snapshot_when_source_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-reuse-") as directory:
            task_root = Path(directory)
            personal = self._write_layer(
                task_root / "personal.json",
                {"config": {"theme": {"profile": "saved-personal", "colors": {"accent": "#334455"}}}, "preferences": {"saved": True}},
            )
            first_config, first, _, _ = self._prepare(
                ROOT,
                task_root / "first",
                personal=personal,
                library_enabled=False,
            )
            personal.unlink()
            second_config, second, _, _ = self._prepare(
                ROOT,
                task_root / "second",
                previous=first,
                library_enabled=False,
            )
            self.assertEqual(second_config, first_config)
            self.assertEqual(second["layers"]["personal"], first["layers"]["personal"])
            self.assertEqual(second["parent_selection_sha256"], first["selection_sha256"])

    def _unified_public_evidence(self) -> dict[str, object]:
        evidence = copy.deepcopy(self.package["index_evidence"])
        snapshots = [
            copy.deepcopy(next(item for item in evidence["provider_lock"]["snapshots"] if item["provider_id"] == "builtin-catalog"))
        ]
        evidence["mode"] = "unified"
        evidence["provider_lock"]["snapshots"] = snapshots
        evidence["provider_lock"]["lock_sha256"] = sha256_json(snapshots)
        evidence["owner_materialization"] = {
            "status": "not-applicable",
            "source_manifest_sha256": None,
            "materialization_report_sha256": None,
            "provider_id": "task-private-learning",
            "record_count": 0,
            "required_sources": [],
            "materialized_source_ids": [],
            "missing_source_ids": [],
        }
        for stage, receipts in evidence["stage_receipts"].items():
            for receipt in receipts:
                receipt["index_snapshot"] = copy.deepcopy(snapshots)
                receipt["request"]["rights_context"] = "public-open-source"
                receipt["request"]["filters"]["provider_ids"] = ["builtin-catalog"]
                candidate = {
                    "record_id": f"synthetic.public.{stage}",
                    "provider_id": "builtin-catalog",
                    "source_id": "synthetic-public-source",
                }
                receipt["candidates"] = [candidate]
                receipt["selection"] = {
                    "selected": [{
                        "record_id": candidate["record_id"],
                        "reason": "synthetic public evidence for the unified route",
                        "adoption_targets": [f"stage:{stage}"],
                        "adoption_status": "material",
                    }],
                    "rejected": [],
                    "coverage_status": "complete",
                    "coverage_gaps": [],
                }
                receipt["ranking"].update(
                    eligible_candidate_count=1,
                    above_threshold_count=1,
                )
                receipt["hallucination_guard"].update(candidate_count=1, invented_record_count=0, only_registered_records=True)
        return evidence

    def test_unified_index_and_inventory_do_not_require_legacy_private_ids_but_missing_selected_materialization_blocks(self) -> None:
        evidence = self._unified_public_evidence()
        errors: list[str] = []
        validate_index_evidence(evidence, ["logic", "copy"], "index_evidence", errors)
        self.assertEqual(errors, [], errors)

        inventory = copy.deepcopy(self.package["resource_inventory"])
        inventory["runtime_mode"] = "unified"
        inventory = finalize_resource_inventory(inventory)
        errors = []
        validate_resource_inventory(inventory, "resource_inventory", errors)
        self.assertEqual(errors, [], errors)

        blocked = copy.deepcopy(evidence)
        snapshots = [
            *copy.deepcopy(blocked["provider_lock"]["snapshots"]),
            {"provider_id": "task-private-learning", "digest": "d" * 64, "record_count": 1},
        ]
        snapshots.sort(key=lambda item: item["provider_id"])
        blocked["provider_lock"]["snapshots"] = snapshots
        blocked["provider_lock"]["lock_sha256"] = sha256_json(snapshots)
        for receipts in blocked["stage_receipts"].values():
            for receipt in receipts:
                receipt["index_snapshot"] = copy.deepcopy(snapshots)
        blocked["owner_materialization"] = {
            "status": "materialized",
            "source_manifest_sha256": "e" * 64,
            "materialization_report_sha256": "f" * 64,
            "provider_id": "task-private-learning",
            "record_count": 1,
            "required_sources": [{"source_id": "private-selected-source", "stages": ["logic"]}],
            "materialized_source_ids": [],
            "missing_source_ids": ["private-selected-source"],
        }
        errors = []
        validate_index_evidence(blocked, ["logic"], "index_evidence", errors)
        self.assertTrue(any("every required source" in error for error in errors), errors)

    def _run_script(self, script: Path, cwd: Path, *args: object, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-B", str(script), *map(str, args)],
            cwd=cwd,
            env=dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("Traceback", result.stderr)
        return result

    def test_unified_pack_requires_task_selection_before_preflight_consumption_and_publisher_accepts_v2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-preflight-") as directory:
            task_root = Path(directory)
            extracted = self._compose_personal(task_root)
            challenge_root = task_root / "challenge"
            challenge_root.mkdir()
            task_request = challenge_root / "task-request.txt"
            task_request.write_bytes(b"synthetic unified workflow task\n")
            challenge_path = challenge_root / "run-challenge.json"
            self._run_script(
                extracted / "scripts" / "runtime_preflight.py",
                challenge_root,
                "--issue-challenge",
                "--task-request",
                task_request,
                "--output",
                challenge_path,
            )
            missing_selection = self._run_script(
                extracted / "scripts" / "runtime_preflight.py",
                challenge_root,
                "--challenge",
                challenge_path,
                "--task-request",
                task_request,
                "--config",
                extracted / "config" / "default.json",
                ok=False,
            )
            self.assertIn("requires --task-selection", missing_selection.stderr)
            self.assertFalse((challenge_root / ".clayz-run-challenges" / "consumed").exists())

            config, selection, config_path, selection_path = self._prepare(extracted, task_root / "selection")
            challenge = json.loads(challenge_path.read_text(encoding="utf-8"))
            challenge_sha256 = _sha256(challenge_path)
            capabilities = list(config["renderer"]["required_capabilities"])
            inventory_path = challenge_root / "host-tool-inventory.json"
            inventory = {
                "contract": HOST_INVENTORY_CONTRACT,
                "run_id": challenge["run_id"],
                "task_request_sha256": challenge["task_request_sha256"],
                "nonce": challenge["nonce"],
                "challenge_sha256": challenge_sha256,
                "capabilities": capabilities,
            }
            inventory_raw = (json.dumps(inventory, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            inventory_path.write_bytes(inventory_raw)
            host_path = challenge_root / "host-capabilities.json"
            host_path.write_text(
                json.dumps(
                    {
                        "contract": HOST_ATTESTATION_CONTRACT,
                        "host": "synthetic-host",
                        "available": True,
                        "capabilities": capabilities,
                        "run_id": challenge["run_id"],
                        "task_request_sha256": challenge["task_request_sha256"],
                        "nonce": challenge["nonce"],
                        "challenge_sha256": challenge_sha256,
                        "source": "host-inspection",
                        "observed_at": challenge["issued_at"],
                        "evidence_receipts": [{
                            "artifact": inventory_path.name,
                            "sha256": hashlib.sha256(inventory_raw).hexdigest(),
                            "contract": HOST_INVENTORY_CONTRACT,
                        }],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            version = str(config["identity"]["version"])
            component_report_path = challenge_root / "component-version-report.json"
            component_report_path.write_text(
                json.dumps(
                    {
                        "contract": "io.clayz.presentation.component-version-report/1.0",
                        "artifact": "component-version-report.json",
                        "sha256": "a" * 64,
                        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                        "status": "latest",
                        "local_release_version": version,
                        "latest_release_version": version,
                        "latest_release": {"version": version},
                        "manifest_sha256": "b" * 64,
                        "all_components_current": True,
                        "error_codes": [],
                        "components": [{"component_id": "synthetic-runtime", "status": "current"}],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            preflight_path = challenge_root / "runtime-preflight.json"
            self._run_script(
                extracted / "scripts" / "runtime_preflight.py",
                challenge_root,
                "--challenge",
                challenge_path,
                "--task-request",
                task_request,
                "--task-selection",
                selection_path,
                "--config",
                config_path,
                "--model-profile",
                "D",
                "--host-capabilities",
                host_path,
                "--component-version-report",
                component_report_path,
                "--output",
                preflight_path,
            )
            preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
            binding = preflight["config_binding"]
            self.assertEqual(binding["source"], "task-selected")
            self.assertEqual(binding["path"], config_path.resolve().as_posix())
            self.assertEqual(binding["selection_path"], selection_path.resolve().as_posix())
            self.assertEqual(binding["selection_sha256"], _sha256(selection_path))
            bad_binding = copy.deepcopy(preflight)
            bad_binding["config_binding"]["source"] = "public-default"
            with self.assertRaisesRegex(RuntimeError, "unified publication requires config binding source task-selected"):
                validate_personal_runtime_binding(
                    config_path,
                    config,
                    bad_binding,
                    runtime_mode="unified",
                    resolved_config_sha256=_sha256(config_path),
                )

            publisher_code = """
import hashlib
import json
import sys
from pathlib import Path
from scripts.publish_supervised_pair import validate_personal_runtime_binding

config_path = Path(sys.argv[1])
preflight_path = Path(sys.argv[2])
raw = config_path.read_bytes()
validate_personal_runtime_binding(
    config_path,
    json.loads(raw),
    json.loads(preflight_path.read_text(encoding='utf-8')),
    runtime_mode='unified',
    resolved_config_sha256=hashlib.sha256(raw).hexdigest(),
)
"""
            publisher = subprocess.run(
                [sys.executable, "-B", "-c", publisher_code, str(config_path), str(preflight_path)],
                cwd=extracted,
                env=dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1"),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
            self.assertEqual(publisher.returncode, 0, publisher.stdout + publisher.stderr)


if __name__ == "__main__":
    unittest.main()
