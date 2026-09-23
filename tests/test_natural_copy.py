"""Natural syntax repetition must not force unsupported language changes."""
import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'packages/validators'))
from validate_ppt_package import validate_deck_expression_variation


class NaturalCopyTests(unittest.TestCase):
    def pages(self):
        facts=[('服务收入增长12%','新增客户较多，服务收入较去年同期增加。'),
               ('维修收入下降3%','维修订单减少，现有资料没有提供具体原因。'),
               ('续费收入保持稳定','续费客户数和客单价与去年同期基本相同。')]
        logic=[]
        pages=[]
        for index,(title,body) in enumerate(facts):
            sid=f'P{index}'
            logic.append({'slide_id':sid,'series_id':None})
            pages.append({'slide_id':sid,'title_copy_id':sid+'title','storyline_copy_id':None,
                          'audience_transition_copy_strategy':f'解释第{index+1}项业务事实',
                          'copy_units':[{'copy_id':sid+'title','role':'title','text':title,'grammar_signature':'judgment'},
                                        {'copy_id':sid+'body','role':'evidence','text':body,'grammar_signature':'explanation'}]})
        return logic,pages

    def test_distinct_facts_can_share_natural_syntax(self):
        logic,pages=self.pages()
        before=copy.deepcopy(pages)
        errors=[]
        validate_deck_expression_variation(logic,pages,errors,enforce_grammar_variation=False)
        self.assertEqual(errors,[])
        self.assertEqual(pages,before)

    def test_legacy_validation_remains_replayable(self):
        logic,pages=self.pages()
        errors=[]
        validate_deck_expression_variation(logic,pages,errors)
        self.assertTrue(any('complete grammar vector' in error for error in errors))

    def test_syntax_relaxation_does_not_hide_duplicate_titles(self):
        logic,pages=self.pages()
        pages[1]['copy_units'][0]['text']=pages[0]['copy_units'][0]['text']
        errors=[]
        validate_deck_expression_variation(logic,pages,errors,enforce_grammar_variation=False)
        self.assertTrue(any('identical non-series title' in error for error in errors))


if __name__=='__main__':
    unittest.main()
