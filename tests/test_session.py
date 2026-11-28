import copy
import hashlib
import subprocess
import sys
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from forge_session import session
from forge_baseline import fingerprint
from forge_validate import load
from forge_integrate import git

ROOT = Path(__file__).resolve().parents[1]


class SessionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.p = Path(tmp.name)
        shutil.copytree(ROOT/'fixtures', self.p/'fixtures')
        (self.p/'schemas').mkdir()
        shutil.copyfile(ROOT/'schemas/example-response-map.schema.json',
                        self.p/'schemas/example-response-map.schema.json')
        self.m = self.p/'fixtures/project.json'
        self.path = self.p/'fixtures/records.json'
        self.r = load(self.path)
        self.get('BASE-01')['data']['source_commit'] = 'a' * 40
        self.get('BASE-01')['data']['composition'].extend([
            {'id':'TEST-01','revision':1}, {'id':'ENV-01','revision':1}])

    def get(self, id):
        return next(r for r in self.r if r['id'] == id)

    def save(self, *, update_digest=True):
        if update_digest:
            m = load(self.m)
            records = {(r['id'],r['revision']):r for r in self.r}
            b = records[(m['baseline_ref']['id'],m['baseline_ref']['revision'])]
            b['data']['snapshot_sha256'] = fingerprint(records,b)
        self.path.write_text(json.dumps(self.r, ensure_ascii=False), encoding='utf-8')

    def run_session(self, **kwargs):
        self.save()
        return session(self.p, 'fixtures/project.json', **kwargs)

    def task(self, report, id='TASK-01'):
        return next(t for t in report['tasks'] if t['task']['id'] == id)

    def reported_pass(self):
        self.get('TASK-01')['data']['state'] = 'done'
        self.get('EVID-01')['data'].update(result='pass', validity='current',
                                          artifact_sha256='b' * 64)

    def add_task(self, id='TASK-02', dependency=None):
        t = copy.deepcopy(self.get('TASK-01'))
        t['id'] = id
        t['data']['state'] = 'proposed'
        t['relations'] = ([{'kind':'depends_on','target_id':dependency}]
                          if dependency else [])
        self.r.append(t)
        return t

    def test_candidate_and_contract(self):
        report = self.run_session()
        self.assertEqual(report['next_candidates'], ['TASK-01'])
        c = self.task(report)['contract']
        self.assertEqual(c['operations_declared_in_both'], ['write-local'])
        self.assertEqual(c['linked_records'][0]['record']['id'], 'REQ-01')
        self.assertEqual(c['completion_checks'][0]['assessment'], 'review_required')
        self.assertFalse(c['operation_authority_verified'])
        self.assertFalse(report['executed'])

    def test_role_scope_mismatch(self):
        self.get('TASK-01')['data']['allowed_operations'].append('publish')
        r = self.run_session()
        self.assertIn('task_operations_outside_role_declaration', self.task(r)['holds'])
        self.assertEqual(r['next_candidates'], [])

    def test_scope_and_independent_work(self):
        self.get('TASK-01')['data']['state'] = 'blocked'
        self.add_task(dependency='TASK-01')
        self.add_task(id='TASK-03')
        r = self.run_session()
        self.assertEqual(r['next_candidates'], ['TASK-03'])
        self.assertEqual(self.task(r,'TASK-02')['waiting_for'], ['TASK-01'])

    def test_done_without_pass(self):
        self.get('TASK-01')['data']['state'] = 'done'
        self.add_task(dependency='TASK-01')
        self.assertEqual(self.run_session()['review_required'], ['TASK-01','TASK-02'])

    def test_reported_done_not_authentication(self):
        self.reported_pass()
        self.add_task(dependency='TASK-01')
        r = self.run_session()
        self.assertEqual(self.task(r)['assessment'], 'recorded_done')
        self.assertEqual(r['next_candidates'], ['TASK-02'])
        self.assertFalse(r['evidence_authenticity_verified'])

    def test_conflicting_evidence_not_cherry_picked(self):
        self.reported_pass()
        e = copy.deepcopy(self.get('EVID-01'))
        e['id'] = 'EVID-FAIL'
        e['data']['result'] = 'fail'
        self.r.append(e)
        self.assertEqual(self.task(self.run_session())['assessment'], 'review_required')

    def test_all_declared_active_tests_required(self):
        self.reported_pass()
        t = copy.deepcopy(self.get('TEST-01'))
        t['id'] = 'TEST-OTHER'
        self.r.append(t)
        self.assertEqual(self.task(self.run_session())['assessment'], 'review_required')

    def test_no_completion_criteria(self):
        self.get('TASK-01')['data']['acceptance'] = []
        self.assertIn('no_completion_criteria', self.task(self.run_session())['holds'])

    def test_non_task_dependency_review(self):
        self.get('TASK-01')['relations'].append({'kind':'depends_on','target_id':'REQ-01'})
        self.assertIn('nonactive_or_nontask_dependency_requires_review',
                      self.task(self.run_session())['holds'])

    def test_old_task_baseline(self):
        old = self.get('BASE-01')
        new = copy.deepcopy(old)
        old['lifecycle'] = 'superseded'
        new['revision'] = 2
        self.r.append(new)
        m = load(self.m)
        m['baseline_ref']['revision'] = 2
        self.m.write_text(json.dumps(m), encoding='utf-8')
        self.assertIn('task_baseline_differs', self.task(self.run_session())['holds'])

    def test_unconfirmed_source(self):
        self.get('BASE-01')['data']['source_commit'] = None
        r = self.run_session()
        self.assertFalse(r['source_revision_observed'])
        self.assertEqual(r['next_candidates'], ['TASK-01'])

    def test_unknown_extension_local_hold(self):
        m = load(self.m)
        m['extension_registry'] = []
        self.m.write_text(json.dumps(m), encoding='utf-8')
        self.get('TASK-01')['relations'].append({'kind':'supported_by','target_id':'MAP-01'})
        self.add_task()
        r = self.run_session()
        self.assertIn('referenced_extension_unverified', self.task(r)['holds'])
        self.assertEqual(r['next_candidates'], ['TASK-02'])

    def test_observe_git_requires_clean_head(self):
        self.save()
        git(self.p, 'init', '-q')
        git(self.p, 'config', 'user.name', 'Session Test')
        git(self.p, 'config', 'user.email', 'test@example.invalid')
        git(self.p, 'add', '.')
        git(self.p, 'commit', '-qm', 'base')
        r = session(self.p, 'fixtures/project.json', observe_git=True)
        self.assertEqual(r['observed_head'], git(self.p,'rev-parse','HEAD').decode().strip())
        self.assertIn('baseline_source_differs_from_observed_head', r['baseline_issues'])
        (self.p/'untracked').write_text('human edit')
        with self.assertRaises(ValueError):
            session(self.p, 'fixtures/project.json', observe_git=True)

    def test_readonly(self):
        self.save()
        before = self.path.read_bytes()
        session(self.p, 'fixtures/project.json')
        self.assertEqual(before, self.path.read_bytes())

    def test_changed_baseline_composition_held(self):
        self.save()
        self.get('REQ-01')['body'] = 'changed requirement'
        self.save(update_digest=False)
        r = session(self.p, 'fixtures/project.json')
        self.assertFalse(r['baseline_composition_matches'])
        self.assertEqual(r['next_candidates'], [])

    def test_separate_code_target(self):
        code = self.p/'code'
        code.mkdir()
        git(code, 'init', '-q')
        git(code, 'config', 'user.name', 'Test')
        git(code, 'config', 'user.email', 'test@example.invalid')
        git(code, 'commit', '--allow-empty', '-qm', 'code')
        self.get('BASE-01')['data']['source_commit'] = git(code,'rev-parse','HEAD').decode().strip()
        self.save()
        r = session(self.p, 'fixtures/project.json', target=code)
        self.assertEqual(r['next_candidates'], ['TASK-01'])
        self.assertTrue(r['source_revision_observed'])
        self.assertTrue(r['baseline_composition_matches'])
        git(code, 'commit', '--allow-empty', '-qm', 'code changed')
        r = session(self.p, 'fixtures/project.json', target=code)
        self.assertEqual(r['next_candidates'], [])
        self.assertIn('baseline_source_differs_from_observed_head', r['baseline_issues'])

    def test_unpinned_test_not_completion_evidence(self):
        self.reported_pass()
        b = self.get('BASE-01')['data']['composition']
        b[:] = [r for r in b if r['id'] != 'TEST-01']
        r = self.run_session()
        self.assertEqual(self.task(r)['assessment'], 'review_required')

    def test_unpinned_criterion_blocks_work_candidate(self):
        b = self.get('BASE-01')['data']['composition']
        b[:] = [r for r in b if r['id'] != 'AC-01']
        self.assertIn('completion_criterion_not_active_and_pinned',
                      self.task(self.run_session())['holds'])

    def test_unpinned_linked_requirement_blocks_candidate(self):
        b = self.get('BASE-01')['data']['composition']
        b[:] = [r for r in b if r['id'] != 'REQ-01']
        self.assertIn('linked_normative_record_not_active_and_pinned',
                      self.task(self.run_session())['holds'])

    def test_real_local_test_then_new_code_invalidates_recorded_done(self):
        code = self.p/'code'
        code.mkdir()
        for filename in ('order.py','test_order.py'):
            shutil.copyfile(ROOT/'examples/uncertain-order'/filename,code/filename)
        git(code,'init','-q')
        git(code,'config','user.name','Test')
        git(code,'config','user.email','test@example.invalid')
        git(code,'add','.')
        git(code,'commit','-qm','initial interval comparator')
        self.get('BASE-01')['data']['source_commit'] = git(code,'rev-parse','HEAD').decode().strip()
        self.get('INTENT-01').update(title='Preserve uncertain event order',body='Preserve uncertainty in local event records')
        self.get('REQ-01').update(title='Do not invent ordering',body='Only claim strict precedence for disjoint closed intervals')
        self.get('REQ-01')['data']['conditions']='Normalized integer ticks'
        self.get('AC-01')['data'].update(expected='Correct interval relations and invalid input handling',
                                          conditions='Closed integer intervals')
        self.get('ENV-01')['data'].update(purpose='Local unit tests',version=sys.version,
                                           capabilities={'python':'available'},verification='Local test invocation')
        self.get('TEST-01')['data']['procedure']='python -B -m unittest -v test_order'
        self.get('TASK-01').update(title='Implement interval comparator',body='Validate closed interval comparisons')
        self.get('TASK-01')['data']['scope']='Interval comparator'
        next_check=copy.deepcopy(self.get('AC-01'))
        next_check['id']='AC-02'
        next_check['data']['expected']='Partial order preserves definite edges without inventing order'
        self.r.append(next_check)
        self.get('BASE-01')['data']['composition'].append({'id':'AC-02','revision':1})
        next_task=self.add_task(dependency='TASK-01')
        next_task.update(title='Design partial order',body='Next milestone')
        next_task['data']['acceptance']=[{'id':'AC-02','revision':1}]
        self.save()
        r=session(self.p,'fixtures/project.json',target=code)
        self.assertEqual(r['next_candidates'],['TASK-01'])
        run=subprocess.run([sys.executable,'-B','-m','unittest','-v','test_order'],
                           cwd=code,capture_output=True,check=True)
        log=run.stdout+run.stderr
        self.assertIn(b'Ran 5 tests',log)
        (self.p/'observed-test.log').write_bytes(log)
        self.get('EVID-01')['data'].update(result='pass',validity='current',
            artifact_sha256=hashlib.sha256(log).hexdigest(),executor='local integration test')
        self.get('TASK-01')['data']['state']='done'
        self.save(update_digest=False)
        r=session(self.p,'fixtures/project.json',target=code)
        self.assertEqual(self.task(r)['assessment'],'recorded_done')
        self.assertEqual(r['next_candidates'],['TASK-02'])
        self.assertFalse(r['evidence_authenticity_verified'])
        (code/'order.py').write_text('def relation(a,b): return "before"\n')
        git(code,'add','order.py')
        git(code,'commit','-qm','introduce regression')
        bad=subprocess.run([sys.executable,'-B','-m','unittest','-v','test_order'],
                           cwd=code,capture_output=True,check=False)
        self.assertNotEqual(bad.returncode,0)
        r=session(self.p,'fixtures/project.json',target=code)
        self.assertEqual(self.task(r)['assessment'],'review_required')
        self.assertEqual(r['next_candidates'],[])

    def test_rejected_task_not_work_candidate(self):
        self.add_task()
        self.get('TASK-01')['authority']='rejected'
        r=self.run_session()
        self.assertIn('task_rejected',self.task(r)['holds'])
        self.assertEqual(r['next_candidates'],['TASK-02'])

    def test_rejected_role_blocks_candidates(self):
        self.get('ROLE-OWNER')['authority']='rejected'
        r=self.run_session()
        self.assertIn('owner_role_rejected',self.task(r)['holds'])
        self.assertFalse(r['next_candidates'])

    def test_rejected_baseline_holds(self):
        self.get('BASE-01')['authority']='rejected'
        r=self.run_session()
        self.assertIn('baseline_rejected',r['baseline_issues'])
        self.assertFalse(r['next_candidates'])

    def test_rejected_criterion_holds(self):
        self.get('AC-01')['authority']='rejected'
        self.assertFalse(self.run_session()['next_candidates'])

    def test_rejected_requirement_holds(self):
        self.get('REQ-01')['authority']='rejected'
        self.assertFalse(self.run_session()['next_candidates'])

    def test_rejected_reported_pass_is_not_completion(self):
        for id in ('TEST-01','ENV-01','EVID-01'):
            with self.subTest(id=id):
                self.reported_pass()
                r=self.get(id)
                original=r['authority']
                r['authority']='rejected'
                self.assertEqual(self.task(self.run_session())['assessment'],'review_required')
                r['authority']=original
