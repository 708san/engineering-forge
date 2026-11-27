import tempfile
import unittest
from pathlib import Path
from forge_handoff import snapshot, verify, load


class HandoffTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.p = Path(temp.name)
        (self.p / 'START-HERE.md').write_text('local context')
        self.s = dict(project='any new project', forge_commit='a' * 40,
                      target_commit=None, entrypoint='START-HERE.md',
                      context=['START-HERE.md'], next_actions=['proposed task'], blockers=[])

    def test_roundtrip(self):
        m = snapshot(self.p, self.s)
        result = verify(self.p, m)
        self.assertEqual(result['context_check'], 'match')
        self.assertFalse(result['authority_verified'])
        self.assertFalse(result['git_revision_verified'])
        self.assertTrue(result['next_actions_are_proposals'])

    def test_edit(self):
        m = snapshot(self.p, self.s)
        (self.p / 'START-HERE.md').write_text('changed')
        self.assertEqual(verify(self.p, m)['changed'], ['START-HERE.md'])

    def test_missing(self):
        m = snapshot(self.p, self.s)
        (self.p / 'START-HERE.md').unlink()
        with self.assertRaises(ValueError):
            verify(self.p, m)

    def test_unsafe_paths(self):
        for name in ('../outside', '/etc/passwd', 'a/../b', 'a//b', 'a\\b', '.git/config', '.'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                snapshot(self.p, dict(self.s, context=[self.s['entrypoint'], name]))

    def test_link(self):
        (self.p / 'alias').symlink_to(self.p / 'START-HERE.md')
        with self.assertRaises(ValueError):
            snapshot(self.p, dict(self.s, context=[self.s['entrypoint'], 'alias']))

    def test_entrypoint(self):
        with self.assertRaises(ValueError):
            snapshot(self.p, dict(self.s, context=[]))

    def test_ambiguous(self):
        with self.assertRaises(ValueError):
            snapshot(self.p, dict(self.s, context=['START-HERE.md', 'start-here.md']))

    def test_bad_digest_map(self):
        m = snapshot(self.p, self.s)
        m['sha256'] = {}
        with self.assertRaises(ValueError):
            verify(self.p, m)

    def test_bad_revision(self):
        with self.assertRaises(ValueError):
            snapshot(self.p, dict(self.s, forge_commit='main'))

    def test_duplicate_keys(self):
        p = self.p / 'duplicate.json'
        p.write_text('{"context": [], "context": []}')
        with self.assertRaises(ValueError):
            load(p)
