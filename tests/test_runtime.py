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

    def test_pack_builder_includes_one_os_pack(self) -> None:
        module = load_module("build_runtime_packs_unit", ROOT / "scripts" / "build_runtime_packs.py")
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temporary:
            archive = module.build("windows", Path(temporary), version)
            with zipfile.ZipFile(archive) as package:
                names = set(package.namelist())
            self.assertIn("clayz-presentation-skills/packages/runtime/packs/windows/runtime-pack.json", names)
            self.assertIn("clayz-presentation-skills/packages/runtime/packs/common/runtime-pack.json", names)
            self.assertFalse(any("/packs/linux/" in name or "/packs/macos/" in name for name in names))
            self.assertIn("clayz-presentation-skills/runtime/runtime-lock.json", names)

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
