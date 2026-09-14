from __future__ import annotations

import sys
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


if __name__ == "__main__":
    unittest.main()
