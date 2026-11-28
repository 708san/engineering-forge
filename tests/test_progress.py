import copy
import unittest

from forge_progress import inspect


def task(id, state='proposed', parent=None, deps=()):
    return dict(id=id, purpose='domain-specific goal', state=state,
                parent=parent, depends_on=list(deps), checks=['check'], owner='local role')


def evidence(id, rev='r1', verdict='pass'):
    return dict(task_id=id, check='check', revision=rev, verdict=verdict,
                environment='test', procedure='test procedure', reference='log reference')


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.l = dict(project='novel project', tasks=[
            task('A', 'done'), task('B', deps=['A']), task('C', 'ready')],
            evidence=[evidence('A')])

    def row(self, report, id):
        return next(r for r in report['tasks'] if r['id'] == id)

    def test_current_pass_allows_dependency(self):
        r = inspect(self.l, 'r1')
        self.assertEqual(set(r['next_candidates']), {'B', 'C'})
        self.assertFalse(r['evidence_authenticity_verified'])
        self.assertFalse(r['revision_observed'])

    def test_stale_pass_does_not_allow_dependency(self):
        r = inspect(self.l, 'r2')
        self.assertEqual(r['review_required'], ['A'])
        self.assertEqual(r['next_candidates'], ['C'])
        self.assertEqual(self.row(r, 'A')['checks']['check'], 'other_revision_only')

    def test_current_failure(self):
        self.l['evidence'] = [evidence('A', verdict='fail')]
        self.assertEqual(inspect(self.l, 'r1')['review_required'], ['A'])

    def test_unverified_completion(self):
        self.l['evidence'] = []
        self.assertEqual(inspect(self.l, 'r1')['review_required'], ['A'])

    def test_transitive_invalid_done(self):
        self.l['tasks'][1]['state'] = 'done'
        self.l['evidence'].append(evidence('B'))
        self.l['evidence'].remove(evidence('A'))
        self.assertEqual(set(inspect(self.l, 'r1')['review_required']), {'A','B'})

    def test_explicit_blocked_not_reactivated(self):
        self.l['tasks'][1]['state'] = 'blocked'
        self.assertEqual(inspect(self.l, 'r1')['next_candidates'], ['C'])

    def test_parent_not_execution_dependency(self):
        self.l['tasks'][2]['parent'] = 'B'
        self.l['tasks'][1]['state'] = 'paused'
        self.assertEqual(inspect(self.l, 'r1')['next_candidates'], ['C'])

    def test_dependency_cycle(self):
        self.l['tasks'][0]['depends_on'] = ['B']
        with self.assertRaisesRegex(ValueError, 'dependency cycle'):
            inspect(self.l, 'r1')

    def test_parent_cycle(self):
        self.l['tasks'][0]['parent'] = 'B'
        self.l['tasks'][1]['parent'] = 'A'
        with self.assertRaisesRegex(ValueError, 'parent cycle'):
            inspect(self.l, 'r1')

    def test_missing_reference(self):
        self.l['tasks'][1]['depends_on'] = ['missing']
        with self.assertRaises(ValueError):
            inspect(self.l, 'r1')

    def test_duplicate_evidence(self):
        self.l['evidence'].append(evidence('A', verdict='fail'))
        with self.assertRaises(ValueError):
            inspect(self.l, 'r1')

    def test_unknown_check(self):
        self.l['evidence'][0]['check'] = 'not required'
        with self.assertRaises(ValueError):
            inspect(self.l, 'r1')

    def test_empty_completion_criteria(self):
        self.l['tasks'][0]['checks'] = []
        with self.assertRaises(ValueError):
            inspect(self.l, 'r1')

    def test_no_mutation(self):
        old = copy.deepcopy(self.l)
        inspect(self.l, 'r1')
        self.assertEqual(self.l, old)
