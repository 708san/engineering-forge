"""Compare declared observations for a project-specific improvement trial; never adopt it."""
import argparse
import hashlib
import json
import math
import sys

from forge_validate import load
from forge_guard import compare


def nonempty(v):
    return isinstance(v,str) and bool(v.strip())


def number(v):
    return type(v) in (int,float) and math.isfinite(v)


def digest(doc):
    return hashlib.sha256(json.dumps(doc,sort_keys=True,ensure_ascii=False,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()


def assess(plan, observations, *, expected_plan_digest):
    if digest(plan) != expected_plan_digest:
        raise ValueError('trial plan differs from separately supplied fingerprint')
    if (not isinstance(plan,dict) or set(plan) != {'project_id','hypothesis','scope',
          'baseline_revision','candidate_revision','rollback','stop_conditions','metrics'}
          or not all(nonempty(plan[k]) for k in ('project_id','hypothesis','scope',
                   'baseline_revision','candidate_revision','rollback','stop_conditions'))
          or plan['baseline_revision']==plan['candidate_revision']
          or not isinstance(plan['metrics'],list) or not plan['metrics']):
        raise ValueError('invalid trial plan')
    metrics={}
    for m in plan['metrics']:
        if (not isinstance(m,dict) or set(m)!={'id','unit','procedure','direction','max_regression','min_improvement','required'}
                or not all(nonempty(m[k]) for k in ('id','unit','procedure'))
                or m['direction'] not in ('higher','lower')
                or not all(number(m[k]) and m[k]>=0 for k in ('max_regression','min_improvement'))
                or type(m['required']) is not bool or m['id'] in metrics):
            raise ValueError('invalid or duplicate metric')
        metrics[m['id']]=m
    if not any(m['required'] for m in metrics.values()):
        raise ValueError('at least one required metric')
    if (not isinstance(observations,dict) or set(observations)!={'project_id','plan_sha256','baseline_revision','candidate_revision','measurements','stop_observations'}
            or any(observations[k]!=plan[k] for k in ('project_id','baseline_revision','candidate_revision'))
            or observations['plan_sha256']!=expected_plan_digest
            or not isinstance(observations['measurements'],list)
            or not isinstance(observations['stop_observations'],list)
            or not all(nonempty(x) for x in observations['stop_observations'])):
        raise ValueError('trial observation identity mismatch or invalid envelope')
    observed={}
    for o in observations['measurements']:
        if (not isinstance(o,dict) or set(o)!={'id','baseline','candidate','baseline_ref','candidate_ref'}
                or not nonempty(o['id']) or o['id'] not in metrics or o['id'] in observed
                or not all(o[k] is None or number(o[k]) for k in ('baseline','candidate'))
                or not all(o[k] is None or nonempty(o[k]) for k in ('baseline_ref','candidate_ref'))):
            raise ValueError('invalid or duplicate measurement')
        observed[o['id']]=o
    rows=[]
    for id,m in metrics.items():
        o=observed.get(id)
        if not o or any(o[k] is None for k in ('baseline','candidate','baseline_ref','candidate_ref')):
            result='unmeasured'
            improvement=None
        else:
            improvement=(o['candidate']-o['baseline'])*(1 if m['direction']=='higher' else -1)
            if not number(improvement):
                raise ValueError('non-finite improvement')
            if improvement < -m['max_regression']:
                result='regression'
            elif improvement > 0 and improvement >= m['min_improvement']:
                result='improved'
            else:
                result='within_tolerance'
        rows.append(dict(id=id,unit=m['unit'],required=m['required'],improvement=improvement,result=result,
                         baseline=o['baseline'] if o else None, candidate=o['candidate'] if o else None,
                         baseline_ref=o['baseline_ref'] if o else None, candidate_ref=o['candidate_ref'] if o else None))
    if observations['stop_observations'] or any(r['result']=='regression' for r in rows):
        assessment='stop_or_rework'
    elif any(r['required'] and r['result']=='unmeasured' for r in rows):
        assessment='insufficient_evidence'
    elif any(r['result']=='improved' for r in rows):
        assessment='candidate_for_review'
    else:
        assessment='no_demonstrated_improvement'
    return dict(project_id=plan['project_id'],plan_sha256=expected_plan_digest,
                metrics=rows,assessment=assessment,stop_observations=observations['stop_observations'],
                plan_authenticity_verified=False,measurements_verified=False,
                protected_conditions_verified=False,adopted=False,authority_verified=False)


def review(plan, observations, expected_plan_digest, baseline_dir, baseline_manifest,
           candidate_dir,candidate_manifest):
    report=assess(plan,observations,expected_plan_digest=expected_plan_digest)
    guard=compare(baseline_dir,baseline_manifest,candidate_dir,candidate_manifest)
    if guard['project_id']!=report['project_id']:
        raise ValueError('trial and record project mismatch')
    report['record_guard']=guard
    report['metric_assessment']=report['assessment']
    report['record_review_required']=guard['review_required']
    if guard['review_required'] and report['assessment'] != 'stop_or_rework':
        report['assessment']='protected_or_governance_review_required'
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan')
    p.add_argument('observations',nargs='?')
    p.add_argument('--expect')
    p.add_argument('--records',nargs=4,metavar=('OLD_DIR','OLD_MANIFEST','NEW_DIR','NEW_MANIFEST'))
    a=p.parse_args()
    try:
        plan=load(a.plan)
        if a.observations is None:
            if a.expect or a.records:
                raise ValueError('fingerprint mode does not take comparison options')
            result={'plan_sha256':digest(plan),'plan_authenticity_verified':False}
        else:
            if not a.expect:
                raise ValueError('separately retained plan fingerprint required')
            obs=load(a.observations)
            result=(review(plan,obs,a.expect,*a.records) if a.records else
                    assess(plan,obs,expected_plan_digest=a.expect))
    except Exception as e:
        print(f'trial blocked: {type(e).__name__}: {e}',file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('assessment','candidate_for_review')=='candidate_for_review' else 2


if __name__=='__main__':
    sys.exit(main())
