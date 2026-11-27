"""Read-only snapshot/check of project-local handoff context; never execute instructions."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys

from forge_preview import root, check_name, key, digest

FIELDS = {'project', 'forge_commit', 'target_commit', 'entrypoint', 'context',
          'next_actions', 'blockers'}


def load(path):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError(f'duplicate JSON key: {k}')
            result[k] = v
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(spec):
    if not isinstance(spec, dict) or set(spec) != FIELDS:
        raise ValueError('invalid handoff fields')
    if not nonempty(spec['project']) or not nonempty(spec['entrypoint']):
        raise ValueError('project and entrypoint required')
    for field in ('forge_commit', 'target_commit'):
        v = spec[field]
        if v is not None and (not isinstance(v, str) or not re.fullmatch('[0-9a-f]{40}', v)):
            raise ValueError(f'invalid {field}; use null if unconfirmed')
    for field in ('context', 'next_actions', 'blockers'):
        v = spec[field]
        if not isinstance(v, list) or not all(nonempty(x) for x in v):
            raise ValueError(f'invalid {field}')
    if spec['entrypoint'] not in spec['context']:
        raise ValueError('entrypoint must be in context')
    names = [key(x) for x in spec['context']]
    if len(set(names)) != len(names):
        raise ValueError('duplicate or ambiguous context path')


def local_file(base, name):
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or not path.parts or '..' in path.parts:
        raise ValueError(f'unsafe relative path: {name!r}')
    p = base
    for part in path.parts:
        check_name(part)
        matches = [x for x in p.iterdir() if key(x.name) == key(part)]
        if len(matches) != 1 or matches[0].name != part or matches[0].is_symlink():
            raise ValueError(f'missing, ambiguous or linked context: {name!r}')
        p = matches[0]
    return p


def snapshot(directory, spec):
    validate(spec)
    base = root(directory)
    return {'version': 1, 'spec': spec,
            'sha256': {name: digest(local_file(base, name)) for name in spec['context']}}


def verify(directory, manifest):
    if (not isinstance(manifest, dict) or set(manifest) != {'version', 'spec', 'sha256'}
            or type(manifest['version']) is not int or manifest['version'] != 1):
        raise ValueError('unsupported manifest')
    current = snapshot(directory, manifest['spec'])
    expected = manifest['sha256']
    if (not isinstance(expected, dict) or expected.keys() != current['sha256'].keys()
            or not all(isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v)
                       for v in expected.values())):
        raise ValueError('invalid digest map')
    changed = sorted(k for k, v in current['sha256'].items() if expected[k] != v)
    return {'context_check': 'changed' if changed else 'match', 'changed': changed,
            'git_revision_verified': False, 'authority_verified': False,
            'next_actions_are_proposals': True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('snapshot', 'verify'))
    p.add_argument('directory')
    p.add_argument('document')
    args = p.parse_args()
    try:
        data = load(args.document)
        result = (snapshot if args.command == 'snapshot' else verify)(args.directory, data)
    except (OSError, ValueError, RecursionError) as e:
        print(f'handoff blocked: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get('changed') else 0


if __name__ == '__main__':
    sys.exit(main())
