import unittest
from forge_json import loads
from forge_handoff import load as handoff_load
from forge_validate import load as validate_load
from forge_json import load


class StrictJsonTests(unittest.TestCase):
    def test_reject_duplicate_nested_key(self):
        with self.assertRaises(ValueError):
            loads('{"a":{"x":1,"x":2}}')

    def test_reject_nonfinite_values(self):
        for value in ('NaN', 'Infinity', '-Infinity', '1e999', '-1e999'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                loads('{"value":'+value+'}')

    def test_valid_numbers_and_unicode(self):
        self.assertEqual(loads('{"日本語":[1,1.5,1e-5,null,true]}'),
                         {'日本語':[1,1.5,0.00001,None,True]})

    def test_shared_parser_used(self):
        self.assertIs(handoff_load, load)
        self.assertIs(validate_load, load)
