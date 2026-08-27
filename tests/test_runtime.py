from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeTests(unittest.TestCase):
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
            report = module.build_preflight_report(config, model_profile="D")
        self.assertEqual(report["contract"], "io.clayz.presentation.runtime-preflight/1.0")
        self.assertEqual(report["model"]["profile"], "D")
        self.assertEqual(report["selected_route"]["authoring_backend"], "python-pptx")
        self.assertEqual(report["selected_route"]["render_backend"], "powerpoint-com")
        self.assertTrue(report["selected_route"]["locked"])
        self.assertFalse(report["selected_route"]["host_model_private_tool_required"])
        self.assertEqual(report["budgets"]["maximum_capability_scans"], 1)
        self.assertEqual(report["budgets"]["maximum_route_switches"], 0)

    def test_platform_pack_manifests_keep_pdf_lazy(self) -> None:
        pack_root = ROOT / "packages" / "runtime" / "packs"
        for name in ("common", "windows", "macos", "linux"):
            manifest = json.loads((pack_root / name / "runtime-pack.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["contract"], "io.clayz.presentation.runtime-pack/1.0")
        self.assertEqual(json.loads((pack_root / "windows" / "runtime-pack.json").read_text(encoding="utf-8"))["pdf_support"]["mode"], "lazy")

    def test_windows_com_is_authoring_fallback_without_python_pptx(self) -> None:
        module = load_module("runtime_preflight_windows_fallback", ROOT / "packages" / "runtime" / "preflight.py")
        config = json.loads((ROOT / "config" / "default.json").read_text(encoding="utf-8"))
        with (
            mock.patch.object(module, "_module", return_value=False),
            mock.patch.object(module, "_artifact_tool", return_value={"available": False, "node": None, "node_modules": None, "bin_dir": None, "package": None}),
            mock.patch.object(module, "_windows_powerpoint", return_value={"available": True, "evidence": "synthetic"}),
            mock.patch.object(module, "_command", return_value=None),
        ):
            report = module.build_preflight_report(
                config,
                model_profile="A",
                required_capabilities=["editable-text", "editable-shapes", "images", "tables", "render-preview", "pptx-inspection"],
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
            report = module.build_preflight_report(
                config,
                model_profile="A",
                host_capabilities={"host": "chatgpt-personal", "available": True, "capabilities": capabilities},
            )
        self.assertEqual(report["dependencies"]["host_tools"]["host"], "chatgpt-personal")
        self.assertEqual(report["selected_route"]["route_id"], "native-presentation-tool+native-presentation-tool")
        self.assertTrue(report["selected_route"]["available"])

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
