import tempfile
import unittest
from pathlib import Path
from forge_handoff import snapshot
from forge_impact import impact


class ImpactTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.p = Path(temp.name)
        (self.p / 'spec.md').write_text('original')
        (self.p / 'other.md').write_text('other')
        self.m = snapshot(self.p, dict(project='example', forge_commit=None,
            target_commit=None, entrypoint='spec.md', context=['spec.md','other.md'],
            next_actions=[], blockers=[]))
        self.g = {'records': [
            dict(id='requirement', kind='requirement', files=['spec.md'], depends_on=[]),
            dict(id='novel', kind='new-domain-method', files=[], depends_on=['requirement']),
            dict(id='proof', kind='evidence', files=[], depends_on=['novel']),
            dict(id='unrelated', kind='task', files=[], depends_on=[])]}

    def test_transitive(self):
        (self.p / 'spec.md').write_text('changed')
        r = impact(self.p, self.m, self.g)
        self.assertEqual([a['id'] for a in r['affected']], ['novel','proof','requirement'])
        self.assertFalse(r['coverage_complete'])

    def test_unchanged(self):
        self.assertEqual(impact(self.p,self.m,self.g)['affected'], [])

    def test_unmapped(self):
        (self.p / 'other.md').write_text('changed')
        self.assertEqual(impact(self.p,self.m,self.g)['unmapped_changes'], ['other.md'])

    def test_unwatched(self):
        self.g['records'][1]['files'] = ['unwatched.py']
        self.assertEqual(impact(self.p,self.m,self.g)['unwatched_dependencies'], ['unwatched.py'])

    def test_cycle(self):
        self.g['records'][0]['depends_on'] = ['proof']
        self.assertEqual(len(impact(self.p,self.m,self.g,['novel'])['affected']), 3)

    def test_dangling(self):
        self.g['records'][0]['depends_on'] = ['absent']
        with self.assertRaises(ValueError):
            impact(self.p,self.m,self.g)

    def test_explicit_unknown(self):
        with self.assertRaises(ValueError):
            impact(self.p,self.m,self.g,['absent'])

    def test_duplicate(self):
        self.g['records'].append(self.g['records'][0])
        with self.assertRaises(ValueError):
            impact(self.p,self.m,self.g)
