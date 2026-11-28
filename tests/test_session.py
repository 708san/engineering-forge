import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from forge_session import session
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

    def get(self, id):
        return next(r for r in self.r if r['id'] == id)

    def save(self):
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
        self.assertIn('baseline_source_revision_unconfirmed', self.run_session()['baseline_issues'])

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
