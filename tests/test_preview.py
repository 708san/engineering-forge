import tempfile
import unittest
from pathlib import Path
from forge_preview import preview


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.c = Path(self.temp.name) / 'candidate'
        self.t = Path(self.temp.name) / 'target'
        self.c.mkdir()
        self.t.mkdir()

    def test_add_without_write(self):
        (self.c / 'new-method.md').write_text('novel method')
        self.assertEqual(preview(self.c, self.t)['entries'][0]['action'], 'add')
        self.assertEqual(list(self.t.iterdir()), [])

    def test_existing_edit_and_identical(self):
        (self.c / 'a').write_text('new')
        (self.t / 'a').write_text('human edit')
        (self.c / 'b').write_text('same')
        (self.t / 'b').write_text('same')
        result = preview(self.c, self.t)
        self.assertEqual([x['action'] for x in result['entries']], ['conflict', 'unchanged'])
        self.assertEqual((self.t / 'a').read_text(), 'human edit')

    def test_nested_new_file(self):
        (self.c / 'novel').mkdir()
        (self.c / 'novel' / 'artifact.json').write_text('{}')
        self.assertEqual(preview(self.c, self.t)['entries'][0]['path'], 'novel/artifact.json')

    def test_candidate_symlink(self):
        (self.c / 'link').symlink_to(self.t, target_is_directory=True)
        with self.assertRaises(ValueError):
            preview(self.c, self.t)

    def test_target_symlink(self):
        (self.c / 'a').write_text('x')
        (self.t / 'a').symlink_to(self.c / 'a')
        self.assertEqual(preview(self.c, self.t)['conflicts'], 1)

    def test_parent_file(self):
        (self.c / 'a').mkdir()
        (self.c / 'a' / 'b').write_text('x')
        (self.t / 'a').write_text('existing')
        self.assertEqual(preview(self.c, self.t)['conflicts'], 1)

    def test_case_collision(self):
        (self.c / 'AGENTS.md').write_text('new')
        (self.t / 'agents.md').write_text('existing')
        self.assertEqual(preview(self.c, self.t)['conflicts'], 1)

    def test_git_metadata(self):
        (self.c / '.git').mkdir()
        with self.assertRaises(ValueError):
            preview(self.c, self.t)

    def test_empty(self):
        with self.assertRaises(ValueError):
            preview(self.c, self.t)

    def test_nested_roots(self):
        (self.c / 'target').mkdir()
        with self.assertRaises(ValueError):
            preview(self.c, self.c / 'target')


if __name__ == '__main__':
    unittest.main()
