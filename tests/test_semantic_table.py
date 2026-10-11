import tempfile
import unittest
from pathlib import Path
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from PIL import ImageFont
from packages.layout.semantic_table import Column, plan, write
from packages.validators.visual_evidence import validate

from tests.font_support import test_font_path
FONT = test_font_path()


class TableRegression(unittest.TestCase):
    def spec(self, **kwargs):
        return plan([Column('项目', weight=2), Column('金额', 'number')],
                    [['经营现金流', '182.935'], ['资本开支', '115.948'], ['差额', '66.987']],
                    width=6, font_path=FONT, caption='FY2026；十亿美元',
                    comparison='比较现金产生、现金投资与剩余', total_rows=[2], **kwargs)

    def test_native_roundtrip_preserves_padding_and_numeric_alignment(self):
        spec = self.spec(); prs = Presentation(); slide = prs.slides.add_slide(prs.slide_layouts[6])
        write(slide, spec, 1, 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'table.pptx'; prs.save(path)
            tbl = Presentation(path).slides[0].shapes[0].table
            self.assertAlmostEqual(tbl.cell(1, 1).margin_left / 914400, .17)
            self.assertEqual(tbl.cell(1, 1).text_frame.paragraphs[0].alignment, PP_ALIGN.RIGHT)
            self.assertTrue(tbl.cell(3, 1).text_frame.paragraphs[0].runs[0].font.bold)
            self.assertFalse(tbl.first_row)
            self.assertGreater(tbl.columns[0].width, tbl.columns[1].width)

    def test_capacity_cannot_pass_by_silent_font_shrink(self):
        with self.assertRaisesRegex(ValueError, 'revise Art'): self.spec(max_height=.5)

    def test_native_width_reserve_reflows_before_capacity_check(self):
        # R4 native reopening split Google Cloud despite a measured single line.
        text = 'AWS、微软Azure、Google Cloud'
        font = ImageFont.truetype(FONT, round(23 * 120 / 72))
        args = dict(columns=[Column('企业样本')], rows=[[text]],
                    width=font.getlength(text)/120*1.04+.34,
                    font_path=FONT, size=23, caption='关键角色样本',
                    comparison='交付与企业对应', protected_terms=['Google Cloud'])
        original = plan(**args)
        calibrated = plan(**args, native_width_scale=1.08)
        self.assertEqual(original['cells'][1][0]['lines'], [text])
        self.assertGreater(calibrated['height'], original['height'])
        self.assertEqual(''.join(calibrated['cells'][1][0]['lines']).replace(' ', ''), text.replace(' ', ''))
        self.assertEqual(calibrated['cells'][1][0]['size_pt'], 23)
        self.assertEqual(calibrated['widths'], original['widths'])
        self.assertEqual(calibrated['padding'], original['padding'])
        with self.assertRaisesRegex(ValueError, 'revise Art'):
            plan(**args, native_width_scale=1.08, max_height=original['height']+.01)

    def test_missing_visual_review_stays_unreviewed(self):
        self.assertTrue(validate({'pages': {'S01': {'content': 'numbers correct'}}}, ['S01']))


if __name__ == '__main__': unittest.main()
