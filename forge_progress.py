"""Inspect task dependencies and revision-bound evidence; do not mutate tasks or approve work."""
import argparse
import json
import sys
from collections import deque

from forge_validate import load
from forge_integrate import clean_head
from forge_preview import root

STATES = {'proposed', 'ready', 'running', 'verifying', 'done', 'blocked',
          'paused', 'rework', 'cancelled', 'reopened'}
VERDICTS = {'pass', 'fail', 'blocked', 'not_run'}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return (isinstance(value, list) and all(text(v) for v in value)
            and len(value) == len(set(value)))


def topological(links, name):
    remaining = {k: len(v) for k, v in links.items()}
    followers = {k: [] for k in links}
    for k, deps in links.items():
        for dep in deps:
            if dep not in links:
                raise ValueError(f'unknown {name} reference: {k} -> {dep}')
            followers[dep].append(k)
    queue = deque(sorted(k for k, n in remaining.items() if not n))
    order = []
    while queue:
        k = queue.popleft()
        order.append(k)
        for follower in sorted(followers[k]):
            remaining[follower] -= 1
            if not remaining[follower]:
                queue.append(follower)
    if len(order) != len(links):
        raise ValueError(f'{name} cycle')
    return order


def inspect(ledger, revision, *, revision_observed=False):
    if not text(revision):
        raise ValueError('current revision required')
    if (not isinstance(ledger, dict) or set(ledger) != {'project', 'tasks', 'evidence'}
            or not text(ledger['project']) or not isinstance(ledger['tasks'], list)
            or not isinstance(ledger['evidence'], list)):
        raise ValueError('invalid ledger')
    tasks = {}
    for t in ledger['tasks']:
        if (not isinstance(t, dict)
                or set(t) != {'id', 'purpose', 'state', 'parent', 'depends_on', 'checks', 'owner'}
                or not all(text(t[k]) for k in ('id', 'purpose', 'owner', 'state'))
                or t['state'] not in STATES
                or (t['parent'] is not None and not text(t['parent']))
                or not strings(t['depends_on']) or not strings(t['checks']) or not t['checks']):
            raise ValueError('invalid task; at least one completion check is required')
        if t['id'] in tasks:
            raise ValueError('duplicate task ID')
        tasks[t['id']] = t
    topological({k: [t['parent']] if t['parent'] is not None else []
                 for k, t in tasks.items()}, 'parent')
    order = topological({k: t['depends_on'] for k, t in tasks.items()}, 'dependency')
    observations = {}
    for e in ledger['evidence']:
        if (not isinstance(e, dict) or set(e) != {'task_id', 'check', 'revision', 'verdict',
                                                 'environment', 'procedure', 'reference'}
                or not all(text(v) for v in e.values()) or e['verdict'] not in VERDICTS):
            raise ValueError('invalid evidence')
        if e['task_id'] not in tasks or e['check'] not in tasks[e['task_id']]['checks']:
            raise ValueError('evidence references an unknown task or check')
        key = e['task_id'], e['check'], e['revision']
        if key in observations:
            raise ValueError('ambiguous duplicate observation for task/check/revision')
        observations[key] = e
    result = {}
    for k in order:
        t = tasks[k]
        checks = {}
        for check in t['checks']:
            e = observations.get((k, check, revision))
            if e:
                checks[check] = 'reported_' + e['verdict']
            elif any(oid == k and c == check for oid, c, _ in observations):
                checks[check] = 'other_revision_only'
            else:
                checks[check] = 'not_recorded'
        waiting = [d for d in t['depends_on'] if result[d]['assessment'] != 'recorded_done']
        state = t['state']
        if state == 'done':
            assessment = ('recorded_done' if not waiting and
                          all(v == 'reported_pass' for v in checks.values()) else 'review_required')
        elif state in {'blocked', 'paused', 'cancelled'}:
            assessment = state
        elif waiting:
            assessment = 'waiting_for_dependency'
        elif state in {'proposed', 'ready', 'rework', 'reopened'}:
            assessment = 'candidate_for_work'
        else:
            assessment = state
        result[k] = dict(id=k, parent=t['parent'], declared_state=state,
                         assessment=assessment, waiting_for=waiting, checks=checks)
    return dict(project=ledger['project'], revision=revision,
                revision_observed=revision_observed, evidence_authenticity_verified=False,
                authority_verified=False, semantic_review_required=True,
                tasks=list(result.values()),
                next_candidates=[k for k, r in result.items() if r['assessment']=='candidate_for_work'],
                review_required=[k for k, r in result.items() if r['assessment']=='review_required'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ledger')
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--target', help='clean local Git worktree at the revision under review')
    group.add_argument('--revision', help='externally supplied revision; not verified')
    a = p.parse_args()
    try:
        revision = clean_head(root(a.target)) if a.target else a.revision
        report = inspect(load(a.ledger), revision, revision_observed=bool(a.target))
    except (OSError, ValueError, RecursionError) as e:
        print(f'progress blocked: {e}', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 2 if report['review_required'] else 0


if __name__ == '__main__':
    sys.exit(main())
