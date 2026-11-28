"""Build an optional, skill-only portable plugin ZIP from a committed Forge revision."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from forge_integrate import git

ROOT = Path(__file__).resolve().parent
# Curated public foundation assets only; no project contents, history or local secrets.
REFERENCES = (
    'README.md', 'RELEASE.md', 'START.md', 'requirements.md', 'detail.md',
    'architect-v0.5.md', 'generative-architecture.md', 'evaluation.md',
    'evaluation-v0.5.md', 'bootstrap/contract.md', 'bootstrap/portable-project.md',
    'bootstrap/quickstart.md', 'bootstrap/handoff.md', 'bootstrap/integration.md',
    'bootstrap/change-impact.md', 'bootstrap/distribution.md', 'bootstrap/agent-adapters.md', 'bootstrap/progress.md', 'bootstrap/records.md', 'bootstrap/session.md', 'bootstrap/adaptation.md',
    'evaluation/first-use.md', 'evaluation/acceptance-index.md', 'evaluation/release-readiness.md', 'evaluation/run-record.md', 'evaluation/calibration-v0.12.md', 'evaluation/rubric.json', 'schemas/blueprint.schema.json', 'schemas/record.schema.json', 'schemas/project.schema.json', 'schemas/example-response-map.schema.json',
    'knowledge/README.md', 'knowledge/lessons.md', 'knowledge/design-reasoning.md',
    'evaluation/design-worked-example.md',
    *('.agents/skills/' + name + '/SKILL.md' for name in (
        'architect-project', 'discover-intent', 'research-knowledge', 'design-method',
        'design-organization', 'design-operations', 'review-blueprint', 'adapt-harness')),
)
SOURCE_FILES = ('distribution/plugin.json', 'distribution/SKILL.md', *REFERENCES)
PREFIX = 'skills/engineering-forge/'


def committed_blob(repo, commit, path):
    raw = git(repo, 'ls-tree', '-z', commit, '--', path)
    items = [x for x in raw.split(b'\0') if x]
    if len(items) != 1:
        raise ValueError('required source missing or ambiguous: ' + path)
    meta, name = items[0].split(b'\t', 1)
    mode, kind, oid = meta.decode('ascii').split()
    if name.decode('utf-8') != path or kind != 'blob' or mode != '100644':
        raise ValueError('required source is not a normal committed file: ' + path)
    data = git(repo, 'cat-file', 'blob', oid)
    data.decode('utf-8')  # All selected inputs are text.
    return data


def build(repo, ref='HEAD'):
    repo = Path(repo).resolve()
    if not isinstance(ref, str) or not ref or ref.startswith('-'):
        raise ValueError('invalid source ref')
    commit = git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()
    if not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', commit):
        raise ValueError('invalid resolved commit')
    blobs = {p: committed_blob(repo, commit, p) for p in SOURCE_FILES}
    manifest = json.loads(blobs['distribution/plugin.json'])
    if (manifest.get('$schema') != 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
            or manifest.get('name') != 'engineering-forge'
            or not re.fullmatch(r'\d+\.\d+\.\d+', manifest.get('version', ''))
            or set(manifest) != {'$schema', 'name', 'version', 'description'}):
        raise ValueError('unexpected skill-only plugin manifest')
    if not blobs['distribution/SKILL.md'].startswith(b'---\nname: engineering-forge\n'):
        raise ValueError('invalid starter skill')
    package = {'plugin.json': blobs['distribution/plugin.json'],
               PREFIX + 'SKILL.md': blobs['distribution/SKILL.md']}
    package.update({PREFIX + 'references/' + p: blobs[p] for p in REFERENCES})
    provenance = {'source_commit': commit, 'source_repository': '708san/engineering-forge',
                  'sha256': {p: hashlib.sha256(data).hexdigest() for p, data in sorted(package.items())},
                  'runtime_verified': False, 'approval_verified': False}
    package[PREFIX + 'references/SOURCE.json'] = (json.dumps(provenance, sort_keys=True,
        indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for path, data in sorted(package.items()):
            item = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            z.writestr(item, data)
    return out.getvalue(), provenance


def write_new(path, data):
    with Path(path).open('xb') as f:
        f.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='explicit committed foundation revision')
    parser.add_argument('--output', required=True, help='new ZIP path; never overwrite')
    args = parser.parse_args()
    try:
        data, meta = build(ROOT, args.ref)
        write_new(args.output, data)
    except (OSError, ValueError, TypeError, AttributeError) as e:
        print(f'pack blocked: {e}', file=sys.stderr)
        return 1
    print(json.dumps({'source_commit': meta['source_commit'], 'output': args.output,
                      'sha256': hashlib.sha256(data).hexdigest(), 'runtime_verified': False,
                      'installed': False, 'published': False}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
