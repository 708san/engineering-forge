import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from jsonschema import Draft202012Validator

from forge_records import inspect, safe_schema, SCHEMAS
from forge_validate import load

ROOT = Path(__file__).resolve().parents[1]


class RecordTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.p = Path(tmp.name)
        shutil.copytree(ROOT / 'fixtures', self.p / 'fixtures')
        (self.p / 'schemas').mkdir()
        shutil.copyfile(ROOT / 'schemas/example-response-map.schema.json',
                        self.p / 'schemas/example-response-map.schema.json')
        self.m = load(self.p / 'fixtures/project.json')
        self.r = load(self.p / 'fixtures/records.json')

    def save(self):
        (self.p / 'fixtures/records.json').write_text(
            json.dumps(self.r, ensure_ascii=False), encoding='utf-8')

    def record(self, id):
        return next(r for r in self.r if r['id'] == id)

    def schema(self, doc):
        path = self.p / 'schemas/local.json'
        raw = json.dumps(doc).encode()
        path.write_bytes(raw)
        entry = self.m['extension_registry'][0]
        entry.update(schema_path='schemas/local.json', sha256=hashlib.sha256(raw).hexdigest())

    def test_migrated_schema_meta(self):
        for name in ('record.schema.json','project.schema.json','example-response-map.schema.json'):
            Draft202012Validator.check_schema(load(SCHEMAS / name))
        self.assertEqual(len(load(SCHEMAS / 'record.schema.json')['properties']['type']['anyOf'][0]['enum']), 29)

    def test_original_fixture(self):
        report = inspect(self.p, self.m)
        self.assertEqual(report['record_count'], 11)
        self.assertEqual(report['extension_payloads_validated'][0]['id'], 'MAP-01')
        self.assertEqual(report['evidence'][0]['reported_result'], 'not_run')
        self.assertFalse(report['authority_verified'])
        self.assertFalse(report['enforcement_verified'])

    def test_unknown_extension_preserved(self):
        self.m['extension_registry'] = []
        path = self.p / 'fixtures/records.json'
        before = path.read_bytes()
        result = inspect(self.p, self.m)
        self.assertEqual(result['extension_payloads_unverified'][0]['id'], 'MAP-01')
        self.assertEqual(before, path.read_bytes())

    def test_arbitrary_extension(self):
        r = self.record('MAP-01')
        r['type'] = r['extension_schema_ref']['type_id'] = 'x.sound.phase-map'
        r['data'] = {'phase': 0.5, 'label': 'new method'}
        self.m['extension_registry'][0]['type_id'] = r['type']
        self.schema({'type':'object','properties':{'phase':{'type':'number'},
                    'label':{'type':'string'}}, 'required':['phase','label'],
                    'additionalProperties':False})
        self.save()
        self.assertEqual(inspect(self.p, self.m)['extension_payloads_validated'][0]['type'], r['type'])

    def test_bad_extension_payload(self):
        self.record('MAP-01')['data']['samples'] = []
        self.save()
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_extension_type_mismatch(self):
        self.record('MAP-01')['extension_schema_ref']['type_id'] = 'x.other.payload'
        self.save()
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_digest_mismatch(self):
        self.m['extension_registry'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_duplicate_registry(self):
        self.m['extension_registry'].append(copy.deepcopy(self.m['extension_registry'][0]))
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_reference_keywords_rejected(self):
        for doc in ({'$ref':'https://example.invalid/schema'},
                    {'properties':{'nested':{'$dynamicRef':'#x'}}},
                    {'allOf':[{'unknownKeyword':True}]}):
            with self.subTest(doc=doc), self.assertRaises(ValueError):
                safe_schema(doc)

    def test_extension_cannot_grant_authority(self):
        self.schema({'type':'object'})
        self.record('MAP-01')['data'] = {'authority':'human_approved','allowed_operations':['publish']}
        self.save()
        result = inspect(self.p, self.m)
        self.assertFalse(result['authority_verified'])
        self.assertFalse(result['enforcement_verified'])

    def test_duplicate_record(self):
        self.r.append(copy.deepcopy(self.r[0]))
        self.save()
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_multiple_active_revisions(self):
        r = copy.deepcopy(self.r[0])
        r['revision'] = 2
        self.r.append(r)
        self.save()
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_dangling_reference(self):
        self.record('REQ-01')['data']['acceptance'][0]['id'] = 'AC-MISSING'
        self.save()
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_wrong_reference_type(self):
        self.record('TEST-01')['data']['environment']['id'] = 'REQ-01'
        self.save()
        with self.assertRaises(ValueError):
            inspect(self.p, self.m)

    def test_dependency_cycle(self):
        self.record('REQ-01')['relations'].append({'kind':'depends_on','target_id':'TASK-01'})
        self.record('TASK-01')['relations'].append({'kind':'depends_on','target_id':'REQ-01'})
        self.save()
        with self.assertRaisesRegex(ValueError,'dependency cycle'):
            inspect(self.p, self.m)

    def test_hierarchy_cycle(self):
        self.record('REQ-01')['relations'].append({'kind':'parent_of','target_id':'TASK-01'})
        self.record('TASK-01')['relations'].append({'kind':'parent_of','target_id':'REQ-01'})
        self.save()
        with self.assertRaisesRegex(ValueError,'hierarchy cycle'):
            inspect(self.p, self.m)

    def test_body_digest(self):
        r = self.record('INTENT-01')
        raw = r.pop('body').encode()
        (self.p / 'intent.md').write_bytes(raw)
        r['body_ref'] = {'path':'intent.md','anchor':'intent',
                         'sha256':hashlib.sha256(raw).hexdigest()}
        self.save()
        self.assertFalse(inspect(self.p,self.m)['body_anchors_verified'])
        (self.p / 'intent.md').write_text('edited')
        with self.assertRaises(ValueError):
            inspect(self.p,self.m)

    def test_symlink_source(self):
        path = self.p / 'fixtures/records.json'
        path.rename(self.p / 'actual.json')
        path.symlink_to(self.p / 'actual.json')
        with self.assertRaises(ValueError):
            inspect(self.p,self.m)

    def test_old_baseline_evidence_review(self):
        prior = copy.deepcopy(self.record('BASE-01'))
        prior['revision'] = 2
        self.record('BASE-01')['lifecycle'] = 'superseded'
        self.r.append(prior)
        self.m['baseline_ref']['revision'] = 2
        self.record('EVID-01')['data']['validity'] = 'current'
        self.record('EVID-01')['data']['result'] = 'pass'
        self.save()
        self.assertTrue(inspect(self.p,self.m)['evidence'][0]['review_required'])

    def test_current_nonpass_requires_review(self):
        self.record('EVID-01')['data']['validity'] = 'current'
        self.save()
        self.assertTrue(inspect(self.p,self.m)['evidence'][0]['review_required'])

    def test_current_pass_without_artifact_requires_review(self):
        data = self.record('EVID-01')['data']
        data.update(validity='current', result='pass', artifact_sha256=None)
        self.save()
        self.assertTrue(inspect(self.p,self.m)['evidence'][0]['review_required'])

    def test_reported_pass_never_authenticates_evidence(self):
        data = self.record('EVID-01')['data']
        data.update(validity='current', result='pass', artifact_sha256='a' * 64)
        self.save()
        observation = inspect(self.p,self.m)['evidence'][0]
        self.assertFalse(observation['authenticity_verified'])
