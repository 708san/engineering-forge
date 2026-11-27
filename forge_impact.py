"""Report potentially affected records through declared dependency links; never approve changes."""
import argparse
import json
import sys

from forge_handoff import load
from forge_integrate import path_parts


def impact(directory, manifest, graph, changed_ids=()):
    # The manifest is a previous observation, not an approval or full tree inventory.
    from forge_handoff import verify
    observation = verify(directory, manifest)
    if not isinstance(graph, dict) or set(graph) != {'records'} or not isinstance(graph['records'], list):
        raise ValueError('expected graph.records array')
    records = {}
    for r in graph['records']:
        if (not isinstance(r, dict) or set(r) != {'id', 'kind', 'files', 'depends_on'}
                or not all(isinstance(r[k], str) and r[k].strip() for k in ('id', 'kind'))
                or not all(isinstance(r[k], list) and all(isinstance(x, str) and x.strip() for x in r[k])
                           for k in ('files', 'depends_on'))):
            raise ValueError('invalid record')
        if r['id'] in records:
            raise ValueError('duplicate record ID')
        for path in r['files']:
            path_parts(path)
        records[r['id']] = r
    for r in records.values():
        if set(r['depends_on']) - records.keys():
            raise ValueError('dangling dependency: ' + r['id'])
    if set(changed_ids) - records.keys():
        raise ValueError('unknown changed record')
    watched = set(manifest['sha256'])
    changed = set(observation['changed'])
    mapped = {f for r in records.values() for f in r['files']}
    direct = set(changed_ids) | {i for i,r in records.items() if changed.intersection(r['files'])}
    affected = set(direct)
    while True:
        more = {i for i,r in records.items() if affected.intersection(r['depends_on'])}
        if more <= affected:
            break
        affected |= more
    return {'changed_files': sorted(changed), 'direct': sorted(direct),
            'affected': [{'id': i, 'kind': records[i]['kind'], 'status': 'review_required'}
                         for i in sorted(affected)],
            'unmapped_changes': sorted(changed-mapped), 'unwatched_dependencies': sorted(mapped-watched),
            'coverage_complete': False, 'semantic_review_required': True,
            'approval_verified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory')
    p.add_argument('manifest')
    p.add_argument('graph')
    p.add_argument('--changed-id', action='append', default=[])
    args = p.parse_args()
    try:
        result = impact(args.directory, load(args.manifest), load(args.graph), args.changed_id)
    except (OSError, ValueError, RecursionError) as e:
        print(f'impact blocked: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if any(result[k] for k in ('affected','unmapped_changes','unwatched_dependencies')) else 0


if __name__ == '__main__':
    sys.exit(main())
