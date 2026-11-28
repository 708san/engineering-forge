import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from forge_integrate import git
from forge_pack import build, write_new, SOURCE_FILES, PREFIX

ROOT = Path(__file__).resolve().parents[1]


class PackTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'Test')
        git(self.repo, 'config', 'user.email', 'test@example.invalid')
        for name in SOURCE_FILES:
            p = self.repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((ROOT / name).read_bytes())
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'source')

    def test_reproducible_provenance(self):
        data, meta = build(self.repo)
        self.assertEqual(data, build(self.repo)[0])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(json.loads(z.read('plugin.json'))['name'], 'engineering-forge')
            stored = json.loads(z.read(PREFIX + 'references/SOURCE.json'))
            self.assertEqual(stored, meta)
            for name, digest in meta['sha256'].items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)
            self.assertEqual(set(z.namelist()), set(meta['sha256']) | {PREFIX + 'references/SOURCE.json'})
            self.assertFalse(meta['runtime_verified'])

    def test_dirty_and_unlisted_files_are_excluded(self):
        before, _ = build(self.repo)
        (self.repo / 'README.md').write_text('uncommitted private edit')
        (self.repo / 'secret.txt').write_text('unlisted')
        self.assertEqual(before, build(self.repo)[0])

    def test_missing_committed_source_rejected(self):
        git(self.repo, 'rm', 'START.md')
        git(self.repo, 'commit', '-qm', 'remove')
        with self.assertRaises(ValueError):
            build(self.repo)

    def test_symlink_rejected(self):
        (self.repo / 'START.md').unlink()
        (self.repo / 'START.md').symlink_to('README.md')
        git(self.repo, 'add', 'START.md')
        git(self.repo, 'commit', '-qm', 'replace with link')
        with self.assertRaises(ValueError):
            build(self.repo)

    def test_no_overwrite(self):
        p = self.repo / 'out.zip'
        p.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            write_new(p, b'new')
        self.assertEqual(p.read_bytes(), b'original')

    def test_invalid_ref(self):
        with self.assertRaises(ValueError):
            build(self.repo, '--help')
