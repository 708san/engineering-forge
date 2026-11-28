import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from forge_guard import compare, read_project
from forge_validate import load

ROOT = Path(__file__).resolve().parents[1]


class GuardTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.old, self.new = Path(tmp.name)/'old', Path(tmp.name)/'new'
        self.manifest = 'fixtures/project.json'
        for base in (self.old,self.new):
            base.mkdir()
            shutil.copytree(ROOT/'fixtures', base/'fixtures')
            (base/'schemas').mkdir()
            shutil.copyfile(ROOT/'schemas/example-response-map.schema.json',
                            base/'schemas/example-response-map.schema.json')
        self.records = load(self.new/'fixtures/records.json')

    def record(self,id):
        return next(r for r in self.records if r['id']==id)

    def run_guard(self):
        (self.new/'fixtures/records.json').write_text(
            json.dumps(self.records,ensure_ascii=False),encoding='utf-8')
        return compare(self.old,self.manifest,self.new,self.manifest)

    def test_unchanged(self):
        r=self.run_guard()
        self.assertEqual(r['protected_records_compared'],3)
        self.assertFalse(r['review_required'])
        self.assertFalse(r['approval_verified'])

    def test_requirements_modified(self):
        self.record('REQ-01')['body']='send data'
        self.assertTrue(self.run_guard()['protected_changes'])

    def test_new_revision_cannot_replace_protected(self):
        old=self.record('REQ-01')
        new=copy.deepcopy(old)
        old['lifecycle']='superseded'
        new['revision']=2
        self.records.append(new)
        self.assertTrue(any(x['reason']=='protected_active_revision_replaced_or_removed'
                            for x in self.run_guard()['protected_changes']))

    def test_criterion_downgrade(self):
        self.record('AC-01')['data']['mandatory']=False
        self.assertTrue(self.run_guard()['protected_changes'])

    def test_pinned_nonmandatory_criterion_protected(self):
        old=load(self.old/'fixtures/records.json')
        next(x for x in old if x['id']=='AC-01')['data']['mandatory']=False
        (self.old/'fixtures/records.json').write_text(json.dumps(old),encoding='utf-8')
        self.record('AC-01')['data']['mandatory']=False
        self.record('AC-01')['data']['expected']='weaker goal'
        self.assertTrue(self.run_guard()['protected_changes'])

    def test_unprotected_design_change_allowed(self):
        self.record('TASK-01')['data']['scope']='changed implementation approach'
        self.assertFalse(self.run_guard()['review_required'])

    def test_role_scope_change_review(self):
        self.record('ROLE-OWNER')['data']['allowed_operations'].append('publish')
        self.assertEqual(self.run_guard()['role_scope_review'],['ROLE-OWNER'])

    def test_added_role_review(self):
        r=copy.deepcopy(self.record('ROLE-OWNER'))
        r['id']='ROLE-NEW'
        self.records.append(r)
        self.assertEqual(self.run_guard()['role_scope_review'],['ROLE-NEW'])

    def test_mismatched_project(self):
        m=load(self.new/self.manifest)
        m['project_id']='PROJECT-OTHER'
        (self.new/self.manifest).write_text(json.dumps(m),encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_guard()

    def test_unknown_extension_review(self):
        m=load(self.new/self.manifest)
        m['extension_registry']=[]
        (self.new/self.manifest).write_text(json.dumps(m),encoding='utf-8')
        self.assertTrue(self.run_guard()['review_required'])

    def test_same_tree_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.old,self.manifest,self.old,self.manifest)

    def test_mode_change_review(self):
        m=load(self.new/self.manifest)
        m['mode']='enforced'
        (self.new/self.manifest).write_text(json.dumps(m),encoding='utf-8')
        self.assertIn('mode',self.run_guard()['manifest_review'])

    def test_removed_target_profile(self):
        m=load(self.new/self.manifest)
        m['target_profiles']=[]
        (self.new/self.manifest).write_text(json.dumps(m),encoding='utf-8')
        self.assertIn('target_profiles',self.run_guard()['manifest_review'])

    def test_pinned_environment_changed(self):
        self.record('ENV-01')['data']['capabilities']['browser']='available'
        self.assertIn('target_profiles',self.run_guard()['manifest_review'])

    def test_baseline_mutated_in_place(self):
        self.record('BASE-01')['data']['snapshot_sha256']='a'*64
        self.assertIn('baseline_ref',self.run_guard()['manifest_review'])

    def test_removed_extension_registration(self):
        m=load(self.new/self.manifest)
        m['extension_registry']=[]
        (self.new/self.manifest).write_text(json.dumps(m),encoding='utf-8')
        self.assertEqual(self.run_guard()['extension_registry_review'],
                         [{'type_id':'x.material.response-map','version':'1.0.0'}])

    def test_pinned_nonprotected_record_rewrite(self):
        old=load(self.old/'fixtures/records.json')
        next(r for r in old if r['id']=='BASE-01')['data']['composition'].append({'id':'TEST-01','revision':1})
        (self.old/'fixtures/records.json').write_text(json.dumps(old),encoding='utf-8')
        self.record('BASE-01')['data']['composition'].append({'id':'TEST-01','revision':1})
        self.record('TEST-01')['data']['procedure']='weakened procedure'
        r=self.run_guard()
        self.assertIn({'id':'TEST-01','revision':1},r['pinned_record_review'])
        self.assertTrue(r['review_required'])

    def test_evidence_rewrite(self):
        self.record('EVID-01')['data']['result']='pass'
        self.assertTrue(self.run_guard()['history_review'])

    def test_evidence_removal(self):
        self.records=[r for r in self.records if r['id']!='EVID-01']
        self.assertTrue(self.run_guard()['history_review'])

    def test_evidence_retirement_requires_review(self):
        self.record('EVID-01')['lifecycle']='retired'
        self.assertEqual(self.run_guard()['history_review'][0]['reason'],'verification_record_deactivated')

    def test_active_test_retirement_requires_review(self):
        self.record('TEST-01')['lifecycle']='retired'
        r=self.run_guard()
        self.assertTrue(any(x['id']=='TEST-01' and x['reason']=='verification_record_deactivated'
                            for x in r['history_review']))

    def test_active_test_rewrite_requires_review_even_if_unpinned(self):
        self.record('TEST-01')['data']['procedure']='skip verification'
        self.assertTrue(any(x['id']=='TEST-01' for x in self.run_guard()['history_review']))

    def test_validated_record_source_read_once(self):
        from forge_records import load as original
        path=self.old/'fixtures/records.json'
        with patch('forge_records.load',wraps=original) as record_load, patch('forge_guard.load',wraps=original) as guard_load:
            _,records,report=read_project(self.old,self.manifest)
            calls=record_load.call_args_list+guard_load.call_args_list
        self.assertEqual(sum(Path(c.args[0])==path for c in calls),1)
        self.assertEqual(len(records),report['record_count'])
