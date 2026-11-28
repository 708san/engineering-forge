"""Read-only check of a Forge skill ZIP against a separately retained release digest."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

from forge_json import loads
from forge_pack import PREFIX, REFERENCES

MANIFEST = PREFIX + 'references/SOURCE.json'
EXPECTED = {'plugin.json', PREFIX + 'SKILL.md',
            *(PREFIX + 'references/' + p for p in REFERENCES)}
MAX_TOTAL = 16 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(path, expected_commit, expected_sha256):
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', expected_commit):
        raise ValueError('expected full commit ID required')
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('expected SHA-256 required')
    with Path(path).open('rb') as f:
        raw = f.read(MAX_TOTAL + 1)
    if len(raw) > MAX_TOTAL:
        raise ValueError('package exceeds size limit')
    if digest(raw) != expected_sha256:
        raise ValueError('package SHA-256 mismatch')
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        items = z.infolist()
        names = [i.filename for i in items]
        if len(names) != len(set(names)) or set(names) != EXPECTED | {MANIFEST}:
            raise ValueError('unexpected, duplicate or missing package path')
        if sum(i.file_size for i in items) > MAX_TOTAL:
            raise ValueError('expanded package exceeds size limit')
        for i in items:
            if (i.is_dir() or i.create_system != 3 or
                    not stat.S_ISREG(i.external_attr >> 16) or i.flag_bits & 1):
                raise ValueError('nonregular or encrypted package entry')
        m = loads(z.read(MANIFEST).decode('utf-8'))
        if (not isinstance(m, dict) or set(m) != {'source_commit', 'source_repository',
                'sha256', 'runtime_verified', 'approval_verified'}
                or m['source_commit'] != expected_commit
                or m['source_repository'] != '708san/engineering-forge'
                or m['runtime_verified'] is not False or m['approval_verified'] is not False
                or not isinstance(m['sha256'], dict) or set(m['sha256']) != EXPECTED):
            raise ValueError('provenance mismatch')
        for name in sorted(EXPECTED):
            contents = z.read(name)
            contents.decode('utf-8')
            if digest(contents) != m['sha256'][name]:
                raise ValueError('entry digest mismatch: ' + name)
    return {'source_commit': expected_commit, 'package_sha256': expected_sha256,
            'entry_count': len(EXPECTED), 'content_check': 'match',
            'release_authenticity_verified': False, 'runtime_verified': False,
            'installed': False, 'files_extracted': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package')
    p.add_argument('--commit', required=True)
    p.add_argument('--sha256', required=True)
    a = p.parse_args()
    try:
        print(json.dumps(verify(a.package, a.commit, a.sha256), indent=2))
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as e:
        print(f'package check blocked: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
