from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "run-test-runtime"
TASK_REQUEST_SHA256 = "a" * 64
COMPONENT_VERSION_GATE = {
    "artifact": "component-version-report.json",
    "sha256": "b" * 64,
    "generated_at": "2026-09-01T00:00:00+00:00",
    "status": "latest",
    "local_release_version": "0.8.0",
    "latest_release_version": "0.8.0",
    "manifest_sha256": "c" * 64,
    "all_components_current": True,
}


def inspected_host(module, capabilities: list[str]) -> tuple[dict[str, object], dict[str, str], str, dict[str, object]]:
    root = Path(tempfile.mkdtemp(prefix="clayz-runtime-ledger-test-"))
    unittest.addModuleCleanup(shutil.rmtree, root, ignore_errors=True)
    challenge = module.issue_run_challenge(
        b"synthetic current presentation request",
        task_root=root,
    )
    challenge_sha256 = module._challenge_digest(challenge)
    receipt = {
        "artifact": "host-tool-inventory.json",
        "sha256": "c" * 64,
        "contract": module.HOST_INVENTORY_CONTRACT,
    }
    host = {
        "contract": module.HOST_ATTESTATION_CONTRACT,
        "host": "chatgpt-personal",
        "available": True,
        "capabilities": capabilities,
        "run_id": challenge["run_id"],
        "task_request_sha256": challenge["task_request_sha256"],
        "nonce": challenge["nonce"],
        "challenge_sha256": challenge_sha256,
        "source": "host-inspection",
        "observed_at": challenge["issued_at"],
        "evidence_receipts": [receipt],
    }
    issuance_record = {
        "contract": module.RUN_CHALLENGE_ISSUANCE_CONTRACT,
        "challenge_sha256": challenge_sha256,
        "run_id": challenge["run_id"],
        "task_request_sha256": challenge["task_request_sha256"],
        "nonce": challenge["nonce"],
        "task_root_sha256": challenge["task_root_sha256"],
        "issued_at": challenge["issued_at"],
        "expires_at": challenge["expires_at"],
    }
    issuance_path = root / Path(challenge["issuance_record"])
    issuance_path.parent.mkdir(parents=True, exist_ok=True)
    issuance_raw = (json.dumps(issuance_record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    issuance_path.write_bytes(issuance_raw)
    issuance = {
        **issuance_record,
        "receipt_path": issuance_path.resolve().as_posix(),
        "receipt_sha256": hashlib.sha256(issuance_raw).hexdigest(),
    }
    consumption_record = {
        "contract": module.RUN_CHALLENGE_CONSUMPTION_CONTRACT,
        "challenge_sha256": challenge_sha256,
        "run_id": challenge["run_id"],
        "task_request_sha256": challenge["task_request_sha256"],
        "nonce": challenge["nonce"],
        "task_root_sha256": challenge["task_root_sha256"],
        "consumed_at": challenge["issued_at"],
    }
    consumption_path = root / ".clayz-run-challenges" / "consumed" / f"{challenge_sha256}.json"
    consumption_path.parent.mkdir(parents=True, exist_ok=True)
    consumption_raw = (json.dumps(consumption_record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    consumption_path.write_bytes(consumption_raw)
    consumption = {
        **consumption_record,
        "receipt_path": consumption_path.resolve().as_posix(),
        "receipt_sha256": hashlib.sha256(consumption_raw).hexdigest(),
    }
    context = {"validated": True, "challenge_sha256": challenge_sha256, "evidence_receipts": [receipt]}
    return host, challenge, challenge_sha256, {"context": context, "issuance": issuance, "consumption": consumption}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeTests(unittest.TestCase):
    def test_preflight_rejects_missing_component_version_gate(self) -> None:
        module = load_module("runtime_preflight_requires_latest_components", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "component version report"):
            module.build_preflight_report(config, model_profile="D")

    def test_model_profiles_are_capability_based(self) -> None:
        module = load_module("runtime_preflight_unit", ROOT / "packages" / "runtime" / "preflight.py")
        self.assertEqual(module.classify_model_profile({"tool_calling": True, "structured_output": True, "visual_inspection": True}), "A")
        self.assertEqual(module.classify_model_profile({"tool_calling": True, "structured_output": True}), "B")
        self.assertEqual(module.classify_model_profile({"structured_output": True}), "C")
        self.assertEqual(module.classify_model_profile({}), "D")

    def test_preflight_locks_host_independent_baseline(self) -> None:
        module = load_module("runtime_preflight_lock", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        fake_modules = {"pptx": True, "PIL": True, "yaml": True}
        with (
            mock.patch.object(module, "_module", side_effect=lambda name: fake_modules.get(name, False)),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": True, "evidence": "synthetic"}),
            mock.patch.object(module, "_command", return_value=None),
        ):
            report = module.build_preflight_report(config, model_profile="D", component_version_gate=COMPONENT_VERSION_GATE)
        self.assertEqual(report["contract"], "io.clayz.presentation.runtime-preflight/1.3")
        self.assertEqual(report["model"]["profile"], "D")
        self.assertEqual(report["selected_route"]["authoring_backend"], "python-pptx")
        self.assertEqual(report["selected_route"]["render_backend"], "powerpoint-com")
        self.assertTrue(report["selected_route"]["locked"])
        self.assertFalse(report["selected_route"]["host_model_private_tool_required"])
        self.assertEqual(report["budgets"]["maximum_capability_scans"], 1)
        self.assertEqual(report["budgets"]["maximum_route_switches"], 0)
        checks = {item["application"]: item for item in report["target_application_checks"]}
        self.assertEqual(checks["powerpoint"]["availability"], "available")
        self.assertFalse(checks["powerpoint"]["blocks_authoring"])

    def test_unavailable_native_target_apps_are_recorded_without_blocking_authoring(self) -> None:
        module = load_module("runtime_preflight_acceptance_observation", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        private_capabilities = list(config["renderer"]["required_capabilities"]) + [
            "owner-private-library", "master-preservation", "layout-inheritance",
            "east-asian-font-name", "ooxml-repair",
        ]
        config["renderer"]["required_capabilities"] = private_capabilities

        def command(*names: str) -> str | None:
            return "C:/synthetic/soffice.exe" if "soffice" in names else None

        with (
            mock.patch.object(module, "_module", return_value=False),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": False, "evidence": None}),
            mock.patch.object(module, "_command", side_effect=command),
        ):
            host, challenge, challenge_sha256, binding = inspected_host(module, private_capabilities)
            report = module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )

        self.assertFalse(report["selected_route"]["available"])
        self.assertTrue(report["selected_route"]["attemptable"])
        self.assertEqual(report["selected_route"]["assurance_level"], "host-declared-unverified")
        checks = {item["application"]: item for item in report["target_application_checks"]}
        self.assertEqual(checks["powerpoint"]["availability"], "unavailable")
        self.assertEqual(checks["powerpoint"]["disposition"], "deferred-and-recorded")
        self.assertEqual(checks["wps"]["availability"], "unavailable")
        self.assertEqual(checks["libreoffice"]["availability"], "available")
        self.assertTrue(report["guards"]["target_application_checks_do_not_block_authoring"])

    def test_require_flag_can_only_add_to_configured_capabilities(self) -> None:
        module = load_module("runtime_preflight_additive_requirements", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        configured = set(config["renderer"]["required_capabilities"])
        with (
            mock.patch.object(module, "_module", return_value=False),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": False, "evidence": None}),
            mock.patch.object(module, "_command", return_value=None),
        ):
            report = module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
                required_capabilities=["structured-spec"],
                run_id=RUN_ID,
                task_request_sha256=TASK_REQUEST_SHA256,
            )
        self.assertTrue(configured.issubset(set(report["required_capabilities"])))
        self.assertIn("structured-spec", report["required_capabilities"])

    def test_available_host_capabilities_must_be_bound_to_current_run(self) -> None:
        module = load_module("runtime_preflight_host_binding", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        host, challenge, challenge_sha256, binding = inspected_host(module, list(config["renderer"]["required_capabilities"]))
        host["run_id"] = "run-other"
        with self.assertRaisesRegex(ValueError, "run challenge run_id"):
            module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )

    def test_host_declaration_cannot_self_mark_verified_without_evidence_context(self) -> None:
        module = load_module("runtime_preflight_host_evidence", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        host, challenge, challenge_sha256, binding = inspected_host(module, list(config["renderer"]["required_capabilities"]))
        host["verified"] = True
        with self.assertRaisesRegex(ValueError, "file-validated evidence receipts"):
            module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
            )

    def test_expired_run_challenge_is_rejected(self) -> None:
        module = load_module("runtime_preflight_expired_challenge", ROOT / "packages" / "runtime" / "preflight.py")
        challenge = module.issue_run_challenge(
            b"expired synthetic presentation request",
            now=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        with self.assertRaisesRegex(ValueError, "not current"):
            module.validate_run_challenge(challenge, challenge_sha256=module._challenge_digest(challenge))

    def test_run_challenge_can_be_consumed_only_once(self) -> None:
        module = load_module("runtime_preflight_cli_consumption", ROOT / "scripts" / "runtime_preflight.py")
        challenge_module = load_module("runtime_preflight_challenge_source", ROOT / "packages" / "runtime" / "preflight.py")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "run-challenge.json"
            challenge = challenge_module.issue_run_challenge(
                b"one-use presentation request",
                task_root=path.parent,
            )
            path.write_text(json.dumps(challenge), encoding="utf-8")
            digest = "e" * 64
            module._consume_challenge(path, challenge, digest)
            with self.assertRaisesRegex(ValueError, "already consumed"):
                module._consume_challenge(path, challenge, digest)

    def test_copying_a_challenge_file_cannot_bypass_the_task_ledger(self) -> None:
        module = load_module("runtime_preflight_cli_copy_replay", ROOT / "scripts" / "runtime_preflight.py")
        challenge_module = load_module("runtime_preflight_copy_replay_source", ROOT / "packages" / "runtime" / "preflight.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "challenge-a.json"
            second = root / "challenge-b.json"
            challenge = challenge_module.issue_run_challenge(b"copy replay request", task_root=root)
            payload = json.dumps(challenge)
            first.write_text(payload, encoding="utf-8")
            second.write_text(payload, encoding="utf-8")
            digest = "f" * 64
            module._consume_challenge(first, challenge, digest)
            with self.assertRaisesRegex(ValueError, "already consumed"):
                module._consume_challenge(second, challenge, digest)

    def test_copying_a_challenge_to_another_task_root_is_rejected(self) -> None:
        module = load_module("runtime_preflight_cli_cross_root", ROOT / "scripts" / "runtime_preflight.py")
        challenge_module = load_module("runtime_preflight_cross_root_source", ROOT / "packages" / "runtime" / "preflight.py")
        with tempfile.TemporaryDirectory() as first_root, tempfile.TemporaryDirectory() as second_root:
            first = Path(first_root) / "run-challenge.json"
            copied = Path(second_root) / "run-challenge.json"
            challenge = challenge_module.issue_run_challenge(b"cross-root request", task_root=Path(first_root))
            payload = json.dumps(challenge)
            first.write_text(payload, encoding="utf-8")
            copied.write_text(payload, encoding="utf-8")
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            with self.assertRaisesRegex(ValueError, "bound to the current task root"):
                module._consume_challenge(copied, challenge, digest)

    def test_script_issuer_materializes_a_hash_checked_canonical_issuance_record(self) -> None:
        module = load_module("runtime_preflight_cli_issuance", ROOT / "scripts" / "runtime_preflight.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            task_request = root / "task-request.txt"
            challenge_path = root / "run-challenge.json"
            task_request.write_bytes(b"canonical task request")
            module._issue_challenge(task_request, challenge_path)
            challenge_raw = challenge_path.read_bytes()
            challenge = json.loads(challenge_raw)
            receipt = module._validate_issuance_receipt(
                challenge_path,
                challenge,
                hashlib.sha256(challenge_raw).hexdigest(),
            )
            self.assertEqual(receipt["contract"], module.RUN_CHALLENGE_ISSUANCE_CONTRACT)
            self.assertTrue(Path(str(receipt["receipt_path"])).is_file())

    def test_in_memory_receipt_claims_without_canonical_files_are_rejected(self) -> None:
        module = load_module("runtime_preflight_fake_ledgers", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            challenge = module.issue_run_challenge(b"fake receipt request", task_root=root)
            challenge_sha256 = module._challenge_digest(challenge)
            issuance = {
                "contract": module.RUN_CHALLENGE_ISSUANCE_CONTRACT,
                "challenge_sha256": challenge_sha256,
                "run_id": challenge["run_id"],
                "task_request_sha256": challenge["task_request_sha256"],
                "nonce": challenge["nonce"],
                "task_root_sha256": challenge["task_root_sha256"],
                "issued_at": challenge["issued_at"],
                "expires_at": challenge["expires_at"],
                "receipt_path": (root / Path(challenge["issuance_record"])).resolve().as_posix(),
                "receipt_sha256": "e" * 64,
            }
            consumption = {
                "contract": module.RUN_CHALLENGE_CONSUMPTION_CONTRACT,
                "challenge_sha256": challenge_sha256,
                "run_id": challenge["run_id"],
                "task_request_sha256": challenge["task_request_sha256"],
                "nonce": challenge["nonce"],
                "task_root_sha256": challenge["task_root_sha256"],
                "consumed_at": challenge["issued_at"],
                "receipt_path": (
                    root / ".clayz-run-challenges" / "consumed" / f"{challenge_sha256}.json"
                ).resolve().as_posix(),
                "receipt_sha256": "d" * 64,
            }
            with self.assertRaisesRegex(ValueError, "receipt file is missing"):
                module.build_preflight_report(
                    config,
                    component_version_gate=COMPONENT_VERSION_GATE,
                    run_challenge=challenge,
                    run_challenge_sha256=challenge_sha256,
                    run_challenge_issuance=issuance,
                    run_challenge_consumption=consumption,
                )

    def test_caller_constructed_challenge_without_issuance_receipt_is_rejected(self) -> None:
        module = load_module("runtime_preflight_caller_challenge", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        challenge = module.issue_run_challenge(b"caller constructed request")
        challenge_sha256 = module._challenge_digest(challenge)
        consumption = {
            "contract": module.RUN_CHALLENGE_CONSUMPTION_CONTRACT,
            "challenge_sha256": challenge_sha256,
            "run_id": challenge["run_id"],
            "task_request_sha256": challenge["task_request_sha256"],
            "nonce": challenge["nonce"],
            "task_root_sha256": challenge["task_root_sha256"],
            "receipt_path": "synthetic-consumption.json",
            "receipt_sha256": "d" * 64,
        }
        with self.assertRaisesRegex(ValueError, "issuance receipt"):
            module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_consumption=consumption,
            )

    def test_capability_scan_rejects_a_replayed_challenge_for_another_task(self) -> None:
        module = load_module("runtime_preflight_cli_task_binding", ROOT / "scripts" / "runtime_preflight.py")
        challenge_module = load_module("runtime_preflight_task_binding_source", ROOT / "packages" / "runtime" / "preflight.py")
        challenge = challenge_module.issue_run_challenge(b"original presentation request")
        with tempfile.TemporaryDirectory() as temporary:
            task_request = Path(temporary) / "current-task-request.txt"
            task_request.write_bytes(b"different presentation request")
            with self.assertRaisesRegex(ValueError, "does not match"):
                module._validate_task_request(task_request, challenge)

    def test_route_selection_can_pair_host_authoring_with_later_available_renderer(self) -> None:
        module = load_module("runtime_preflight_mixed_route", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        authoring_only = [
            capability for capability in config["renderer"]["required_capabilities"]
            if capability != "render-preview"
        ]

        def command(*names: str) -> str | None:
            return "C:/synthetic/soffice.exe" if "soffice" in names else None

        with (
            mock.patch.object(module, "_module", return_value=False),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": False, "evidence": None}),
            mock.patch.object(module, "_command", side_effect=command),
        ):
            host, challenge, challenge_sha256, binding = inspected_host(module, authoring_only)
            report = module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )

        self.assertEqual(report["selected_route"]["route_id"], "native-presentation-tool+libreoffice")
        self.assertFalse(report["selected_route"]["available"])
        self.assertTrue(report["selected_route"]["attemptable"])
        self.assertEqual(report["selected_route"]["assurance_level"], "host-declared-unverified")

    def test_platform_pack_manifests_keep_pdf_lazy(self) -> None:
        pack_root = ROOT / "packages" / "runtime" / "packs"
        for name in ("common", "windows", "macos", "linux"):
            manifest = json.loads((pack_root / name / "runtime-pack.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["contract"], "io.clayz.presentation.runtime-pack/1.0")
        self.assertEqual(json.loads((pack_root / "windows" / "runtime-pack.json").read_text(encoding="utf-8"))["pdf_support"]["mode"], "lazy")

    def test_windows_com_is_authoring_fallback_without_python_pptx(self) -> None:
        module = load_module("runtime_preflight_windows_fallback", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        config["renderer"]["required_capabilities"] = [
            "editable-text", "editable-shapes", "images", "tables", "render-preview", "pptx-inspection"
        ]
        with (
            mock.patch.object(module, "_module", return_value=False),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": True, "evidence": "synthetic"}),
            mock.patch.object(module, "_command", return_value=None),
        ):
            report = module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
            )
        self.assertEqual(report["selected_route"]["route_id"], "powerpoint-com+powerpoint-com")
        self.assertTrue(report["selected_route"]["available"])
        self.assertFalse(report["selected_route"]["host_model_private_tool_required"])

    def test_chatgpt_host_tools_form_the_cloud_execution_body(self) -> None:
        module = load_module("preflight_cloud_host", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        capabilities = list(config["renderer"]["required_capabilities"]) + ["svg", "speaker-notes"]
        with (
            mock.patch.object(module, "_module", return_value=False),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": False, "evidence": None}),
            mock.patch.object(module, "_command", return_value=None),
        ):
            host, challenge, challenge_sha256, binding = inspected_host(module, capabilities)
            report = module.build_preflight_report(
                config,
                component_version_gate=COMPONENT_VERSION_GATE,
                model_profile="A",
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )
        self.assertEqual(report["dependencies"]["host_tools"]["host"], "chatgpt-personal")
        observation = report["dependencies"]["host_tools"]["observation"]
        self.assertEqual(observation["verification_status"], "challenge-bound-host-declaration")
        self.assertEqual(observation["assurance_level"], "host-declared-unverified")
        self.assertFalse(observation["route_eligible"])
        self.assertNotIn("verified", observation)
        self.assertEqual(report["selected_route"]["route_id"], "native-presentation-tool+native-presentation-tool")
        self.assertFalse(report["selected_route"]["available"])
        self.assertTrue(report["selected_route"]["attemptable"])

    def test_release_builder_separates_light_plugin_and_offline_wheels(self) -> None:
        module = load_module("build_runtime_packs_unit", ROOT / "scripts" / "build_runtime_packs.py")
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            local_light = module.build_light(temporary_root, version, "local")
            cloud_light = module.build_light(temporary_root, version, "cloud")
            with zipfile.ZipFile(local_light) as package:
                local_names = set(package.namelist())
                local_lock = json.loads(package.read("clayz-presentation-skills/runtime/runtime-lock.json"))
            with zipfile.ZipFile(cloud_light) as package:
                cloud_names = set(package.namelist())
                cloud_lock = json.loads(package.read("clayz-presentation-skills/runtime/runtime-lock.json"))
            self.assertIn("clayz-presentation-skills/packages/runtime/packs/windows/runtime-pack.json", local_names)
            self.assertIn("clayz-presentation-skills/packages/runtime/packs/common/runtime-pack.json", local_names)
            self.assertNotIn("clayz-presentation-skills/packages/runtime/packs/windows/runtime-pack.json", cloud_names)
            self.assertFalse(any("/packages/adapters/" in name for name in cloud_names))
            self.assertIn("clayz-presentation-skills/catalog/provider-manifest.json", cloud_names)
            self.assertEqual(local_lock["public_core_sha256"], cloud_lock["public_core_sha256"])
            self.assertEqual(cloud_lock["tool_boundary"], "host-provided")
            self.assertFalse(any("/experience/" in name or "/assets/showcase/" in name for name in local_names | cloud_names))
            self.assertFalse(any(name.endswith(".whl") for name in local_names | cloud_names))

            wheel_dir = temporary_root / "wheels" / "windows"
            wheel_dir.mkdir(parents=True)
            for distribution, dependency_version in module.REQUIRED_DISTRIBUTIONS.items():
                filename = f"{distribution.replace('-', '_')}-{dependency_version}-py3-none-any.whl"
                with zipfile.ZipFile(wheel_dir / filename, "w") as wheel:
                    wheel.writestr(
                        f"{distribution.replace('-', '_')}-{dependency_version}.dist-info/licenses/LICENSE",
                        "synthetic permissive license\n",
                    )
            offline = module.build_offline("windows", temporary_root / "wheels", temporary_root, version)
            with zipfile.ZipFile(offline) as package:
                offline_names = set(package.namelist())
                lock = package.read("clayz-presentation-skills-offline/requirements.lock").decode("utf-8")
            self.assertIn("clayz-presentation-skills-offline/offline-pack.json", offline_names)
            self.assertIn("clayz-presentation-skills-offline/install_offline_dependencies.py", offline_names)
            self.assertEqual(sum(name.endswith(".whl") for name in offline_names), len(module.REQUIRED_DISTRIBUTIONS))
            self.assertIn("--hash=sha256:", lock)

    def test_public_core_digest_ignores_python_cache_files(self) -> None:
        module = load_module("build_runtime_packs_cache_hygiene", ROOT / "scripts" / "build_runtime_packs.py")
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            catalog = temporary_root / "catalog"
            catalog.mkdir()
            (catalog / "provider-manifest.json").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(module, "ROOT", temporary_root):
                clean_digest = module.public_core_digest()
                cache = catalog / "__pycache__"
                cache.mkdir()
                (cache / "provider.cpython-312.pyc").write_bytes(b"synthetic cache")
                self.assertEqual(module.public_core_digest(), clean_digest)

    def test_release_audit_rejects_external_denylist_text(self) -> None:
        module = load_module("build_runtime_packs_brand_audit", ROOT / "scripts" / "build_runtime_packs.py")
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "candidate.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("package/readme.txt", "synthetic-private-company")
            with self.assertRaises(ValueError):
                module.audit_archive(archive, ("synthetic-private-company",))
            self.assertFalse(archive.exists())

    def test_python_adapter_builds_editable_synthetic_deck(self) -> None:
        if importlib.util.find_spec("pptx") is None:
            self.skipTest("python-pptx is installed from requirements in CI and runtime packs")
        module = load_module("python_pptx_adapter_unit", ROOT / "packages" / "adapters" / "python_pptx" / "render.py")
        manifest = ROOT / "examples" / "synthetic-business-review" / "render-manifest.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "synthetic.pptx"
            module.render(manifest, output)
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertIn("COPY::COPY-S01-01::OBJECT-TITLE", slide_xml)
            self.assertIn("Evidence before implication", slide_xml)


if __name__ == "__main__":
    unittest.main()
