"""Exercise an isolated project from initial integration through a human edit."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forge_handoff import load, verify
from forge_impact import impact
from forge_integrate import git, plan, stage


class LifecycleTest(unittest.TestCase):
    def test_new_project_update_and_review(self):
        with tempfile.TemporaryDirectory() as d:
            t, c = Path(d) / 'target', Path(d) / 'candidate'
            t.mkdir()
            example = Path(__file__).resolve().parents[1] / 'examples/uncertain-order'
            shutil.copytree(example, c, ignore=shutil.ignore_patterns('__pycache__'))
            git(t, 'init', '-q')
            git(t, 'config', 'user.name', 'Integration Test')
            git(t, 'config', 'user.email', 'test@example.invalid')
            git(t, 'commit', '--allow-empty', '-qm', 'initial')
            p = plan(c, t)
            r = stage(c, t, {}, p['token'], 'forge/initial')
            self.assertFalse((t / 'order.py').exists())
            git(t, 'merge', '--ff-only', r['branch'])
            manifest = load(t / 'handoff-manifest.json')
            self.assertEqual(verify(t, manifest)['context_check'], 'match')
            prior = r['next_prior_candidate']
            purpose = t / 'PURPOSE.md'
            purpose.write_text(purpose.read_text() + '\nHuman note.\n')
            git(t, 'add', 'PURPOSE.md')
            git(t, 'commit', '-qm', 'human change')
            code = c / 'order.py'
            code.write_text(code.read_text() + '\n# candidate update\n')
            p = plan(c, t, prior)
            actions = {e['path']: e['action'] for e in p['entries']}
            self.assertEqual(actions['PURPOSE.md'], 'preserve')
            self.assertEqual(actions['order.py'], 'update')
            r = stage(c, t, prior, p['token'], 'forge/update')
            git(t, 'merge', '--ff-only', r['branch'])
            self.assertIn('Human note.', purpose.read_text())
            graph = {'records': [
                dict(id='REQ', kind='requirement', files=['PURPOSE.md'], depends_on=[]),
                dict(id='IMPL', kind='implementation', files=['order.py'], depends_on=['REQ']),
                dict(id='TEST', kind='evidence', files=['test_order.py'], depends_on=['IMPL'])]}
            report = impact(t, manifest, graph)
            self.assertEqual({x['id'] for x in report['affected']}, {'REQ', 'IMPL', 'TEST'})
            subprocess.run([sys.executable, '-B', '-m', 'unittest', '-q', 'test_order'], cwd=t, check=True)
            (c / 'PURPOSE.md').write_text('AI changed too')
            self.assertEqual(plan(c, t, r['next_prior_candidate'])['conflicts'], 1)
