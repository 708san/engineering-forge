"""Inspect project records and local declarative extensions. Never infer approval or execute payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
from forge_preview import root, key
from forge_handoff import local_file
from forge_validate import load
from forge_progress import topological

SCHEMAS = Path(__file__).resolve().parent / 'schemas'
DRAFT = 'https://json-schema.org/draft/2020-12/schema'
# Deliberately limited, self-contained JSON Schema vocabulary. No external retrieval,
# custom keywords, executable code, or reference resolution, even within the schema.
SCALAR = {'$schema', 'title', 'description', 'type', 'enum', 'const', 'required',
          'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf',
          'minLength', 'maxLength', 'pattern', 'minItems', 'maxItems', 'uniqueItems',
          'minProperties', 'maxProperties', 'minContains', 'maxContains'}
SINGLE = {'items', 'additionalProperties', 'contains', 'not', 'if', 'then', 'else',
          'propertyNames'}
MAP = {'properties', 'patternProperties'}
ARRAY = {'allOf', 'anyOf', 'oneOf', 'prefixItems'}


def safe_schema(s, *, top=True):
    if isinstance(s, bool):
        return
    if not isinstance(s, dict):
        raise ValueError('invalid extension schema node')
    if set(s) - SCALAR - SINGLE - MAP - ARRAY:
        raise ValueError('unsupported extension schema keyword: ' +
                         ', '.join(sorted(set(s) - SCALAR - SINGLE - MAP - ARRAY)))
    if '$schema' in s and (not top or s['$schema'] != DRAFT):
        raise ValueError('only the local Draft 2020-12 dialect is supported')
    for k in SINGLE & s.keys():
        safe_schema(s[k], top=False)
    for k in MAP & s.keys():
        if not isinstance(s[k], dict):
            raise ValueError('invalid schema map')
        for child in s[k].values():
            safe_schema(child, top=False)
    for k in ARRAY & s.keys():
        if not isinstance(s[k], list):
            raise ValueError('invalid schema list')
        for child in s[k]:
            safe_schema(child, top=False)


def checked(validator, value, label):
    errors = sorted(f'{label} {list(e.absolute_path)}: {e.message}'
                    for e in validator.iter_errors(value))
    if errors:
        raise ValueError('; '.join(errors))


def project_file(base, name):
    p = local_file(base, name)
    if not p.is_file():
        raise ValueError('not a regular project file: ' + name)
    return p


def file_hash(base, ref):
    if hashlib.sha256(project_file(base, ref['path']).read_bytes()).hexdigest() != ref['sha256']:
        raise ValueError('body content digest mismatch: ' + ref['path'])


def extension_validators(base, manifest):
    result = {}
    for entry in manifest['extension_registry']:
        ref = (entry['type_id'], entry['version'])
        if ref in result:
            raise ValueError('duplicate extension registration: ' + str(ref))
        path = project_file(base, entry['schema_path'])
        # Read the same bytes that are validated and hashed.
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('extension schema digest mismatch: ' + entry['schema_path'])
        def unique(pairs):
            result = {}
            for k, v in pairs:
                if k in result:
                    raise ValueError('duplicate schema key: ' + k)
                result[k] = v
            return result
        def invalid(v):
            raise ValueError('non-finite schema value: ' + v)
        doc = json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=invalid)
        safe_schema(doc)
        Draft202012Validator.check_schema(doc)
        result[ref] = Draft202012Validator(doc)
    return result


# Only inspect typed references defined by the migrated core format. Never interpret
# arbitrary extension payload keys as authority, dependencies, or executable actions.
DATA_REFS = {
    'Requirement': {'acceptance': 'AcceptanceCriterion'},
    'UseCase': {'acceptance': 'AcceptanceCriterion'},
    'Constraint': {'acceptance': 'AcceptanceCriterion'},
    'Task': {'acceptance': 'AcceptanceCriterion', 'baseline': 'Baseline'},
    'Milestone': {'acceptance': 'AcceptanceCriterion'},
    'Change': {'baseline': 'Baseline', 'targets': None},
    'Role': {'knowledge_refs': None},
    'Agent': {'roles': 'Role', 'environment': 'Environment'},
    'Test': {'criteria': 'AcceptanceCriterion', 'environment': 'Environment'},
    'Evidence': {'test': 'Test', 'baseline': 'Baseline', 'environment': 'Environment'},
    'Finding': {'target': None},
    'Baseline': {'composition': None},
    'Release': {'baseline': 'Baseline', 'evidence': 'Evidence'},
}


def inspect(directory, manifest, *, include_records=False):
    base = root(directory)
    checked(Draft202012Validator(load(SCHEMAS / 'project.schema.json')), manifest, 'project')
    rv = Draft202012Validator(load(SCHEMAS / 'record.schema.json'))
    extensions = extension_validators(base, manifest)
    records, active = {}, {}
    sources = set()
    for source in manifest['record_sources']:
        name = source['path']
        if key(name) in sources:
            raise ValueError('duplicate record source: ' + name)
        sources.add(key(name))
        doc = load(project_file(base, name))
        if not isinstance(doc, list):
            raise ValueError('record source must be an array: ' + name)
        for record in doc:
            checked(rv, record, 'record in ' + name)
            rid = (record['id'], record['revision'])
            if rid in records:
                raise ValueError('duplicate record revision: ' + str(rid))
            records[rid] = record
            if record['lifecycle'] == 'active':
                if record['id'] in active:
                    raise ValueError('multiple active revisions: ' + record['id'])
                active[record['id']] = rid
            if 'body_ref' in record:
                file_hash(base, record['body_ref'])

    def resolve(id, revision=None, expected=None):
        rid = active.get(id) if revision is None else (id, revision)
        if rid not in records:
            raise ValueError('unresolved record reference: ' + str((id, revision)))
        if expected and records[rid]['type'] != expected:
            raise ValueError('wrong record type for reference: ' + str(rid))
        return rid

    def resolve_ref(ref, expected=None):
        return resolve(ref['id'], ref['revision'], expected)

    for source in manifest['record_sources']:
        resolve(source['owner_role'], expected='Role')
    baseline = resolve_ref(manifest['baseline_ref'], 'Baseline')
    for field, expected in [('policies', 'Policy'), ('target_profiles', 'Environment')]:
        for ref in manifest[field]:
            resolve_ref(ref, expected)
    graph = {rid: [] for rid in records}
    hierarchy = {rid: [] for rid in records}
    unknown, validated, evidence, practices = [], [], [], []
    for rid, r in records.items():
        resolve(r['owner_role'], expected='Role')
        if 'change_ref' in r:
            resolve_ref(r['change_ref'], 'Change')
        for rel in r['relations']:
            target = resolve(rel['target_id'], rel.get('target_revision'))
            if rel['kind'] == 'depends_on':
                graph[rid].append(target)
            if rel['kind'] == 'parent_of':
                hierarchy[rid].append(target)
        kind = r['type']
        d = r['data']
        for field, expected in DATA_REFS.get(kind, {}).items():
            refs = d[field] if isinstance(d[field], list) else [d[field]]
            for ref in refs:
                resolve_ref(ref, expected)
        if kind.startswith('x.'):
            ref = r['extension_schema_ref']
            if ref['type_id'] != kind:
                raise ValueError('extension type mismatch: ' + r['id'])
            validator = extensions.get((kind, ref['version']))
            item = dict(id=r['id'], revision=r['revision'], type=kind, version=ref['version'])
            if validator is None:
                unknown.append(item)
            else:
                checked(validator, d, 'extension ' + r['id'])
                validated.append(item)
        if kind == 'Practice':
            practices.append(dict(id=r['id'], revision=r['revision'],
                                  definition_ref=d['definition_ref']))
        if kind == 'Evidence':
            observed_baseline = resolve_ref(d['baseline'], 'Baseline')
            test = records[resolve_ref(d['test'], 'Test')]
            review = (observed_baseline != baseline or d['validity'] != 'current'
                      or d['environment'] != test['data']['environment']
                      or d['result'] != 'pass' or d['artifact_sha256'] is None)
            evidence.append(dict(id=r['id'], revision=r['revision'],
                                 reported_result=d['result'], review_required=review,
                                 authenticity_verified=False))
    # Separate parent/child hierarchy from hard execution dependencies.
    topological({k: sorted(set(v)) for k,v in graph.items()}, 'dependency')
    topological({k: sorted(set(v)) for k,v in hierarchy.items()}, 'hierarchy')
    report = dict(project_id=manifest['project_id'], record_count=len(records),
                structure='pass', extension_payloads_validated=validated,
                extension_payloads_unverified=unknown, evidence=evidence,
                practice_definition_refs_unverified=practices,
                body_anchors_verified=False, baseline_snapshot_verified=False,
                managed_outputs_verified=False, authority_verified=False,
                semantic_review_required=True, enforcement_verified=False,
                files_modified=False)
    return (report, records) if include_records else report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory')
    p.add_argument('manifest', help='project manifest path relative to directory')
    args = p.parse_args()
    try:
        base = root(args.directory)
        result = inspect(base, load(project_file(base, args.manifest)))
    except (OSError, ValueError, RecursionError) as e:
        print(f'record inspection blocked: {e}', file=sys.stderr)
        return 1
    except Exception as e:
        # Invalid schemas/regex and other inspection failures must not become a pass.
        print(f'record inspection failed: {type(e).__name__}: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result['extension_payloads_unverified'] else 0


if __name__ == '__main__':
    sys.exit(main())
