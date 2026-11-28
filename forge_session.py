"""Derive project-local work candidates and contracts from canonical records. Read-only."""
import argparse
import json
import sys

from forge_guard import read_project
from forge_integrate import clean_head
from forge_preview import root
from forge_progress import topological


def ref(r):
    return {'id': r['id'], 'revision': r['revision']}


def pair(r):
    return (r['id'], r['revision'])


def session(directory, manifest_path, *, observe_git=False):
    base = root(directory)
    head = clean_head(base) if observe_git else None
    manifest, records, observation = read_project(base, manifest_path)
    active = {r['id']: r for r in records.values() if r['lifecycle'] == 'active'}
    baseline = records[pair(manifest['baseline_ref'])]
    tasks = {k: r for k,r in active.items() if r['type'] == 'Task'}
    baseline_issues = []
    if baseline['lifecycle'] != 'active':
        baseline_issues.append('baseline_not_active')
    if baseline['data']['source_commit'] is None:
        baseline_issues.append('baseline_source_revision_unconfirmed')
    elif head is not None and baseline['data']['source_commit'] != head:
        baseline_issues.append('baseline_source_differs_from_observed_head')
    # A baseline may describe requirements rather than the entire working tree.
    # Never infer that the snapshot or its authority is authenticated.
    unknown = {pair(r) for r in observation['extension_payloads_unverified']}
    evidence_reports = {pair(r): r for r in observation['evidence']}
    active_tests = [r for r in active.values() if r['type'] == 'Test']
    active_evidence = [r for r in active.values() if r['type'] == 'Evidence']

    def criterion_report(criterion):
        cid = pair(criterion)
        tests = [t for t in active_tests if cid in
                 {pair(c) for c in t['data']['criteria']}]
        outcomes = []
        for t in sorted(tests, key=pair):
            candidates = [e for e in active_evidence
                          if pair(e['data']['test']) == pair(t)
                          and pair(e['data']['baseline']) == pair(baseline)]
            # Multiple current observations cannot be cherry-picked; conflicting
            # or incomplete reports require review, not a vote or latest-pass rule.
            reports = [evidence_reports[pair(e)] for e in candidates]
            environment = records[pair(t['data']['environment'])]
            good = (bool(reports) and not any(e['review_required'] for e in reports)
                    and environment['lifecycle'] == 'active')
            outcomes.append({'test': ref(t), 'evidence': [ref(e) for e in candidates],
                             'assessment': 'reported_pass' if good else 'review_required'})
        ok = (criterion['lifecycle'] == 'active' and bool(outcomes)
              and all(t['assessment'] == 'reported_pass' for t in outcomes))
        return {'criterion': ref(criterion), 'expected': criterion['data']['expected'],
                'conditions': criterion['data']['conditions'], 'tests': outcomes,
                'assessment': 'reported_pass' if ok else 'review_required'}

    task_links, other_deps = {}, {}
    for id, task in tasks.items():
        task_links[id], other_deps[id] = [], []
        for link in task['relations']:
            if link['kind'] != 'depends_on':
                continue
            target = (records[(link['target_id'], link['target_revision'])]
                      if 'target_revision' in link else active[link['target_id']])
            if target['type'] == 'Task' and target['lifecycle'] == 'active':
                task_links[id].append(target['id'])
            else:
                other_deps[id].append(ref(target))
        task_links[id] = sorted(set(task_links[id]))
    order = topological(task_links, 'active task dependency')
    results = {}
    for id in order:
        task = tasks[id]
        data = task['data']
        role = active[task['owner_role']]
        permitted = sorted(set(data['allowed_operations']) & set(role['data']['allowed_operations']))
        outside = sorted(set(data['allowed_operations']) - set(permitted))
        checks = [criterion_report(records[pair(c)]) for c in data['acceptance']]
        waits = [d for d in task_links[id] if results[d]['assessment'] != 'recorded_done']
        holds = list(baseline_issues)
        if data['baseline'] != ref(baseline):
            holds.append('task_baseline_differs')
        if outside:
            holds.append('task_operations_outside_role_declaration')
        if not checks:
            holds.append('no_completion_criteria')
        if other_deps[id]:
            holds.append('nonactive_or_nontask_dependency_requires_review')
        if any((link['target_id'], link.get('target_revision',
                    active.get(link['target_id'], {}).get('revision'))) in unknown
               for link in task['relations']):
            holds.append('referenced_extension_unverified')
        if waits:
            holds.append('task_dependency_not_recorded_done')
        if data['blocked_reason']:
            holds.append('recorded_blocked_reason')
        state = data['state']
        if state == 'done':
            assessment = ('recorded_done' if not holds and
                          all(c['assessment'] == 'reported_pass' for c in checks)
                          else 'review_required')
        elif state in {'blocked', 'paused', 'cancelled'}:
            assessment = state
        elif holds:
            assessment = 'review_required'
        elif state in {'proposed', 'ready', 'rework', 'reopened'}:
            assessment = 'candidate_for_work'
        else:
            assessment = state
        requirements = []
        for link in task['relations']:
            if link['kind'] in {'implements','satisfies','derives_from','governed_by'}:
                target = (records[(link['target_id'], link['target_revision'])]
                          if 'target_revision' in link else active[link['target_id']])
                requirements.append({'kind': link['kind'], 'record': ref(target),
                                     'title': target['title']})
        results[id] = {'task': ref(task), 'declared_state': state, 'assessment': assessment,
                       'holds': holds, 'waiting_for': waits,
                       'other_dependencies': other_deps[id],
                       'contract': {'purpose': task['title'], 'scope': data['scope'],
                                    'excluded': data['excluded'], 'baseline': data['baseline'],
                                    'owner_role': ref(role), 'role_mission': role['data']['mission'],
                                    'role_responsibilities': role['data']['responsibilities'],
                                    'decision_scope_declared': role['data']['decision_scope'],
                                    'operations_declared_in_both': permitted,
                                    'operations_outside_role': outside,
                                    'input_contract': role['data']['input_contract'],
                                    'output_contract': role['data']['output_contract'],
                                    'role_verification': role['data']['verification'],
                                    'escalation': role['data']['escalation'],
                                    'budget': data['budget'],
                                    'stop_conditions': list(dict.fromkeys(
                                        data['stop_conditions'] + role['data']['stop_conditions'])),
                                    'task_authority_label': task['authority'],
                                    'role_authority_label': role['authority'],
                                    'linked_records': requirements, 'completion_checks': checks,
                                    'operation_authority_verified': False}}
    if observe_git and clean_head(base) != head:
        raise ValueError('target HEAD changed during inspection')
    return {'project_id': manifest['project_id'], 'baseline': ref(baseline),
            'observed_head': head, 'baseline_issues': baseline_issues,
            'tasks': list(results.values()),
            'next_candidates': [id for id,t in results.items()
                                if t['assessment'] == 'candidate_for_work'],
            'review_required': [id for id,t in results.items()
                                if t['assessment'] == 'review_required'],
            'unknown_extensions': observation['extension_payloads_unverified'],
            'baseline_authenticity_verified': False,
            'evidence_authenticity_verified': False, 'authority_verified': False,
            'semantic_review_required': True, 'executed': False, 'files_modified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory')
    p.add_argument('manifest')
    p.add_argument('--observe-git', action='store_true',
                   help='observe clean target HEAD, not proof of baseline authenticity')
    a = p.parse_args()
    try:
        result = session(a.directory, a.manifest, observe_git=a.observe_git)
    except Exception as e:
        print(f'session inspection blocked: {type(e).__name__}: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if (result['review_required'] or result['baseline_issues']
                 or result['unknown_extensions']) else 0


if __name__ == '__main__':
    sys.exit(main())
