"""Check availability of optional guidance, not the quality of AI reasoning."""
from pathlib import Path
import unittest
from forge_pack import REFERENCES


ROOT = Path(__file__).resolve().parents[1]


class GuidancePackTests(unittest.TestCase):
    def test_optional_guidance_is_packaged(self):
        for name in ('knowledge/design-reasoning.md', 'evaluation/design-worked-example.md'):
            with self.subTest(name=name):
                self.assertIn(name, REFERENCES)
                self.assertTrue((ROOT / name).is_file())

    def test_eight_skill_reference_targets_exist(self):
        names = [name for name in REFERENCES if name.startswith('.agents/skills/')]
        self.assertEqual(len(names), 8)
        for name in names:
            path = ROOT / name
            with self.subTest(name=name):
                target = '../../../knowledge/design-reasoning.md'
                self.assertIn(target, path.read_text(encoding='utf-8'))
                self.assertEqual((path.parent / target).resolve(),
                                 (ROOT / 'knowledge/design-reasoning.md').resolve())
