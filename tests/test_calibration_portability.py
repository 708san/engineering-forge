"""Execute the public hearing prototype outside the foundation checkout."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class CalibrationPortabilityTests(unittest.TestCase):
    def test_hearing_standalone(self):
        source = Path(__file__).resolve().parents[1] / 'examples/calibration-hearing'
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'standalone'
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__'))
            env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
            result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_hearing'],
                                    cwd=destination, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Ran 15 tests', result.stderr)
