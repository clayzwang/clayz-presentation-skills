"""Regression cases for source emphasis lost by line-local phrase matching."""
import unittest

from packages.layout.text_emphasis import project_emphasis


class EmphasisProjectionTests(unittest.TestCase):
    def test_actual_monetary_phrase_crossing_line(self):
        text = '由24亿美元收益转为7.91亿美元损失。'
        phrase = '7.91亿美元损失'
        start = text.index(phrase)
        runs = project_emphasis(text, ['由24亿美元收益转为7.91', '亿美元损失。'],
                                [(start, start + len(phrase))])
        self.assertEqual([[r['text'] for r in row if r['emphasis']]
                          for row in runs], [['7.91'], ['亿美元损失']])
        self.assertEqual(''.join(r['text'] for row in runs for r in row), text)

    def test_only_selected_repeated_occurrence(self):
        text = '收益增加，收益下降'
        runs = project_emphasis(text, ['收益增加，收', '益下降'], [(5, 7)])
        self.assertFalse(runs[0][0]['emphasis'])
        self.assertEqual([r['text'] for row in runs for r in row
                          if r['emphasis']], ['收', '益'])

    def test_overlapping_spans_preserve_union(self):
        runs = project_emphasis('甲乙丙丁戊', ['甲乙丙', '丁戊'], [(0, 3), (2, 4)])
        self.assertEqual([[r['text'] for r in row if r['emphasis']]
                          for row in runs], [['甲乙丙'], ['丁']])

    def test_empty_and_unemphasized_lines_preserve_offsets(self):
        runs = project_emphasis('甲乙', ['', '甲', '乙'], [])
        self.assertEqual(runs[0], [])
        self.assertEqual(runs[2], [dict(text='乙', emphasis=False, start=1, end=2)])

    def test_text_drift_is_rejected(self):
        for lines in [['净利', '103.1'], ['净利 ', '103.10'], ['净利103.10。']]:
            with self.assertRaises(ValueError):
                project_emphasis('净利103.10', lines, [(0, 2)])

    def test_invalid_spans_are_rejected(self):
        for spans in [[(-1, 1)], [(0, 4)], [(1, 1)], [(True, 2)], [('0', 2)]]:
            with self.assertRaises(ValueError):
                project_emphasis('甲乙丙', ['甲', '乙丙'], spans)


if __name__ == '__main__':
    unittest.main()
