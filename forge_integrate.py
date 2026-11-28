"""Plan and stage generated files on a NEW local Git branch; never checkout or push."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

from forge_preview import root, files, key, check_name, target_state
from forge_handoff import load


def git(repo, *args, data=None, index=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    if index is not None:
        env['GIT_INDEX_FILE'] = str(index)
    result = subprocess.run(['git', '-C', str(repo), *args], input=data,
                            capture_output=True, env=env, check=False)
    if result.returncode:
        raise ValueError('git failed: ' + result.stderr.decode(errors='replace').strip())
    return result.stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def path_parts(name):
    p = PurePosixPath(name)
    if not p.parts or p.is_absolute() or p.as_posix() != name or '..' in p.parts:
        raise ValueError('unsafe path: ' + name)
    for part in p.parts:
        check_name(part)
    return p.parts


def clean_head(repo):
    if Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != repo:
        raise ValueError('target must be the Git worktree root')
    if git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all'):
        raise ValueError('target has uncommitted or untracked changes')
    return git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()


def plan(candidate, target, prior=None):
    c, t = root(candidate), root(target)
    if c == t or c in t.parents or t in c.parents:
        raise ValueError('separate candidate and target trees required')
    if prior is None:
        prior = {}
    if not isinstance(prior, dict):
        raise ValueError('prior must be a path-to-SHA256 map')
    prior_aliases = {}
    prior_leaves = set()
    for name, value in prior.items():
        parts = path_parts(name)
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            normalized = key(prefix)
            if normalized in prior_aliases and prior_aliases[normalized] != prefix:
                raise ValueError('ambiguous prior path: ' + name)
            prior_aliases[normalized] = prefix
        prior_leaves.add(key(name))
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError('invalid prior digest')
    if any(any('/'.join(name.split('/')[:i]) in prior_leaves
               for i in range(1, len(name.split('/')))) for name in prior_leaves):
        raise ValueError('prior contains file/directory conflict')
    base = clean_head(t)
    tracked = {}
    for item in git(t, 'ls-tree', '-rz', base).split(b'\0'):
        if item:
            meta, name = item.split(b'\t', 1)
            mode, _, oid = meta.decode().split()
            tracked[name.decode('utf-8')] = (mode, oid)
    aliases = {}
    for name in tracked:
        parts = PurePosixPath(name).parts
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            aliases.setdefault(key(prefix), set()).add(prefix)
    entries = []
    for p in sorted(files(c)):
        name = p.relative_to(c).as_posix()
        parts = path_parts(name)
        new = sha(p.read_bytes())
        old, mode = None, '100644'
        bad = False
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            if aliases.get(key(prefix), {prefix}) != {prefix}:
                bad = True
            if i < len(parts) and prefix in tracked:
                bad = True
            if prior_aliases.get(key(prefix), prefix) != prefix:
                bad = True
            if i < len(parts) and key(prefix) in prior_leaves:
                bad = True
        if key(name) in prior_aliases and key(name) not in prior_leaves:
            bad = True
        if name in tracked:
            mode, oid = tracked[name]
            if mode not in ('100644', '100755'):
                bad = True
            else:
                old = sha(git(t, 'cat-file', 'blob', oid))
        elif key(name) in aliases:
            bad = True
        work_state, work_hash = target_state(t, Path(name))
        if (name not in tracked and work_state != 'missing') or (
                name in tracked and (work_state != 'file' or work_hash != old)):
            bad = True
        if bad:
            action = 'conflict'
        elif old is None:
            # A previously managed file deleted by a human is not resurrected.
            action = 'conflict' if name in prior else 'add'
        elif new == old:
            action = 'unchanged'
        elif prior.get(name) == old:
            action = 'update'
        elif prior.get(name) == new:
            action = 'preserve'
        else:
            action = 'conflict'
        entries.append(dict(path=name, action=action, old_sha256=old,
                            new_sha256=new, mode=mode))
    if not entries:
        raise ValueError('empty candidate')
    next_prior = dict(prior)
    for e in entries:
        if e['action'] in ('add', 'update'):
            next_prior[e['path']] = e['new_sha256']
    result = dict(version=1, base=base, candidate=str(c), target=str(t),
                  next_prior_candidate=next_prior,
                  entries=entries, omitted_prior=sorted(set(prior)-{e['path'] for e in entries}),
                  conflicts=sum(e['action']=='conflict' for e in entries))
    result['token'] = sha(json.dumps(result, sort_keys=True, ensure_ascii=True).encode())
    return result


def stage(candidate, target, prior, expected, branch):
    p = plan(candidate, target, prior)
    if p['token'] != expected or p['conflicts']:
        raise ValueError('plan changed or conflicts remain; regenerate and review')
    t, c = Path(p['target']), Path(p['candidate'])
    if not branch.startswith('forge/'):
        raise ValueError('use a new forge/ branch')
    ref = 'refs/heads/' + branch
    git(t, 'check-ref-format', ref)
    changes = [e for e in p['entries'] if e['action'] in ('add', 'update')]
    if not changes:
        raise ValueError('nothing to integrate')
    with tempfile.TemporaryDirectory() as d:
        index = Path(d) / 'index'
        git(t, 'read-tree', p['base'], index=index)
        for e in changes:
            data = (c / e['path']).read_bytes()
            if sha(data) != e['new_sha256']:
                raise ValueError('candidate changed during staging')
            oid = git(t, 'hash-object', '-w', '--stdin', data=data).decode().strip()
            git(t, 'update-index', '--add', '--cacheinfo', e['mode'], oid, e['path'], index=index)
        tree = git(t, 'write-tree', index=index).decode().strip()
        commit = git(t, '-c', 'commit.gpgsign=false', 'commit-tree', tree, '-p', p['base'],
                     '-m', 'Engineering Forge integration candidate').decode().strip()
        if plan(candidate, target, prior)['token'] != expected:
            raise ValueError('candidate or target changed during staging')
        git(t, 'update-ref', '--no-deref', ref, commit, '0' * len(commit))
    return dict(branch=branch, commit=commit, base=p['base'], changed=len(changes),
                checked_out=False, pushed=False, approval_verified=False,
                next_prior_candidate=p['next_prior_candidate'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'stage'))
    parser.add_argument('candidate')
    parser.add_argument('target')
    parser.add_argument('--prior', help='independently stored prior-generated path/hash map')
    parser.add_argument('--expect')
    parser.add_argument('--branch')
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    try:
        prior = load(args.prior) if args.prior else {}
        if prior is None:
            raise ValueError('null prior')
        if args.command == 'stage':
            if not (args.confirm and args.expect and args.branch):
                raise ValueError('stage requires --confirm, --expect and --branch')
            result = stage(args.candidate, args.target, prior, args.expect, args.branch)
        else:
            result = plan(args.candidate, args.target, prior)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if result.get('conflicts') else 0
    except (OSError, ValueError, RecursionError) as e:
        print(f'integration blocked: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
