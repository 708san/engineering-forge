import unittest
from order import relation


class OrderTests(unittest.TestCase):
    def test_disjoint(self):
        self.assertEqual(relation((0, 2), (3, 5)), 'before')
        self.assertEqual(relation((3, 5), (0, 2)), 'after')

    def test_touching(self):
        self.assertEqual(relation((0, 3), (3, 5)), 'indeterminate')

    def test_overlap(self):
        self.assertEqual(relation((0, 5), (2, 4)), 'indeterminate')

    def test_invalid(self):
        with self.assertRaises(ValueError):
            relation((3, 2), (0, 1))

    def test_same_point(self):
        self.assertEqual(relation((2, 2), (2, 2)), 'indeterminate')
