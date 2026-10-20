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

def test_author_terms_do_not_weaken_existing_date_number_or_latin_atoms():
    class UnitFont:
        def getlength(self, value): return len(value)
    for text, atom, selection, width in [
        ('日期2026-06-30','2026-06-30','2026',10),
        ('值12.34','12.34','12',5),
        ('型CPU/DCU','CPU/DCU','CPU',7),
    ]:
        lines=wrap(text,UnitFont(),width,minimum_tail_em=0,protected_terms=(selection,))
        assert ''.join(lines)==text
        assert any(atom in line for line in lines)
        assert all(len(line)<=width for line in lines)

def test_explicit_hygon_groups_preserve_text_at_observed_font_widths():
    for text,size,width,group in [
        ('研发、设计与销售',58,438.4512,'设计'),
        ('公司另预告扣非归母24.5—27.1亿元。',62,887.04,'24.5—27.1亿元'),
    ]:
        font=ImageFont.truetype(str(FONT),size)
        lines=wrap(text,font,width,protected_terms=(group,))
        assert ''.join(lines)==text
        assert any(group in line for line in lines)
        assert all(font.getlength(line)<=width for line in lines)

def test_overlapping_groups_union_but_adjacent_groups_can_break():
    class UnitFont:
        def getlength(self, value): return len(value)
    text='甲乙丙丁'
    assert wrap(text,UnitFont(),2,minimum_tail_em=0,protected_terms=('甲乙','丙丁'))==['甲乙','丙丁']
    assert wrap(text,UnitFont(),3,minimum_tail_em=0,protected_terms=('甲乙','乙丙'))==['甲乙丙','丁']
    try:wrap(text,UnitFont(),2,protected_terms=('甲乙','乙丙'))
    except ValueError as ex:assert 'exceeds width' in str(ex)
    else:raise AssertionError('Oversize combined author group must return to Art')

def test_invalid_author_selection_is_explicit_and_hard_breaks_survive():
    class UnitFont:
        def getlength(self, value): return len(value)
    for invalid in ['设计',('',),('甲\n乙',),(1,)]:
        try:wrap('甲乙',UnitFont(),5,protected_terms=invalid)
        except ValueError:pass
        else:raise AssertionError('Invalid author terms must not silently change tokenization')
    assert wrap('甲乙\n丙丁',UnitFont(),2,protected_terms=())==['甲乙','丙丁']


class TextFlowRegression(unittest.TestCase):
    def test_financial_atoms_and_date(self):
        test_financial_atoms_and_date_survive_narrow_columns()

    def test_chinese_punctuation_and_tail(self):
        test_chinese_punctuation_and_short_tail_regression()

    def test_punctuation_after_tail_rebalance(self):
        test_short_tail_rebalance_keeps_existing_punctuation_boundaries()

    def test_author_selection_preserves_existing_atoms(self):
        test_author_terms_do_not_weaken_existing_date_number_or_latin_atoms()

    def test_observed_phrase_and_range(self):
        test_explicit_hygon_groups_preserve_text_at_observed_font_widths()

    def test_overlapping_and_adjacent_selections(self):
        test_overlapping_groups_union_but_adjacent_groups_can_break()

    def test_selection_domain_and_hard_breaks(self):
        test_invalid_author_selection_is_explicit_and_hard_breaks_survive()
