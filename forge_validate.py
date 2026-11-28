"""Validate a blueprint candidate, not its approval, quality or runtime behavior."""
import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).resolve().parent / 'schemas/blueprint.schema.json'


from forge_json import load


def validate(candidate, baseline=None):
    schema = load(SCHEMA)
    validator = Draft202012Validator(schema)
    errors = [f'schema: {list(e.absolute_path)}: {e.message}'
              for e in validator.iter_errors(candidate)]
    if errors:
        return errors
    groups = ('discoveries', 'outcomes', 'methods', 'roles', 'artifacts')
    ids = [x['id'] for group in groups for x in candidate[group]]
    if len(ids) != len(set(ids)):
        errors.append('duplicate record ID')
    outcomes = {x['id']: x for x in candidate['outcomes']}
    roles = {x['id'] for x in candidate['roles']}
    artifacts = {x['id'] for x in candidate['artifacts']}
    covered = set()
    for m in candidate['methods']:
        if set(m['outcome_ids']) - set(outcomes) or set(m['artifact_ids']) - set(artifacts):
            errors.append(f"invalid method reference: {m['id']}")
        if m['status'] in ('proposed', 'trial', 'selected'):
            covered.update(m['outcome_ids'])
    for a in candidate['artifacts']:
        if a['owner_role'] not in roles:
            errors.append(f"unknown owner: {a['id']}")
    for c in candidate['collaborations']:
        if {c['from_role'], c['to_role']} - set(roles):
            errors.append('invalid collaboration reference')
    for h in candidate['holds']:
        if h['outcome_id'] not in outcomes:
            errors.append('invalid hold reference')
        covered.add(h['outcome_id'])
    for oid, outcome in outcomes.items():
        if outcome['mandatory'] and oid not in covered:
            errors.append(f'unaddressed mandatory outcome: {oid}')
    if baseline is not None:
        if not isinstance(baseline, dict) or set(baseline) != {'project_id', 'intent_ref', 'outcomes'}:
            return errors + ['invalid baseline envelope']
        if any(candidate[k] != baseline[k] for k in ('project_id', 'intent_ref')):
            errors.append('baseline project or intent mismatch')
        b = baseline['outcomes']
        if not Draft202012Validator(schema['properties']['outcomes']).is_valid(b):
            return errors + ['invalid baseline outcomes']
        if len({o['id'] for o in b}) != len(b):
            errors.append('duplicate baseline outcome ID')
        for o in b:
            if o['mandatory'] and outcomes.get(o['id']) != o:
                errors.append(f"protected outcome differs or missing: {o['id']}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--baseline', help='separately supplied baseline; authenticity not verified')
    group.add_argument('--new-proposal', action='store_true', help='no prior baseline; not approved')
    args = parser.parse_args()
    try:
        candidate = load(args.candidate)
        baseline = load(args.baseline) if args.baseline else None
        if args.baseline and baseline is None:
            raise ValueError('null baseline')
        errors = validate(candidate, baseline)
    except (OSError, ValueError, RecursionError) as e:
        print(f'validation blocked: {e}', file=sys.stderr)
        return 1
    print(json.dumps({'structural_check': 'fail' if errors else 'pass',
                      'baseline_comparison': 'supplied' if args.baseline else 'not_performed',
                      'approval_verified': False, 'runtime_verified': False,
                      'semantic_review_required': True, 'errors': errors}, ensure_ascii=False, indent=2))
    return 2 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
