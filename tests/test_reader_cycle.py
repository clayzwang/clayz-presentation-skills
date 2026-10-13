"""Synthetic orchestration tests: no real language quality or host execution claimed."""
import copy
import unittest
from packages.validators import reader_review as rr
from packages.validators import reader_cycle as rc
from tests import test_reader_review as fixture

class ReaderCycleTests(unittest.TestCase):
    setUp = fixture.ReaderReviewTests.setUp
    put = fixture.ReaderReviewTests.put
    context = fixture.ReaderReviewTests.context
    response = fixture.ReaderReviewTests.response

    def setup_cycle(self, gaps=True, phase='copy'):
        package=rr.read(self.package); package['status']='copy-approved'
        self.package=self.put(phase+'-delivered.json',package)
        self.config=self.put('config.json',{'workflow':{'reader_review':{'repair_policy':'consolidated-once'}}})
        self.logic=self.put(phase+'-logic.json',{**package,'status':'logic-approved'})
        self.plan=self.put('plan.json',{})
        self.reviews={}
        phases=['title','content'] if phase=='copy' else ['final']
        for reader in phases:
            packet=self.root/(reader+'-packet.json')
            rr.prepare_packet(phase=reader,package=self.package,brief=self.brief,
              directory=self.root/(reader+'-input'),output=packet,config=self.config,
              plan=self.plan if reader=='final' else None,
              pptx=self.pptx if reader=='final' else None,renders=self.renders if reader=='final' else None)
            first=self.root/(reader+'-first.json')
            rr.record_first(packet=packet,context=self.context(packet,reader),
              response=self.put(reader+'-response.json',self.response(gaps)),output=first)
            baseline=self.package if reader=='final' else self.logic
            comp={'baseline':rr.ref(baseline),'checks':{k:'Synthetic grounded comparison.' for k in
               (['research_conclusions'] if reader=='title' else ['accuracy','completeness','reasoning'])},
               'verdict':'return-art' if gaps and reader=='final' else ('return-copy' if gaps else 'pass'),
               'explanation':'Synthetic comparison observation.'}
            evidence=[baseline]
            if reader=='final': comp['art_changes']=[]; evidence.append(__import__('pathlib').Path(rr.read(packet)['art_plan']['path']))
            dis=[{'finding_id':'TITLE-ANSWER','owner_layer':'copy','status':'open',
                   'explanation':'A synthetic issue.','evidence_refs':[rr.ref(baseline)]}] if gaps else []
            review=self.root/(reader+'-review.json')
            rr.record_review(first_read=first,dispositions=self.put(reader+'-dis.json',dis),
              evidence=evidence,comparison=self.put(reader+'-comparison.json',comp),output=review)
            self.reviews[reader]=review
        self.cycle=self.root/(phase+'-cycle.json')
        return rc.collect(phase=phase,config=self.config,package=self.package,
             reviews=list(self.reviews.values()),output=self.cycle,
             plan=self.plan,pptx=self.pptx,renders=self.renders)

    def closure(self,value,remaining=False,new=False):
        current=copy.deepcopy(value['baseline'])
        if value['phase']=='copy' and value.get('repair'):
            revised=rr.read(self.package)
            revised['copy_layer']['slides'][0]['copy_units'][0]['text']='A gives a deadline; B gives principles'
            current['package']=rr.ref(self.put('revised-copy.json',revised))
        issues=rc.inspect(value)[2]
        rows=[{'issue_id':x['issue_id'],'status':'remaining' if remaining else 'resolved',
               'explanation':'Confirmed from revised visible material.','evidence':[current['package']]} for x in issues]
        result={'artifacts':current,'resolutions':rows,'confirmations':{}}
        if value.get('repair'):
            result['verification']=rr.ref(self.put(value['phase']+'-owner-check.json',{'owner':value['repair']['owner'],
                'artifacts':current,'checks':[{'status':'pass','observation':'Actual fixture files checked.'}]}))
            for phase in value['reviews']:
                raw=self.put(phase+'-reread-raw.json',{'synthetic_test_fixture':True,'context':phase})
                receipt=self.put(phase+'-reread-host.json',{'context_id':phase,'host_tool':'fixture-followup',
                    'input_artifacts':current,'raw_receipt':rr.ref(raw)})
                record={'contract':'io.clayz.presentation.reader-confirmation/1.0','phase':phase,
                    'context_id':phase,'binding':value['binding'],'artifacts':current,'reviewed_at':rc.now(),
                    'host_receipt':rr.ref(receipt),'resolutions':[x for x in rows if x['issue_id'].startswith(phase+':')],
                    'new_findings':[{'finding_id':'N1','slide_ids':['S01'],'statement':'A new issue.',
                        'reader_impact':'Extra reading effort.','visible_evidence':'Synthetic rendered material.'}] if new else []}
                result['confirmations'][phase]=rr.ref(self.put(phase+'-confirmation.json',record))
        return result

    def test_parallel_copy_reading_and_no_repair(self):
        value=self.setup_cycle(gaps=False)
        closed=rc.close(self.cycle,self.closure(value))
        self.assertEqual(0,rc.validate_cycle(closed)['repair_count'])
        self.assertTrue(rr.check_art_gate(rr.read(self.package),self.reviews['title'],self.reviews['content'],
                         config=self.config,reader_cycle=self.cycle)['ready'])

    def test_one_repair_original_readers_confirm_and_remaining_is_report_only(self):
        self.setup_cycle(); value=rc.start_repair(self.cycle,'copy','Consolidated findings')
        with self.assertRaisesRegex(ValueError,'no second'):rc.start_repair(self.cycle,'copy','Again')
        closure=self.closure(value,remaining=True,new=True)
        closed=rc.close(self.cycle,closure); result=rc.validate_cycle(closed)
        self.assertEqual(4,len(result['remaining']));self.assertEqual(2,len(result['new_findings']))
        self.assertTrue(rr.check_art_gate(rr.load_ref(closure['artifacts']['package']),self.reviews['title'],
             self.reviews['content'],config=self.config,reader_cycle=self.cycle)['ready'])
        with self.assertRaisesRegex(ValueError,'closed'):rc.close(self.cycle,closure)
        with self.assertRaisesRegex(ValueError,'blocked'):rr.require_pass(result['reviews']['title'])

    def test_missing_original_rereader_cannot_close(self):
        self.setup_cycle();v=rc.start_repair(self.cycle,'copy','Fix');c=self.closure(v)
        del c['confirmations']['content']
        with self.assertRaisesRegex(ValueError,'every original'):rc.close(self.cycle,c)

    def test_substituted_rereader_cannot_close(self):
        self.setup_cycle();v=rc.start_repair(self.cycle,'copy','Fix');c=self.closure(v)
        item=rr.load_ref(c['confirmations']['title']);item['context_id']='replacement'
        c['confirmations']['title']=rr.ref(self.put('replacement.json',item))
        with self.assertRaisesRegex(ValueError,'original reader'):rc.close(self.cycle,c)

    def test_owner_cannot_overrule_reader_confirmation(self):
        self.setup_cycle();v=rc.start_repair(self.cycle,'copy','Fix');c=self.closure(v)
        c['resolutions'][0]['status']='remaining'
        with self.assertRaisesRegex(ValueError,'override'):rc.close(self.cycle,c)

    def test_confirmation_cannot_bind_old_artifact(self):
        self.setup_cycle();v=rc.start_repair(self.cycle,'copy','Fix');c=self.closure(v)
        item=rr.load_ref(c['confirmations']['title']);item['artifacts']=v['baseline']
        c['confirmations']['title']=rr.ref(self.put('stale.json',item))
        with self.assertRaisesRegex(ValueError,'repaired artifacts'):rc.close(self.cycle,c)

    def test_final_only_art_or_output_and_copy_immutable(self):
        self.setup_cycle(phase='final')
        for owner in ['copy','logic','supervisor']:
            with self.assertRaisesRegex(ValueError,'designated owner'):rc.start_repair(self.cycle,owner,'Fix')
        v=rc.start_repair(self.cycle,'output','Fix layout');c=self.closure(v,remaining=True)
        modified=rr.read(self.package);modified['extra']='unauthorized Copy change'
        c['artifacts']['package']=rr.ref(self.put('bad-copy.json',modified))
        with self.assertRaisesRegex(ValueError,'do not reopen'):rc.close(self.cycle,c)
        closed=rc.close(self.cycle,self.closure(v,remaining=True))
        self.assertEqual(1,rc.validate_cycle(closed)['repair_count'])

    def test_missing_readers_and_concurrent_reservation_rejected(self):
        v=self.setup_cycle();del v['reviews']['title']
        with self.assertRaisesRegex(ValueError,'all required'):rc.inspect(v)
        lock=self.root/'copy-cycle.json.lock';lock.write_text('reserved')
        with self.assertRaises(FileExistsError):rc.start_repair(self.cycle,'copy','Concurrent')

    def test_audit_carries_remaining_and_new_findings_after_both_cycles(self):
        self.setup_cycle();v=rc.start_repair(self.cycle,'copy','Consolidated fix')
        c=self.closure(v,remaining=True,new=True);rc.close(self.cycle,c)
        copy_cycle=self.cycle;original=dict(self.reviews)
        self.package=__import__('pathlib').Path(c['artifacts']['package']['path'])
        self.setup_cycle(phase='final');v=rc.start_repair(self.cycle,'art-direction','Layout fix')
        rc.close(self.cycle,self.closure(v,remaining=True,new=True))
        all_reviews={**original,**self.reviews}
        audit={'run_id':'reader-test','task_request_sha256':'a'*64,'audited_at':rc.now(),
            'final_pptx':rr.ref(self.pptx),'source_records':[
             {'kind':k,**rr.ref(p)} for k,p in {'package':self.package,'plan':self.plan,'config':self.config,
             'reader-cycle-copy':copy_cycle,'reader-cycle-final':self.cycle,
             **{'reader-review-'+k:p for k,p in all_reviews.items()}}.items()]}
        checks=rr.audit_reviews(audit,required=True)
        self.assertEqual({'title','content','final'},set(checks))
        findings=rr.audit_reader_findings(audit,checks)
        self.assertEqual(9,len([f for f in findings if f['finding_id'].startswith('READER-CYCLE-')]))
        self.assertTrue(all('Report only' in f['recommended_change'] for f in findings if f['finding_id'].startswith('READER-CYCLE-')))
        from packages.validators.work_report import _auditor, _render_auditor
        section=_auditor(audit,{},snapshots=[],ids=set());lines=[]
        _render_auditor(lines,{'auditor':section})
        self.assertIn('reader-confirmation','\n'.join(lines))
        audit['audited_at']='2020-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'follow all'):rr.audit_reviews(audit,required=True)

    def test_legacy_content_order_preserved(self):
        with self.assertRaisesRegex(ValueError,'title-review'):
            rr.prepare_packet(phase='content',package=self.package,brief=self.brief,
                              directory=self.root/'legacy',output=self.root/'legacy.json')

if __name__=='__main__':unittest.main()
