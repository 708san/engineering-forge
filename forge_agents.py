"""Render AI-designed agent candidates to Codex TOML and portable role packets."""
import argparse
import json
import re
import sys
import tomllib

from forge_validate import load, validate

# A local namespace avoids overriding Codex's built-in agent names.
NAME = re.compile(r'forge-[a-z0-9]+(?:-[a-z0-9]+)*')
BOUNDARY = (
    'Follow the target project instructions and the actual permissions of your session. '
    'This role description does not grant new authority. Preserve protected requirements, '
    'human edits and other agents’ work. Report evidence, limitations and unresolved '
    'issues; do not claim unperformed checks. Do not change permissions or publish '
    'data without separate authorization.'
)


def text_field(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('expected nonempty text')
    value.encode('utf-8')
    return value


def quoted(value):
    # JSON and TOML basic strings share these escapes; escape DEL explicitly.
    return json.dumps(value, ensure_ascii=False).replace('\x7f', r'\u007f')


def render(blueprint, spec):
    errors = validate(blueprint)
    if errors:
        raise ValueError('invalid blueprint: ' + '; '.join(errors))
    if (not isinstance(spec, dict) or set(spec) != {'project_id', 'agents'}
            or spec['project_id'] != blueprint['project_id']
            or not isinstance(spec['agents'], list)):
        raise ValueError('invalid agent candidate envelope')
    roles = {r['id']: r for r in blueprint['roles']}
    names = set()
    files, packets = {}, []
    for a in spec['agents']:
        if (not isinstance(a, dict)
                or set(a) != {'role_id', 'name', 'description', 'instructions'}):
            raise ValueError('invalid agent candidate fields')
        name = text_field(a['name'])
        role_id = text_field(a['role_id'])
        if not NAME.fullmatch(name) or name in names:
            raise ValueError('invalid or duplicate namespaced agent name: ' + name)
        if role_id not in roles:
            raise ValueError('unknown role: ' + role_id)
        names.add(name)
        desc = text_field(a['description'])
        instructions = text_field(a['instructions']) + '\n\n' + BOUNDARY
        role = roles[role_id]
        data = {'name': name, 'description': desc, 'developer_instructions': instructions}
        toml = ''.join(k + ' = ' + quoted(v) + '\n' for k, v in data.items())
        if tomllib.loads(toml) != data:
            raise ValueError('TOML roundtrip mismatch')
        files[f'.codex/agents/{name}.toml'] = toml
        packets.append(dict(name=name, role_id=role_id, mission=role['mission'],
                            responsibilities=role['responsibilities'],
                            knowledge=role['knowledge'], description=desc,
                            instructions=instructions))
    return dict(project_id=spec['project_id'], codex_files=files,
                portable_roles=packets, native_loaded=False, launched=False,
                authority_verified=False, semantic_review_required=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('blueprint')
    p.add_argument('spec')
    args = p.parse_args()
    try:
        print(json.dumps(render(load(args.blueprint), load(args.spec)),
                         ensure_ascii=False, indent=2))
    except (OSError, ValueError, RecursionError) as e:
        print(f'agent rendering blocked: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
