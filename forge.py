"""Optional entry point for Engineering Forge's local helpers (no AI or network required)."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

COMMANDS = {
    'preview': 'forge_preview.py',
    'validate': 'forge_validate.py',
    'handoff': 'forge_handoff.py',
    'integrate': 'forge_integrate.py',
    'impact': 'forge_impact.py',
}


def doctor(target=None):
    result = {
        'python_version': '.'.join(map(str, sys.version_info[:3])),
        'python_supported': sys.version_info >= (3, 11),
        'git_executable': 'found' if shutil.which('git') else 'missing',
        'jsonschema_discoverable': importlib.util.find_spec('jsonschema') is not None,
        'codex_executable': 'found' if shutil.which('codex') else 'not_found_on_path',
        'network_access': 'unverified',
        'github_write_access': 'unverified',
        'native_skills_loaded': 'unverified',
        'operation_authority': 'unverified',
        'target': {'status': 'not_requested'},
        'readiness_verified': False,
    }
    if target is not None:
        try:
            from forge_integrate import clean_head
            from forge_preview import root
            path = root(target)
            result['target'] = {'status': 'clean_head_observed', 'head': clean_head(path)}
        except (OSError, ValueError) as e:
            result['target'] = {'status': 'blocked_or_unconfirmed', 'reason': str(e)}
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['doctor', *COMMANDS])
    p.add_argument('arguments', nargs=argparse.REMAINDER)
    args = p.parse_args(argv)
    if args.command == 'doctor':
        d = argparse.ArgumentParser(prog='forge.py doctor', description='Observe local capabilities; no authority or runtime guarantees.')
        d.add_argument('--target', help='optional trusted local Git worktree root')
        opts = d.parse_args(args.arguments)
        print(json.dumps(doctor(opts.target), ensure_ascii=False, indent=2))
        return 0
    script = Path(__file__).resolve().parent / COMMANDS[args.command]
    return subprocess.run([sys.executable, '-B', str(script), *args.arguments], check=False).returncode


if __name__ == '__main__':
    sys.exit(main())
