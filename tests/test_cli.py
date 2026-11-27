import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forge_integrate import git

ROOT = Path(__file__).resolve().parents[1]


def cli(*args):
    return subprocess.run([sys.executable, '-B', str(ROOT / 'forge.py'), *map(str,args)],
                          capture_output=True, text=True, check=False)


class CliTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.t = Path(temp.name) / 'target'
        self.c = Path(temp.name) / 'candidate'
        self.t.mkdir()
        self.c.mkdir()
        git(self.t, 'init', '-q')
        git(self.t, 'config', 'user.name', 'CLI Test')
        git(self.t, 'config', 'user.email', 'test@example.invalid')
        git(self.t, 'commit', '--allow-empty', '-qm', 'base')

    def test_doctor_unknown_is_not_success(self):
        r = cli('doctor', '--target', self.t)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['target']['status'], 'clean_head_observed')
        self.assertFalse(data['readiness_verified'])
        self.assertEqual(data['native_skills_loaded'], 'unverified')
        self.assertEqual(data['operation_authority'], 'unverified')

    def test_doctor_dirty(self):
        (self.t / 'edit').write_text('human')
        r = cli('doctor', '--target', self.t)
        self.assertEqual(json.loads(r.stdout)['target']['status'], 'blocked_or_unconfirmed')

    def test_integrate_cli(self):
        (self.c / 'novel.md').write_text('candidate')
        r = cli('integrate', 'plan', self.c, self.t)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(r.stdout)
        args = ('integrate', 'stage', self.c, self.t, '--expect', plan['token'], '--branch', 'forge/cli')
        self.assertEqual(cli(*args).returncode, 1)
        r = cli(*args, '--confirm')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(git(self.t, 'show', 'forge/cli:novel.md'), b'candidate')
        self.assertFalse((self.t / 'novel.md').exists())

    def test_validate_cli(self):
        r = cli('validate', ROOT / 'examples/portable-candidate/blueprint.json', '--new-proposal')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(r.stdout)['approval_verified'])

    def test_handoff_cli(self):
        e = ROOT / 'examples/uncertain-order'
        r = cli('handoff', 'verify', e, e / 'handoff-manifest.json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['context_check'], 'match')
