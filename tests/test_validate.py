import copy
import tempfile
import unittest
from pathlib import Path
from forge_validate import load, validate

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/portable-candidate'


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.c = load(EXAMPLE / 'blueprint.json')
        self.b = load(EXAMPLE / 'baseline.example.json')

    def test_example(self):
        self.assertEqual(validate(self.c, self.b), [])

    def test_new_proposal(self):
        self.assertEqual(validate(self.c), [])

    def test_novel_method(self):
        self.c['methods'][0]['name'] = '光と素材の新しい比較法'
        self.c['artifacts'][0]['format'] = 'unregistered-format'
        self.assertEqual(validate(self.c, self.b), [])

    def test_duplicate_id(self):
        self.c['roles'].append(copy.deepcopy(self.c['roles'][0]))
        self.assertIn('duplicate record ID', validate(self.c))

    def test_bad_reference(self):
        self.c['methods'][0]['artifact_ids'] = ['ART-ABSENT']
        self.assertTrue(validate(self.c))

    def test_unaddressed(self):
        self.c['methods'] = self.c['holds'] = []
        self.assertTrue(validate(self.c))

    def test_removed_requirement(self):
        self.c['outcomes'] = self.c['methods'] = self.c['holds'] = []
        self.assertTrue(validate(self.c, self.b))

    def test_downgrade(self):
        self.c['outcomes'][0]['mandatory'] = False
        self.assertTrue(validate(self.c, self.b))

    def test_other_project(self):
        self.b['project_id'] = 'PROJECT-OTHER'
        self.assertTrue(validate(self.c, self.b))

    def test_malformed_baseline(self):
        self.assertTrue(validate(self.c, []))

    def test_malformed_candidate(self):
        self.assertTrue(validate({}, self.b))

    def test_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.json'
            p.write_text('{"id": 1, "id": 2}')
            with self.assertRaises(ValueError):
                load(p)


if __name__ == '__main__':
    unittest.main()
