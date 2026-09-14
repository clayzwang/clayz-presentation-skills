# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

from tests.test_runtime import inspected_host


ROOT = Path(__file__).resolve().parents[1]


def load_preflight():
    spec = importlib.util.spec_from_file_location(
        "runtime_preflight_fidelity",
        ROOT / "packages" / "runtime" / "preflight.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load runtime preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def component_gate(config: dict[str, object]) -> dict[str, object]:
    version = str(config["identity"]["version"])
    return {
        "artifact": "synthetic-component-version-report.json",
        "sha256": "b" * 64,
        "generated_at": "2026-09-14T00:00:00+00:00",
        "status": "latest",
        "local_release_version": version,
        "latest_release_version": version,
        "manifest_sha256": "c" * 64,
        "all_components_current": True,
    }


def public_config() -> dict[str, object]:
    return json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))


def runtime_dependencies(module, *, pptx: bool, libreoffice: bool = False, powerpoint: bool = False):
    def module_probe(name: str) -> bool:
        return name == "pptx" and pptx

    def command_probe(*names: str) -> str | None:
        return "C:/synthetic/soffice.exe" if libreoffice and "soffice" in names else None

    return mock.patch.object(module, "_module", side_effect=module_probe), mock.patch.object(
        module,
        "_artifact_tool",
        return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None},
    ), mock.patch.object(
        module,
        "_windows_powerpoint",
        return_value={"available": powerpoint, "evidence": "synthetic" if powerpoint else None},
    ), mock.patch.object(module, "_command", side_effect=command_probe)


class PreflightFidelityTests(unittest.TestCase):
    def test_master_quality_gaps_keep_required_list_but_allow_real_python_author(self) -> None:
        module = load_preflight()
        config = public_config()
        config["theme"]["source"] = "user-master"
        config["theme"]["master_path"] = "task://user-master.pptx"
        required = config["renderer"]["required_capabilities"]
        required.extend(["master-preservation", "layout-inheritance", "east-asian-font-name"])

        patches = runtime_dependencies(module, pptx=True)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["route_id"], "python-pptx+none")
        self.assertFalse(selected["available"])
        self.assertTrue(selected["attemptable"])
        self.assertEqual(selected["assurance_level"], "runtime-probed")
        self.assertEqual(set(config["renderer"]["required_capabilities"]), set(report["required_capabilities"]))
        self.assertTrue({"master-preservation", "layout-inheritance", "east-asian-font-name"}.issubset(
            set(selected["missing_capabilities"])
        ))
        self.assertIn("render-preview", selected["missing_capabilities"])
        warning_text = " ".join(report["warnings"])
        self.assertIn("real PPTX authoring route is available", warning_text)
        self.assertIn("unverified/pending", warning_text)
        self.assertIn("master-preservation", warning_text)

    def test_real_renderer_is_preferred_while_master_fidelity_stays_pending(self) -> None:
        module = load_preflight()
        config = public_config()
        config["theme"]["source"] = "user-master"
        config["theme"]["master_path"] = "task://user-master.pptx"
        config["renderer"]["required_capabilities"].extend([
            "master-preservation", "layout-inheritance", "east-asian-font-name",
        ])

        patches = runtime_dependencies(module, pptx=True, libreoffice=True)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["route_id"], "python-pptx+libreoffice")
        self.assertFalse(selected["available"])
        self.assertTrue(selected["attemptable"])
        self.assertEqual(
            set(selected["missing_capabilities"]),
            {"master-preservation", "layout-inheritance", "east-asian-font-name"},
        )

    def test_unknown_non_execution_capability_remains_pending_with_real_writer(self) -> None:
        module = load_preflight()
        config = public_config()
        config["theme"]["source"] = "user-master"
        config["theme"]["master_path"] = "task://user-master.pptx"
        config["renderer"]["required_capabilities"].extend([
            "master-preservation", "layout-inheritance", "east-asian-font-name", "future-template-check",
        ])

        patches = runtime_dependencies(module, pptx=True)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["authoring_backend"], "python-pptx")
        self.assertTrue(selected["attemptable"])
        self.assertIn("future-template-check", selected["missing_capabilities"])
        self.assertIn("future-template-check", " ".join(report["warnings"]))

    def test_missing_real_authoring_core_still_blocks_calibrated_route(self) -> None:
        module = load_preflight()
        config = public_config()
        config["theme"]["source"] = "user-master"
        config["theme"]["master_path"] = "task://user-master.pptx"
        config["renderer"]["required_capabilities"].extend([
            "master-preservation", "layout-inheritance", "east-asian-font-name",
        ])
        # Simulate an author backend whose declaration does not cover the
        # configured editable-shape core requirement.
        capabilities = [
            item for item in config["renderer"]["required_capabilities"] if item != "editable-shapes"
        ]
        host, challenge, challenge_sha256, binding = inspected_host(module, capabilities)
        patches = runtime_dependencies(module, pptx=False)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["authoring_backend"], "spec-only")
        self.assertFalse(selected["attemptable"])
        self.assertIn("editable-shapes", selected["missing_capabilities"])
        self.assertTrue(any("No executable PPTX authoring route" in warning for warning in report["warnings"]))

    def test_host_authoring_without_render_capability_cannot_become_renderer(self) -> None:
        module = load_preflight()
        config = public_config()
        capabilities = [
            item for item in config["renderer"]["required_capabilities"]
            if item not in {"render-preview", "pptx-inspection"}
        ]
        host, challenge, challenge_sha256, binding = inspected_host(module, capabilities)

        patches = runtime_dependencies(module, pptx=False)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["authoring_backend"], "native-presentation-tool")
        self.assertEqual(selected["render_backend"], "none")
        self.assertTrue(selected["attemptable"])
        self.assertFalse(selected["available"])
        self.assertIn("render-preview", selected["missing_capabilities"])
        self.assertIn("pptx-inspection", selected["missing_capabilities"])

    def test_render_only_host_declaration_cannot_be_used_as_writer(self) -> None:
        module = load_preflight()
        config = public_config()
        config["renderer"]["required_capabilities"] = ["render-preview"]
        host, challenge, challenge_sha256, binding = inspected_host(module, ["render-preview"])

        patches = runtime_dependencies(module, pptx=False)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
                host_capabilities=host,
                run_challenge=challenge,
                run_challenge_sha256=challenge_sha256,
                run_challenge_issuance=binding["issuance"],
                run_challenge_consumption=binding["consumption"],
                host_attestation_context=binding["context"],
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["authoring_backend"], "spec-only")
        self.assertFalse(selected["attemptable"])
        self.assertTrue(any("No executable PPTX authoring route" in warning for warning in report["warnings"]))

    def test_legacy_route_keeps_strict_capability_semantics(self) -> None:
        module = load_preflight()
        config = public_config()
        config["workflow"]["delivery_policy"]["mode"] = "legacy"
        config["theme"]["source"] = "user-master"
        config["theme"]["master_path"] = "task://user-master.pptx"
        config["renderer"]["required_capabilities"].extend([
            "master-preservation", "layout-inheritance", "east-asian-font-name",
        ])

        patches = runtime_dependencies(module, pptx=True)
        for patch in patches:
            patch.start()
        try:
            report = module.build_preflight_report(
                config,
                model_profile="A",
                component_version_gate=component_gate(config),
            )
        finally:
            for patch in reversed(patches):
                patch.stop()

        selected = report["selected_route"]
        self.assertEqual(selected["authoring_backend"], "spec-only")
        self.assertFalse(selected["available"])
        self.assertFalse(selected["attemptable"])
        self.assertTrue({"master-preservation", "layout-inheritance", "east-asian-font-name"}.issubset(
            set(selected["missing_capabilities"])
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
