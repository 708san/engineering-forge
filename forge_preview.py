"""Read-only preview of AI-generated text or binary artifacts; never applies them."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import unicodedata


def root(path):
    p = Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError(f"not a real directory: {p}")
    return p.resolve(strict=True)


def digest(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"not a regular file: {path}")
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def key(name):
    return unicodedata.normalize('NFC', name).casefold()


def check_name(name):
    if (key(name) == '.git' or name.endswith((' ', '.')) or
            any(ord(c) < 32 or c in '\\:<>"|?*' for c in name) or
            name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
                *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}):
        raise ValueError(f"unsafe path component: {name!r}")


def walk_error(error):
    raise error


def files(candidate):
    for base, dirs, names in os.walk(candidate, onerror=walk_error, followlinks=False):
        seen = set()
        for name in sorted(dirs + names):
            check_name(name)
            if key(name) in seen:
                raise ValueError(f"ambiguous path: {name}")
            seen.add(key(name))
            p = Path(base) / name
            mode = p.lstat().st_mode
            if p.is_symlink() or not (stat.S_ISDIR(mode) if name in dirs else stat.S_ISREG(mode)):
                raise ValueError(f"unsupported path: {p}")
        dirs.sort()
        for name in sorted(names):
            yield Path(base) / name


def target_state(target, relative):
    p = target
    for i, name in enumerate(relative.parts):
        matches = [x for x in p.iterdir() if key(x.name) == key(name)]
        if not matches:
            return 'missing', None
        if len(matches) != 1 or matches[0].name != name:
            return 'path_conflict', None
        p = matches[0]
        mode = p.lstat().st_mode
        if i < len(relative.parts) - 1:
            if not stat.S_ISDIR(mode):
                return 'path_conflict', None
        elif not stat.S_ISREG(mode):
            return 'path_conflict', None
    return 'file', digest(p)


def preview(candidate, target):
    c, t = root(candidate), root(target)
    if c == t or c in t.parents or t in c.parents:
        raise ValueError('candidate and target must be separate directory trees')
    entries = []
    for path in sorted(files(c)):
        relative = path.relative_to(c)
        new = digest(path)
        state, old = target_state(t, relative)
        action = {'missing': 'add', 'path_conflict': 'conflict'}.get(state)
        if action is None:
            action = 'unchanged' if old == new else 'conflict'
        entries.append(dict(path=relative.as_posix(), action=action,
                            candidate_sha256=new, target_sha256=old))
    if not entries:
        raise ValueError('empty candidate')
    return dict(version=1, mode='preview_only', candidate=str(c), target=str(t),
                entries=entries, conflicts=sum(x['action'] == 'conflict' for x in entries))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', help='separate directory with generated artifacts')
    parser.add_argument('target', help='existing destination directory')
    args = parser.parse_args()
    try:
        result = preview(args.candidate, args.target)
    except (OSError, ValueError) as e:
        print(f'preview blocked: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result['conflicts'] else 0


if __name__ == '__main__':
    sys.exit(main())
