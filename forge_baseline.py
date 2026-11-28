"""Compute a deterministic fingerprint for the declared, pinned record composition."""
import argparse
import hashlib
import json
import sys

from forge_guard import read_project


def fingerprint(records, baseline):
    own = (baseline['id'], baseline['revision'])
    ids = [(r['id'], r['revision']) for r in baseline['data']['composition']]
    if not ids or len(set(ids)) != len(ids) or own in ids:
        raise ValueError('baseline composition must be nonempty, unique, and not self-referential')
    if any(k not in records for k in ids):
        raise ValueError('baseline composition reference missing')
    # Versioned Python JSON encoding, not a cross-language RFC 8785 promise.
    payload = {'encoding': 'forge-record-composition-v1',
               'records': [records[k] for k in sorted(ids)]}
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def inspect_baseline(directory, manifest_path):
    m, records, report = read_project(directory, manifest_path)
    b = records[(m['baseline_ref']['id'],m['baseline_ref']['revision'])]
    computed = fingerprint(records,b)
    return {'project_id':m['project_id'], 'baseline':m['baseline_ref'],
            'declared_sha256':b['data']['snapshot_sha256'], 'computed_sha256':computed,
            'composition_matches':computed == b['data']['snapshot_sha256'],
            'record_count':len(b['data']['composition']),
            'source_commit_declared':b['data']['source_commit'],
            'source_commit_verified':False, 'authority_verified':False,
            'snapshot_authenticity_verified':False, 'files_modified':False,
            'unknown_extensions':report['extension_payloads_unverified']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory')
    p.add_argument('manifest')
    a=p.parse_args()
    try:
        result=inspect_baseline(a.directory,a.manifest)
    except Exception as e:
        print(f'baseline inspection blocked: {type(e).__name__}: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['composition_matches'] and not result['unknown_extensions'] else 2


if __name__ == '__main__':
    sys.exit(main())
