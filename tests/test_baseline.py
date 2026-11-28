import copy
import unittest
from pathlib import Path

from forge_baseline import fingerprint, inspect_baseline
from forge_validate import load

ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.r = {(r['id'],r['revision']):r for r in load(ROOT/'fixtures/records.json')}
        self.b = self.r[('BASE-01',1)]

    def test_order_independent_composition(self):
        a = fingerprint(self.r,self.b)
        self.b['data']['composition'].reverse()
        self.assertEqual(a,fingerprint(dict(reversed(list(self.r.items()))),self.b))

    def test_content_change_detected(self):
        a = fingerprint(self.r,self.b)
        self.r[('REQ-01',1)]['body'] = 'changed'
        self.assertNotEqual(a,fingerprint(self.r,self.b))

    def test_unrelated_change_not_in_fingerprint(self):
        a = fingerprint(self.r,self.b)
        self.r[('TASK-01',1)]['title'] = 'other'
        self.assertEqual(a,fingerprint(self.r,self.b))

    def test_invalid_composition(self):
        for values in ([], [{'id':'BASE-01','revision':1}],
                       [{'id':'REQ-01','revision':1}]*2,
                       [{'id':'REQ-UNKNOWN','revision':1}]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                b=copy.deepcopy(self.b)
                b['data']['composition']=values
                fingerprint(self.r,b)

    def test_legacy_placeholder_not_a_match(self):
        result = inspect_baseline(ROOT,'fixtures/project.json')
        self.assertFalse(result['composition_matches'])
        self.assertFalse(result['snapshot_authenticity_verified'])
        self.assertFalse(result['authority_verified'])
