"""Exercise actual Office on a host with LibreOffice, Poppler and python-pptx."""
from pathlib import Path
import shutil
import subprocess

import pytest

from test_training_operations import frozen_run, io, load_script, ops


def test_real_office_reopens_three_times(tmp_path):
    if any(shutil.which(name) is None for name in ("libreoffice", "fc-match", "pdftoppm", "pdffonts")):
        pytest.skip("real LibreOffice and Poppler binaries required")
    pptx_module = pytest.importorskip("pptx")
    root = tmp_path / "case"
    native = frozen_run(root, current=True)
    deck = pptx_module.Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[5])
    slide.shapes.title.text = "Independent reopen regression"
    source = root / "source.pptx"
    deck.save(source)
    expected = io.digest(source.read_bytes())
    font = subprocess.check_output(["fc-match", "--format=%{file}", "Liberation Sans"], text=True)
    renderer = load_script("render_regression", "render_native_preview.py")
    profiles = set()
    for i in range(3):
        target = root / f"render-{i}"
        manifest = renderer.render(source, target, ["p01"], font_file=font,
                                   font_family="Liberation Sans", training_run=root)
        assert manifest["pptx"]["sha256"] == expected
        assert (target / "p01.png").is_file() and Path(manifest["pdf"]["path"]).is_file()
        if shutil.which("pdftotext"):
            text = subprocess.check_output(["pdftotext", manifest["pdf"]["path"], "-"], text=True)
            assert "Independent reopen regression" in " ".join(text.split())
        profile_command = io.read(target / "office-launch.json")["command"][1]
        profiles.add(profile_command)
    assert len(profiles) == 3
    counts = ops.report(root, native)["counts"]
    assert counts["office_processes"] == counts["full_deck_renders"] == 3
