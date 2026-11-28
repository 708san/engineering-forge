import tempfile
import unittest
from pathlib import Path
from forge_integrate import git, plan, stage, sha


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.t = Path(temp.name) / 'target'
        self.c = Path(temp.name) / 'candidate'
        self.t.mkdir()
        self.c.mkdir()
        git(self.t, 'init', '-q')
        git(self.t, 'config', 'user.name', 'Test')
        git(self.t, 'config', 'user.email', 'test@example.invalid')
        (self.t / 'a').write_text('old')
        git(self.t, 'add', '.')
        git(self.t, 'commit', '-qm', 'base')
        self.base = git(self.t, 'rev-parse', 'HEAD').strip()

    def test_add_branch_only(self):
        (self.c / 'new').write_text('novel')
        p = plan(self.c, self.t)
        r = stage(self.c, self.t, {}, p['token'], 'forge/demo')
        self.assertEqual(git(self.t, 'show', r['commit'] + ':new'), b'novel')
        self.assertEqual(git(self.t, 'show', r['commit'] + ':a'), b'old')
        self.assertEqual(git(self.t, 'rev-parse', 'HEAD').strip(), self.base)
        self.assertFalse((self.t / 'new').exists())

    def test_update_prior(self):
        (self.c / 'a').write_text('new')
        prior = {'a': sha(b'old')}
        p = plan(self.c, self.t, prior)
        self.assertEqual(p['entries'][0]['action'], 'update')
        r = stage(self.c, self.t, prior, p['token'], 'forge/update')
        self.assertEqual(git(self.t, 'show', r['commit'] + ':a'), b'new')
        self.assertEqual((self.t / 'a').read_text(), 'old')

    def test_preserve_human_edit(self):
        (self.c / 'a').write_text('previous')
        p = plan(self.c, self.t, {'a': sha(b'previous')})
        self.assertEqual(p['entries'][0]['action'], 'preserve')

    def test_conflict(self):
        (self.c / 'a').write_text('new')
        p = plan(self.c, self.t, {'a': sha(b'previous')})
        self.assertEqual(p['conflicts'], 1)
        with self.assertRaises(ValueError):
            stage(self.c, self.t, {'a': sha(b'previous')}, p['token'], 'forge/no')

    def test_untracked(self):
        (self.c / 'new').write_text('new')
        (self.t / 'human').write_text('edit')
        with self.assertRaises(ValueError):
            plan(self.c, self.t)

    def test_stale_candidate(self):
        (self.c / 'new').write_text('new')
        p = plan(self.c, self.t)
        (self.c / 'new').write_text('changed')
        with self.assertRaises(ValueError):
            stage(self.c, self.t, {}, p['token'], 'forge/no')

    def test_existing_branch(self):
        (self.c / 'new').write_text('new')
        p = plan(self.c, self.t)
        git(self.t, 'branch', 'forge/existing')
        with self.assertRaises(ValueError):
            stage(self.c, self.t, {}, p['token'], 'forge/existing')
        self.assertEqual(git(self.t, 'rev-parse', 'forge/existing').strip(), self.base)

    def test_case_collision(self):
        (self.c / 'A').write_text('new')
        self.assertEqual(plan(self.c, self.t)['conflicts'], 1)

    def test_deleted_prior(self):
        (self.c / 'new').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'new': sha(b'old')})['conflicts'], 1)

    def test_omitted_prior_no_deletion(self):
        (self.c / 'new').write_text('new')
        p = plan(self.c, self.t, {'a': sha(b'old')})
        self.assertEqual(p['omitted_prior'], ['a'])
        r = stage(self.c, self.t, {'a': sha(b'old')}, p['token'], 'forge/keep')
        self.assertEqual(git(self.t, 'show', r['commit'] + ':a'), b'old')

    def test_target_head_changed(self):
        (self.c / 'new').write_text('new')
        p = plan(self.c, self.t)
        git(self.t, 'commit', '--allow-empty', '-qm', 'another')
        with self.assertRaises(ValueError):
            stage(self.c, self.t, {}, p['token'], 'forge/no')

    def test_file_directory_conflict(self):
        (self.c / 'a').mkdir()
        (self.c / 'a' / 'child').write_text('new')
        self.assertEqual(plan(self.c, self.t)['conflicts'], 1)

    def test_ignored_collision(self):
        (self.t / '.git/info/exclude').write_text('ignored\n')
        (self.t / 'ignored').write_text('human data')
        (self.c / 'ignored').write_text('new')
        self.assertEqual(plan(self.c, self.t)['conflicts'], 1)

    def test_hidden_worktree_edit(self):
        git(self.t, 'update-index', '--assume-unchanged', 'a')
        (self.t / 'a').write_text('hidden edit')
        (self.c / 'a').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'a': sha(b'old')})['conflicts'], 1)

    def test_do_not_claim_existing_equal_file(self):
        (self.c / 'a').write_text('old')
        self.assertEqual(plan(self.c, self.t)['next_prior_candidate'], {})

    def test_next_prior_candidate(self):
        (self.c / 'a').write_text('new')
        prior = {'a': sha(b'old')}
        p = plan(self.c, self.t, prior)
        r = stage(self.c, self.t, prior, p['token'], 'forge/update')
        self.assertEqual(r['next_prior_candidate'], {'a': sha(b'new')})

    def test_deleted_prior_case_alias(self):
        (self.c / 'New').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'new': sha(b'old')})['conflicts'], 1)

    def test_deleted_prior_unicode_alias(self):
        (self.c / 'cafe\u0301').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'caf\u00e9': sha(b'old')})['conflicts'], 1)

    def test_deleted_prior_file_to_directory(self):
        (self.c / 'removed').mkdir()
        (self.c / 'removed' / 'child').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'removed': sha(b'old')})['conflicts'], 1)

    def test_deleted_prior_directory_to_file(self):
        (self.c / 'removed').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'removed/child': sha(b'old')})['conflicts'], 1)

    def test_ambiguous_prior_rejected(self):
        (self.c / 'new').write_text('new')
        for prior in ({'A/x': sha(b'old'), 'a/y': sha(b'old')},
                      {'a': sha(b'old'), 'a/child': sha(b'old')}):
            with self.subTest(prior=prior), self.assertRaises(ValueError):
                plan(self.c, self.t, prior)

    def test_new_sibling_of_prior_file_allowed(self):
        (self.c / 'dir').mkdir()
        (self.c / 'dir' / 'new').write_text('new')
        self.assertEqual(plan(self.c, self.t, {'dir/old': sha(b'old')})['entries'][0]['action'], 'add')
