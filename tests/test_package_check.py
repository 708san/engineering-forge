import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from forge_integrate import git
from forge_pack import build, SOURCE_FILES
from forge_package_check import verify, MANIFEST, MAX_TOTAL

ROOT = Path(__file__).resolve().parents[1]


class PackageCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.repo = Path(tmp.name)
        git(cls.repo, 'init', '-q')
        git(cls.repo, 'config', 'user.name', 'Test')
        git(cls.repo, 'config', 'user.email', 'test@example.invalid')
        for name in SOURCE_FILES:
            p = cls.repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((ROOT / name).read_bytes())
        git(cls.repo, 'add', '.')
        git(cls.repo, 'commit', '-qm', 'source')
        cls.raw, cls.meta = build(cls.repo)

    def check(self, raw=None, commit=None, checksum=None):
        raw = self.raw if raw is None else raw
        path = self.repo / 'check.zip'
        path.write_bytes(raw)
        return verify(path, commit or self.meta['source_commit'],
                      checksum or hashlib.sha256(raw).hexdigest())

    def changed(self, *, replacement=None, omit=None, extra=None):
        out = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(self.raw)) as old, zipfile.ZipFile(out, 'w') as new:
            for i in old.infolist():
                if i.filename == omit:
                    continue
                data = old.read(i.filename)
                if replacement and i.filename == replacement[0]:
                    data = replacement[1]
                new.writestr(i, data)
            if extra:
                new.writestr(*extra)
        return out.getvalue()

    def test_valid(self):
        r = self.check()
        self.assertEqual(r['content_check'], 'match')
        self.assertFalse(r['runtime_verified'])
        self.assertFalse(r['files_extracted'])

    def test_wrong_checksum(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            self.check(checksum='a'*64)

    def test_wrong_commit(self):
        with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
            self.check(commit='b'*40)

    def test_changed_entry_even_with_new_outer_hash(self):
        with self.assertRaisesRegex(ValueError, 'entry digest mismatch'):
            self.check(self.changed(replacement=('plugin.json', b'changed')))

    def test_missing_entry(self):
        with self.assertRaisesRegex(ValueError, 'package path'):
            self.check(self.changed(omit='plugin.json'))

    def test_extra_unsafe_entry(self):
        with self.assertRaisesRegex(ValueError, 'package path'):
            self.check(self.changed(extra=('../unexpected', b'bad')))

    def test_forged_runtime_claim(self):
        m = dict(self.meta, runtime_verified=True)
        with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
            self.check(self.changed(replacement=(MANIFEST, json.dumps(m).encode())))

    def test_oversize_package(self):
        with self.assertRaisesRegex(ValueError, 'size limit'):
            self.check(b'x' * (MAX_TOTAL + 1))
