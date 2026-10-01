from __future__ import annotations

import sys
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from audit_ppt_font_names import audit_font_names  # noqa: E402


SLIDE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
 <p:cSld><p:spTree><p:sp><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r>
 <a:rPr><a:ea typeface="{font}"/><a:latin typeface="{font}"/></a:rPr>
 <a:t>中文字体检查</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>"""

THEME_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Synthetic">
 <a:themeElements><a:fontScheme name="Synthetic"><a:majorFont><a:latin typeface="STKaiti"/><a:ea typeface="STKaiti"/></a:majorFont><a:minorFont><a:latin typeface="STKaiti"/><a:ea typeface="STKaiti"/></a:minorFont></a:fontScheme></a:themeElements>
</a:theme>"""


def _pptx(path: Path, font: str) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", SLIDE_XML.format(font=font))
        archive.writestr("ppt/theme/theme1.xml", THEME_XML)


def _config() -> dict:
    return {
        "theme": {
            "typography": {
                "primary_fonts": ["华文楷体"],
                "font_validation": {
                    "deferred_font_identities": [
                        {"canonical_family": "华文楷体", "aliases": ["STKaiti"]}
                    ]
                },
            }
        }
    }


class FontNameAuditTests(unittest.TestCase):
    def test_visible_cjk_preserves_configured_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "good.pptx"
            _pptx(path, "STKaiti")
            report = audit_font_names(path, _config())
            self.assertTrue(report["ok"])
            self.assertEqual(report["visible_cjk_chars"], report["conforming_cjk_chars"])

    def test_explicit_yahei_override_fails_even_when_theme_is_kaiti(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "bad.pptx"
            _pptx(path, "微软雅黑")
            report = audit_font_names(path, _config())
            self.assertFalse(report["ok"])
            self.assertEqual(report["violations"][0]["observed_typeface"], "微软雅黑")

    def _pinned_config(self, payload: bytes) -> dict:
        config = _config()
        config["theme"]["typography"]["font_validation"]["deferred_font_identities"][0]["font_asset"] = {
            "file_name": "STKAITI.TTF",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "font_version": "Synthetic binding fixture; not a real font",
        }
        return config

    def test_same_family_name_does_not_pass_without_pinned_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            pptx = Path(raw) / "deck.pptx"
            _pptx(pptx, "STKaiti")
            report = audit_font_names(pptx, self._pinned_config(b"synthetic font bytes"))
            self.assertEqual(report["font_name_status"], "pass")
            self.assertEqual(report["status"], "deferred")
            self.assertFalse(report["ok"])

    def test_same_filename_with_different_bytes_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            pptx, font = Path(raw) / "deck.pptx", Path(raw) / "STKAITI.TTF"
            _pptx(pptx, "STKaiti")
            font.write_bytes(b"different font bytes")
            report = audit_font_names(pptx, self._pinned_config(b"synthetic font bytes"), {"STKaiti": font})
            self.assertEqual(report["font_name_status"], "pass")
            self.assertEqual(report["status"], "fail")
            self.assertFalse(report["ok"])

    def test_correct_bytes_pass_under_renamed_file_and_canonical_alias(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            pptx, font = Path(raw) / "deck.pptx", Path(raw) / "renamed.ttf"
            _pptx(pptx, "STKaiti")
            font.write_bytes(b"synthetic font bytes")
            report = audit_font_names(pptx, self._pinned_config(font.read_bytes()), {"华文楷体": font})
            self.assertTrue(report["ok"])
            self.assertEqual(report["font_asset_checks"][0]["renderer_loaded_file"], "not-verified")

    def test_conflicting_alias_file_cannot_hide_behind_correct_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pptx, correct, wrong = root / "deck.pptx", root / "correct.ttf", root / "wrong.ttf"
            _pptx(pptx, "STKaiti")
            correct.write_bytes(b"synthetic font bytes")
            wrong.write_bytes(b"different font bytes")
            report = audit_font_names(pptx, self._pinned_config(correct.read_bytes()), {"STKaiti": correct, "华文楷体": wrong})
            self.assertEqual(report["status"], "fail")

    def test_missing_supplied_file_is_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            pptx = Path(raw) / "deck.pptx"
            _pptx(pptx, "STKaiti")
            report = audit_font_names(pptx, self._pinned_config(b"synthetic font bytes"), {"STKaiti": Path(raw) / "missing.ttf"})
            self.assertEqual(report["status"], "deferred")


if __name__ == "__main__":
    unittest.main()
