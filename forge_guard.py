"""Compare independently supplied record snapshots; never grant authority or approve changes."""
import argparse
import json
from pathlib import Path
import sys

from forge_records import inspect, project_file
from forge_preview import root
from forge_validate import load


def read_project(directory, relative_manifest):
    base = root(directory)
    manifest = load(project_file(base, relative_manifest))
    report, records = inspect(base, manifest, include_records=True)
    return manifest, records, report


def protected(r):
    d = r['data']
    kind = r['type']
    if kind in {'Intent', 'Goal', 'Principle', 'Requirement', 'Constraint', 'Policy'}:
        return d.get('protected') is True or (
            kind == 'Requirement' and d.get('priority') == 'mandatory')
    return kind == 'AcceptanceCriterion' and d.get('mandatory') is True


def compare(before_dir, before_manifest, after_dir, after_manifest):
    old_dir, new_dir = root(before_dir), root(after_dir)
    if old_dir == new_dir or old_dir in new_dir.parents or new_dir in old_dir.parents:
        raise ValueError('separate baseline and candidate trees required')
    old_m, old, old_report = read_project(old_dir, before_manifest)
    new_m, new, new_report = read_project(new_dir, after_manifest)
    if old_m['project_id'] != new_m['project_id']:
        raise ValueError('project identity mismatch')
    old_active = {r['id']: k for k,r in old.items() if r['lifecycle'] == 'active'}
    new_active = {r['id']: k for k,r in new.items() if r['lifecycle'] == 'active'}
    keys = {k for k in old_active.values() if protected(old[k])}
    # A mandatory/protected requirement's pinned criteria must not be silently altered,
    # even if the criterion itself has no mandatory flag.
    for k in list(keys):
        r = old[k]
        if r['type'] in {'Requirement', 'Constraint'}:
            keys.update((ref['id'], ref['revision']) for ref in r['data']['acceptance'])
    changes = []
    for k in sorted(keys):
        prior = old[k]
        current = new.get(k)
        if current != prior:
            changes.append({'id': k[0], 'revision': k[1],
                            'reason': 'protected_record_missing_or_changed'})
        if old_active.get(k[0]) == k and new_active.get(k[0]) != k:
            changes.append({'id': k[0], 'revision': k[1],
                            'reason': 'protected_active_revision_replaced_or_removed'})
    # Permission text is not runtime authority. Report changes to existing role scope
    # and newly added roles for human/authorized review; do not infer set inclusion.
    scope_review = []
    for id in sorted(old_active.keys() | new_active.keys()):
        a = old.get(old_active.get(id))
        b = new.get(new_active.get(id))
        if not any(r and r['type'] == 'Role' for r in (a,b)):
            continue
        fields = ('decision_scope','allowed_operations')
        if (not a or not b or a['type'] != b['type'] or
                any(a['data'].get(f) != b['data'].get(f) for f in fields)):
            scope_review.append(id)
    manifest_review = []
    for field in ('mode', 'policies', 'target_profiles', 'baseline_ref'):
        if old_m[field] != new_m[field]:
            manifest_review.append(field)
    # A pinned policy/environment/baseline can be edited in place without
    # changing the reference. Detect the content change independently.
    for field in ('policies', 'target_profiles'):
        if any(old.get((r['id'],r['revision'])) != new.get((r['id'],r['revision']))
               for r in old_m[field]) and field not in manifest_review:
            manifest_review.append(field)
    b = old_m['baseline_ref']
    if old.get((b['id'],b['revision'])) != new.get((b['id'],b['revision'])) and 'baseline_ref' not in manifest_review:
        manifest_review.append('baseline_ref')
    # Preserve the meaning of previously pinned records and historical evidence.
    # Lifecycle-only changes to nonprotected records can be legitimate retirement.
    prior_baseline = old[(b['id'], b['revision'])]
    pinned_review = []
    for r in prior_baseline['data']['composition']:
        k = (r['id'], r['revision'])
        if old[k] != new.get(k):
            pinned_review.append(dict(id=k[0],revision=k[1]))
    history_review = []
    for k, r in sorted(old.items()):
        if r['lifecycle'] == 'active' and r['type'] not in {'Evidence','Finding','Change','Decision','Release','Incident','Baseline'}:
            continue
        n = new.get(k)
        if n is None or ({x:v for x,v in r.items() if x != 'lifecycle'} !=
                         {x:v for x,v in n.items() if x != 'lifecycle'}):
            history_review.append(dict(id=k[0],revision=k[1],reason='removed_or_rewritten'))
        elif r['lifecycle'] != 'active' and n['lifecycle'] == 'active':
            history_review.append(dict(id=k[0],revision=k[1],reason='historical_revision_reactivated'))
    # Extensions can evolve by adding versions. Redefining/removing an
    # already registered version requires review.
    old_ext = {(r['type_id'],r['version']):r for r in old_m['extension_registry']}
    new_ext = {(r['type_id'],r['version']):r for r in new_m['extension_registry']}
    extension_review = [dict(type_id=k[0],version=k[1]) for k in sorted(old_ext)
                        if old_ext[k] != new_ext.get(k)]
    unknown = {'baseline': old_report['extension_payloads_unverified'],
               'candidate': new_report['extension_payloads_unverified']}
    return {'project_id': old_m['project_id'], 'protected_records_compared': len(keys),
            'protected_changes': changes, 'role_scope_review': scope_review,
            'manifest_review': manifest_review, 'extension_registry_review': extension_review,
            'pinned_record_review': pinned_review, 'history_review': history_review,
            'unverified_extensions': unknown,
            'review_required': bool(changes or scope_review or manifest_review or extension_review or pinned_review or history_review or any(unknown.values())),
            'baseline_authenticity_verified': False, 'approval_verified': False,
            'authority_verified': False, 'semantic_review_required': True,
            'files_modified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline_directory')
    p.add_argument('baseline_manifest')
    p.add_argument('candidate_directory')
    p.add_argument('candidate_manifest')
    a = p.parse_args()
    try:
        result = compare(a.baseline_directory, a.baseline_manifest,
                         a.candidate_directory, a.candidate_manifest)
    except Exception as e:
        print(f'guard blocked: {type(e).__name__}: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if result['review_required'] else 0


if __name__ == '__main__':
    sys.exit(main())
