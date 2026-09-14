# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Behavioral coverage for optional owner-Library task routing.

These tests exercise the public and owner-personal boundaries through the
existing command line tools and final publisher.  Private inputs are synthetic
profile/provider fixtures only; no host Library or external service is used.
"""

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
from importlib import util as importlib_util
from pathlib import Path
from unittest import mock

from packages.index_runtime import INDEX_CONTRACT, IndexProvider
from packages.index_runtime.utils import sha256_json
from packages.personal_extension import build_provider_manifest
from packages.validators import index_evidence as index_evidence_validator
from packages.validators.resource_inventory import finalize_resource_inventory, validate_resource_inventory
from scripts.compose_personal_light import compose_personal_light


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)
PUBLIC_CONFIG_PATH = ROOT / "config" / "default.json"
PUBLIC_INDEX_PATH = ROOT / "catalog" / "records.jsonl"
PRE_FLIGHT_CONTRACT = "io.clayz.presentation.runtime-preflight/1.3"
HOST_ATTESTATION_CONTRACT = "io.clayz.presentation.host-capability-attestation/1.0"
HOST_INVENTORY_CONTRACT = "io.clayz.presentation.host-tool-inventory/1.0"
INDEX_EVIDENCE_CONTRACT = "io.clayz.presentation.index-execution-evidence/1.1"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _load_script_module(name: str, path: Path):
    spec = importlib_util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic_private_record(provider_id: str) -> dict[str, object]:
    """Build metadata only; the source body is deliberately never packaged."""

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
            "sha256": "1" * 64,
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
        "payload": {
            "kind": "uri",
            "ref": "library://example-presentation/references/logic/example.pdf",
        },
        "neighbors": {"physical": [], "semantic": []},
    }


def _synthetic_profile(core_version: str) -> dict[str, object]:
    return {
        "contract": "io.clayz.presentation.personal-extension-profile/1.0",
        "profile_id": "example.personal",
        "profile_version": "1.0.0",
        "compatibility": {
            "minimum_core_version": core_version,
            "maximum_core_version_exclusive": "1.0.0",
        },
        "overrides": [
            {"path": "theme.profile", "policy": "replace", "value": "owner-private-theme"},
            {"path": "theme.source", "policy": "replace", "value": "user-master"},
            {
                "path": "theme.master_path",
                "policy": "replace",
                "value": "library://example-presentation/assets/masters/official.pptx",
            },
            {"path": "theme.colors.accent", "policy": "replace", "value": "#F05A28"},
            {
                "path": "renderer.required_capabilities",
                "policy": "append_unique",
                "value": ["owner-private-library"],
            },
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


def _component_version_report(config: dict[str, object]) -> dict[str, object]:
    version = str(config["identity"]["version"])
    return {
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
    }


def _run_process(args: list[object], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [str(PYTHON), "-B", *map(str, args)],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def _public_preflight(root: Path, task_root: Path) -> tuple[dict[str, object], Path]:
    """Run the shipped preflight CLI with an explicit public config binding."""

    task_root.mkdir(parents=True, exist_ok=True)
    task_request = task_root / "task-request.txt"
    task_request.write_bytes(b"synthetic public-core presentation request\n")
    challenge = task_root / "run-challenge.json"
    script = root / "scripts" / "runtime_preflight.py"
    issued = _run_process(
        [script, "--issue-challenge", "--task-request", task_request, "--output", challenge],
        cwd=task_root,
    )
    if issued.returncode != 0:
        raise AssertionError(issued.stderr or issued.stdout)

    challenge_raw = challenge.read_bytes()
    challenge_value = json.loads(challenge_raw)
    challenge_sha256 = _sha256_bytes(challenge_raw)
    config = json.loads((root / "config" / "default.json").read_text(encoding="utf-8"))
    capabilities = list(config["renderer"]["required_capabilities"])
    inventory = {
        "contract": HOST_INVENTORY_CONTRACT,
        "run_id": challenge_value["run_id"],
        "task_request_sha256": challenge_value["task_request_sha256"],
        "nonce": challenge_value["nonce"],
        "challenge_sha256": challenge_sha256,
        "capabilities": capabilities,
    }
    inventory_path = task_root / "host-tool-inventory.json"
    inventory_raw = _json_bytes(inventory)
    inventory_path.write_bytes(inventory_raw)
    host = {
        "contract": HOST_ATTESTATION_CONTRACT,
        "host": "synthetic-host",
        "available": True,
        "capabilities": capabilities,
        "run_id": challenge_value["run_id"],
        "task_request_sha256": challenge_value["task_request_sha256"],
        "nonce": challenge_value["nonce"],
        "challenge_sha256": challenge_sha256,
        "source": "host-inspection",
        "observed_at": challenge_value["issued_at"],
        "evidence_receipts": [
            {
                "artifact": inventory_path.name,
                "sha256": _sha256_bytes(inventory_raw),
                "contract": HOST_INVENTORY_CONTRACT,
            }
        ],
    }
    host_path = task_root / "host-capabilities.json"
    host_path.write_bytes(_json_bytes(host))
    component_report = task_root / "component-version-report.json"
    component_report.write_bytes(_json_bytes(_component_version_report(config)))
    output = task_root / "runtime-preflight.json"
    scanned = _run_process(
        [
            script,
            "--challenge",
            challenge,
            "--task-request",
            task_request,
            "--config",
            root / "config" / "default.json",
            "--model-profile",
            "D",
            "--host-capabilities",
            host_path,
            "--component-version-report",
            component_report,
            "--output",
            output,
        ],
        cwd=task_root,
    )
    if scanned.returncode != 0:
        raise AssertionError(scanned.stderr or scanned.stdout)
    return json.loads(output.read_text(encoding="utf-8")), output


def _compose_and_extract_personal_skill(destination: Path) -> Path:
    config = json.loads(PUBLIC_CONFIG_PATH.read_text(encoding="utf-8"))
    provider = IndexProvider.from_records(
        "example.private-library",
        [_synthetic_private_record("example.private-library")],
    )
    manifest = build_provider_manifest(
        provider,
        index_uri="library://example-presentation/_extension/providers/private/index/records.jsonl",
    )
    profile_path = destination / "synthetic-profile.json"
    manifest_path = destination / "synthetic-provider.json"
    archive_path = destination / "personal-light.zip"
    profile_path.write_bytes(_json_bytes(_synthetic_profile(str(config["identity"]["version"]))))
    manifest_path.write_bytes(_json_bytes(manifest))
    compose_personal_light(profile_path, [manifest_path], archive_path)
    extracted = destination / "extracted-personal"
    extracted.mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extracted)
    # Historical 0.13 mode-binding compatibility fixture. New production
    # policy is exercised separately by test_unified_workflow.
    lock_path = extracted / "runtime/runtime-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["unified_workflow_required"] = False
    lock_path.write_bytes(_json_bytes(lock))
    return extracted


def _publisher_module(root: Path):
    return _load_script_module(
        f"publish_supervised_pair_optional_library_{id(root)}",
        root / "scripts" / "publish_supervised_pair.py",
    )


def _public_inventory(*, master_available: bool) -> dict[str, object]:
    resources = [
        {
            "resource_id": "task.request",
            "category": "task-input",
            "label": "synthetic user request",
            "origin": "task",
            "locator": "task://request",
            "availability": "available",
            "required": True,
            "stages": ["root", "logic"],
            "quantity": 1,
            "fingerprint_sha256": "a" * 64,
            "rights_context": "task-provided",
            "decision": "selected",
            "decision_reason": "required by the task",
            "evidence_ref": "evidence/task-request.json",
        },
        {
            "resource_id": "public.index",
            "category": "index-provider",
            "label": "bundled public Index",
            "origin": "public-catalog",
            "locator": "public-index://builtin-catalog",
            "availability": "available",
            "required": True,
            "stages": ["root", "logic", "copy", "art-direction", "output", "supervisor"],
            "quantity": 24,
            "fingerprint_sha256": "b" * 64,
            "rights_context": "public-open-source",
            "decision": "selected",
            "decision_reason": "public retrieval is required in public-core mode",
            "evidence_ref": "evidence/public-index.json",
        },
        {
            "resource_id": "task.master",
            "category": "template",
            "label": "explicitly requested user master",
            "origin": "task",
            "locator": "attachment://user-master.pptx",
            "availability": "available" if master_available else "missing",
            "required": True,
            "stages": ["root", "art-direction", "output", "supervisor"],
            "quantity": 1,
            "fingerprint_sha256": "c" * 64 if master_available else None,
            "rights_context": "task-provided",
            "decision": "selected" if master_available else "unavailable",
            "decision_reason": "the user explicitly required this master",
            "evidence_ref": "evidence/user-master.pptx",
        },
        {
            "resource_id": "host.route",
            "category": "authoring-route",
            "label": "synthetic authoring route",
            "origin": "host",
            "locator": "host://authoring-route",
            "availability": "available",
            "required": True,
            "stages": ["root", "output", "supervisor"],
            "quantity": 1,
            "fingerprint_sha256": None,
            "rights_context": "host-capability",
            "decision": "selected",
            "decision_reason": "the locked route is available",
            "evidence_ref": "runtime-preflight.json",
        },
    ]
    reported = sorted(item["resource_id"] for item in resources)
    selected = sorted(item["resource_id"] for item in resources if item["decision"] == "selected")
    not_selected = sorted(set(reported) - set(selected))
    draft = {
        "contract": "io.clayz.presentation.resource-inventory/1.0",
        "inventory_id": "inventory.optional-library.public",
        "revision": 1,
        "task_mode": "new-build",
        "runtime_mode": "public-core",
        "created_at": "2026-09-13T08:00:00+00:00",
        "scan_scope": [
            {
                "scope": scope,
                "status": "not-applicable" if scope == "owner-library" else "complete",
                "evidence_ref": f"evidence/{scope}.json",
                "discovered_entry_count": 0 if scope == "owner-library" else 1,
                "note": f"{scope} was inspected for this synthetic public task",
            }
            for scope in (
                "plugin-runtime",
                "task-inputs",
                "owner-library",
                "public-index",
                "brand-assets",
                "host-capabilities",
                "font-environment",
            )
        ],
        "resources": resources,
        "execution_route": {
            "status": "ready",
            "authoring_route": "synthetic authoring",
            "render_route": "synthetic render",
            "target_application": "synthetic target",
            "evidence_ref": "runtime-preflight.json",
        },
        "user_brief": {
            "status": "presented",
            "presented_at": "2026-09-13T08:01:00+00:00",
            "channel": "commentary",
            "language": "en-US",
            "reported_resource_ids": reported,
            "reported_selected_resource_ids": selected,
            "reported_not_selected_resource_ids": not_selected,
            "reported_unavailable_resource_ids": ["task.master"] if not master_available else [],
            "discovered_lines": ["Public runtime and bundled public Index are available."],
            "selected_lines": ["This task uses the public-core route and public Index."],
            "unavailable_lines": [] if master_available else ["The explicitly requested user master is unavailable."],
            "execution_line": "The public route is locked and ready for Logic.",
        },
        "gate": {
            "verified_before_logic": True,
            "authoring_started_at": "2026-09-13T08:02:00+00:00",
        },
    }
    return finalize_resource_inventory(draft)


class OptionalLibraryBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="clayz-optional-library-")
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_composed_personal_skill_public_preflight_binds_config_without_private_runtime(self) -> None:
        """Exercise the public config binding while the private runtime is not selected."""

        extracted = _compose_and_extract_personal_skill(self.root)
        preflight, _ = _public_preflight(extracted, self.root / "public-task")

        self.assertEqual(preflight["contract"], PRE_FLIGHT_CONTRACT)
        self.assertEqual(preflight["config_binding"]["source"], "public-default")
        self.assertEqual(
            Path(preflight["config_binding"]["path"]).resolve(),
            (extracted / "config" / "default.json").resolve(),
        )
        self.assertEqual(preflight["config_binding"]["sha256"], _sha256_file(extracted / "config" / "default.json"))
        self.assertTrue(preflight["selected_route"]["attemptable"] or preflight["selected_route"]["available"])

        # The composed package contains a private runtime for owner-personal
        # tasks, but this call explicitly selects the public route.  It must
        # validate the bundled public config binding and return before reading
        # the unselected private runtime.  Release assembly is covered by the
        # calibrated end-to-end tests; this compatibility test does not create
        # or publish an unassembled report.
        publisher = _publisher_module(extracted)
        resolved_config_path = extracted / "config" / "default.json"
        resolved_config = json.loads(resolved_config_path.read_text(encoding="utf-8"))
        self.assertTrue((extracted / "runtime" / "personal-extension.json").is_file())
        publisher.validate_personal_runtime_binding(
            resolved_config_path,
            resolved_config,
            preflight,
            runtime_mode="public-core",
            resolved_config_sha256=_sha256_file(resolved_config_path),
        )

    def test_public_publisher_rejects_swapped_or_mixed_config(self) -> None:
        """Publisher mode/config binding is tested; semantic QA is mocked."""

        extracted = _compose_and_extract_personal_skill(self.root)
        preflight, preflight_path = _public_preflight(extracted, self.root / "public-task")
        publisher = _publisher_module(extracted)
        config_path = extracted / "config" / "default.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        public_inventory = _public_inventory(master_available=True)
        public_package = {
            "resource_inventory": public_inventory,
            "index_evidence": {"mode": "public-core"},
        }

        def attempt(
            *,
            path: Path,
            value: dict[str, object],
            output_name: str,
            binding: dict[str, object],
            package: dict[str, object] = public_package,
        ) -> None:
            report_path = self.root / f"{output_name}-report.json"
            report = {
                "run_id": preflight["run_binding"]["run_id"],
                "task_request_sha256": preflight["run_binding"]["task_request_sha256"],
                "index_evidence": {"mode": "public-core"},
            }
            report_path.write_bytes(_json_bytes(report))
            pptx = self.root / f"{output_name}.pptx"
            pptx.write_bytes(b"synthetic public-core pptx payload")
            with mock.patch.object(publisher, "validate_report", return_value=[]), mock.patch.object(publisher, "_records_required", return_value=False):
                with self.assertRaises(RuntimeError):
                    publisher.publish_supervised_pair(
                        package=package,
                        plan={},
                        qa={},
                        inventory=public_inventory,
                        report=report,
                        report_path=report_path,
                        pptx=pptx,
                        runtime_preflight=binding,
                        runtime_preflight_sha256=_sha256_file(preflight_path),
                        resolved_config=value,
                        resolved_config_sha256=_sha256_file(path),
                        config_path=path,
                        output_dir=self.root / output_name,
                    )
            self.assertFalse((self.root / output_name).exists())

        swapped = extracted / "config" / "swapped-public.json"
        swapped.write_bytes(config_path.read_bytes())
        attempt(path=swapped, value=config, output_name="swapped", binding=preflight)

        mixed_modes = {
            "resource_inventory": public_inventory,
            "index_evidence": {"mode": "owner-personal"},
        }
        attempt(path=config_path, value=config, output_name="mixed-modes", binding=preflight, package=mixed_modes)

        mixed = copy.deepcopy(config)
        mixed["theme"]["profile"] = "mixed-private"
        mixed_binding = copy.deepcopy(preflight)
        mixed_binding["config_binding"] = dict(preflight["config_binding"])
        mixed_binding["config_binding"]["sha256"] = sha256_json(mixed)
        attempt(path=config_path, value=mixed, output_name="mixed", binding=mixed_binding)

        runtime_lock_path = extracted / "runtime" / "runtime-lock.json"
        original_lock = runtime_lock_path.read_bytes()
        tampered_lock = json.loads(original_lock)
        tampered_lock["artifact_sha256"]["config/default.json"] = "0" * 64
        runtime_lock_path.write_bytes(_json_bytes(tampered_lock))
        attempt(path=config_path, value=config, output_name="tampered-lock", binding=preflight)
        runtime_lock_path.write_bytes(original_lock)

        tampered_config = copy.deepcopy(config)
        tampered_config["theme"]["profile"] = "tampered-public"
        config_path.write_bytes(_json_bytes(tampered_config))
        attempt(path=config_path, value=tampered_config, output_name="tampered-config", binding=preflight)

    def test_public_index_cli_retrieval_and_finalize_use_only_bundled_provider(self) -> None:
        request_path = self.root / "public-request.json"
        request_path.write_bytes(
            _json_bytes(
                {
                    "contract": "io.clayz.presentation.retrieval-request/1.0",
                    "request_id": "public.optional.library",
                    "stage": "logic",
                    "query": "evidence research reasoning for a presentation decision",
                    "intent": "task-reference",
                    "rights_context": "public-open-source",
                    "filters": {
                        "provider_ids": ["builtin-catalog"],
                        "task_modes": ["new-build"],
                        "languages": ["en-US"],
                    },
                    "limit": 5,
                    "task_context": {
                        "decision_goal": "select a public reasoning method",
                        "target_refs": ["logic:brief"],
                        "format_need": "task-reference",
                    },
                    "ranking_policy": {
                        "profile": "content",
                        "minimum_score": 0.0,
                        "max_selected": 1,
                        "diversity_lambda": 0.7,
                    },
                }
            )
        )
        receipt_path = self.root / "public-receipt.json"
        provider = f"builtin-catalog={PUBLIC_INDEX_PATH}"
        searched = _run_process(
            [
                ROOT / "scripts" / "index_runtime_cli.py",
                "--root",
                self.root,
                "search",
                "--provider",
                provider,
                "--request",
                request_path,
                "--receipt",
                receipt_path,
            ],
            cwd=self.root,
        )
        self.assertEqual(searched.returncode, 0, searched.stderr or searched.stdout)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["index_snapshot"][0]["provider_id"], "builtin-catalog")
        self.assertGreaterEqual(len(receipt["candidates"]), 1)
        selected_id = receipt["candidates"][0]["record_id"]
        finalized_path = self.root / "public-finalized-receipt.json"
        finalized = _run_process(
            [
                ROOT / "scripts" / "index_runtime_cli.py",
                "--root",
                self.root,
                "finalize",
                "--provider",
                provider,
                "--receipt",
                receipt_path,
                "--selected",
                f"{selected_id}=supports the public Logic decision",
                "--output",
                finalized_path,
            ],
            cwd=self.root,
        )
        self.assertEqual(finalized.returncode, 0, finalized.stderr or finalized.stdout)
        result = json.loads(finalized_path.read_text(encoding="utf-8"))
        self.assertEqual(result["selection"]["selected"][0]["record_id"], selected_id)
        self.assertEqual(result["selection"]["selected"][0]["adoption_status"], "planned")
        self.assertFalse(result["fallback"]["used"])
        self.assertEqual({item["provider_id"] for item in result["index_snapshot"]}, {"builtin-catalog"})

    def test_owner_personal_missing_required_provider_is_fail_closed(self) -> None:
        extracted = _compose_and_extract_personal_skill(self.root)
        runtime = json.loads((extracted / "runtime" / "personal-extension.json").read_text(encoding="utf-8"))
        public_manifest = json.loads((extracted / "catalog" / "provider-manifest.json").read_text(encoding="utf-8"))
        snapshots = [
            public_manifest["index"]["snapshot"],
            {"provider_id": "task-private-learning", "digest": "2" * 64, "record_count": 1},
        ]
        snapshots.sort(key=lambda item: item["provider_id"])
        evidence = {
            "contract": INDEX_EVIDENCE_CONTRACT,
            "mode": "owner-personal",
            "runtime_lock_digest": runtime["lock"]["digest"],
            "provider_lock": {
                "lock_id": "synthetic-owner-lock",
                "snapshots": snapshots,
                "lock_sha256": sha256_json(snapshots),
            },
            "owner_materialization": {
                "status": "materialized",
                "source_manifest_sha256": "3" * 64,
                "materialization_report_sha256": "4" * 64,
                "provider_id": "task-private-learning",
                "record_count": 1,
                "required_sources": [{"source_id": "source-1", "stages": ["logic"]}],
                "materialized_source_ids": ["source-1"],
                "missing_source_ids": [],
            },
            "stage_receipts": {},
        }
        errors: list[str] = []
        with mock.patch.object(index_evidence_validator, "ROOT", extracted):
            index_evidence_validator.validate_index_evidence(evidence, [], "evidence", errors)
        self.assertTrue(
            any("example.private-library" in error for error in errors),
            errors,
        )
        self.assertTrue(any("owner-personal mode requires" in error for error in errors), errors)

    def test_public_inventory_allows_unselected_owner_scope_but_keeps_required_master_gate(self) -> None:
        ready = _public_inventory(master_available=True)
        ready_errors: list[str] = []
        validate_resource_inventory(ready, "public-ready", ready_errors, require_ready=True)
        self.assertEqual(ready_errors, [])
        self.assertEqual(
            next(item for item in ready["scan_scope"] if item["scope"] == "owner-library")["status"],
            "not-applicable",
        )
        self.assertEqual(ready["runtime_mode"], "public-core")

        missing_master = _public_inventory(master_available=False)
        missing_errors: list[str] = []
        validate_resource_inventory(missing_master, "public-missing-master", missing_errors, require_ready=False)
        self.assertEqual(missing_errors, [])
        self.assertEqual(missing_master["gate"]["status"], "blocked")
        self.assertIn("task.master", missing_master["gate"]["blocking_resource_ids"])
        self.assertFalse(missing_master["gate"]["authoring_may_start"])


if __name__ == "__main__":
    unittest.main()
