"""Regressions observed in the Microsoft lab.01 draft and reopened output."""
from pathlib import Path
from PIL import ImageFont
from packages.layout.text_flow import wrap,CLOSING,OPENING
from tests.font_support import test_font_path
import unittest

FONT=Path(test_font_path())

def test_financial_atoms_and_date_survive_narrow_columns():
    font=ImageFont.truetype(str(FONT),42)
    for text,width in [('现金购置固定资产：35.8',432),('收入同比增长43%。',210),('财年于2026-06-30结束。',360)]:
        lines=wrap(text,font,width)
        assert ''.join(lines)==text
        for atom in ['35.8','43%','2026-06-30']:
            if atom in text: assert any(atom in line for line in lines)
        assert all(font.getlength(line)<=width for line in lines)

def test_chinese_punctuation_and_short_tail_regression():
    font=ImageFont.truetype(str(FONT),38)
    text='持续需求要转成实际服务收入和回款；模型公司的承诺与其他客户需求应分别观察。'
    lines=wrap(text,font,1375)
    assert ''.join(lines)==text
    assert all(not line or line[0] not in CLOSING for line in lines)
    assert all(not line or line[-1] not in OPENING for line in lines[:-1])
    assert len(lines[-1])>=4


def test_short_tail_rebalance_keeps_existing_punctuation_boundaries():
    class UnitFont:
        def getlength(self, value):
            return len(value)

    # Automotive AU07 at the observed STKaiti 84px / 532.224px ratio.
    # Previously balancing moved a comma to the start of the final line.
    for text in ['装入并连接动力、内饰、车轮等',
                 '装入并连接动力，内饰，车轮等',
                 '零件装入（动力与内饰）再检验']:
        lines=wrap(text,UnitFont(),6.336,protected_terms=())
        assert ''.join(lines)==text
        assert all(len(line)<=6.336 for line in lines)
        assert all(not line or line[0] not in CLOSING for line in lines[1:])
        assert all(not line or line[-1] not in OPENING for line in lines[:-1])


class TextFlowRegression(unittest.TestCase):
    def test_financial_atoms_and_date(self):
        test_financial_atoms_and_date_survive_narrow_columns()

    def test_chinese_punctuation_and_tail(self):
        test_chinese_punctuation_and_short_tail_regression()

    def test_punctuation_after_tail_rebalance(self):
        test_short_tail_rebalance_keeps_existing_punctuation_boundaries()
