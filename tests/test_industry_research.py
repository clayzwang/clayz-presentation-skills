import copy
import unittest
from packages.validators.industry_research import inspect, reader_brief

class IndustryResearchReferences(unittest.TestCase):
    def setUp(self):
        self.ledger={
            'contract':'io.clayz.presentation.industry-research/1.0',
            'stages':[{'stage_id':s,'source_ids':['S1'],'claim_status':'source-fact'} for s in ('design','fab','memory')],
            'companies':[{'company_id':c,'stage_ids':[s],'role':r,'selection_basis':'公开披露对应业务','source_ids':['S1'],'claim_status':'source-fact'} for c,s,r in [('nvidia','design','设计产品并委托制造'),('tsmc','fab','晶圆代工'),('micron','memory','存储器件')]],
            'links':[{'link_id':lid,'from_stage':a,'to_stage':'design','kind':kind,'what_moves':what,'scope':'verified-company-relationship','company_ids':ids,'source_ids':['S1'],'claim_status':'source-fact'} for lid,a,kind,what,ids in [('fab','fab','service','晶圆制造',['tsmc','nvidia']),('mem','memory','goods','存储器件',['micron','nvidia'])]]}
    def test_parallel_inputs_do_not_require_a_linear_chain(self):
        observed=inspect(self.ledger,['S1'])
        self.assertTrue(observed['ok']);self.assertEqual([],observed['isolated_stages'])
        self.assertIn('substantive completeness',observed['limitation'])
    def test_named_relationship_cannot_resolve_to_unknown_company(self):
        bad=copy.deepcopy(self.ledger);bad['links'][1]['company_ids']=['missing','nvidia']
        self.assertFalse(inspect(bad,['S1'])['ok'])
    def test_dangling_source_is_reported_without_rewriting_research(self):
        bad=copy.deepcopy(self.ledger);bad['links'][0]['source_ids']=['S404'];before=copy.deepcopy(bad)
        self.assertFalse(inspect(bad,['S1'])['ok']);self.assertEqual(bad,before)
    def test_neutral_audience_survives_without_finance_assumptions(self):
        p={'audience':'没有行业或财报专业知识','purpose':'理解业务与上下游','task':'根据可见材料说明理解和疑问'}
        self.assertEqual(reader_brief(p),p)
        self.assertEqual(p['audience'],reader_brief(p)['audience'])

if __name__=='__main__':unittest.main()
