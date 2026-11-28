import copy
from pathlib import Path
import tomllib
import unittest

from forge_agents import render, BOUNDARY
from forge_validate import load

ROOT = Path(__file__).resolve().parents[1]


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.b = load(ROOT / 'examples/portable-candidate/blueprint.json')
        self.s = {'project_id': self.b['project_id'], 'agents': [
            {'role_id': self.b['roles'][0]['id'], 'name': 'forge-material-trace',
             'description': '独自の素材応答を評価 🧪',
             'instructions': 'Review "response".\nKeep \\ and uncertainty.\x7f'}]}

    def test_render_arbitrary_role(self):
        result = render(self.b, self.s)
        data = tomllib.loads(result['codex_files']['.codex/agents/forge-material-trace.toml'])
        self.assertEqual(data['description'], self.s['agents'][0]['description'])
        self.assertEqual(data['developer_instructions'],
                         self.s['agents'][0]['instructions'] + '\n\n' + BOUNDARY)
        self.assertEqual(result['portable_roles'][0]['role_id'], self.b['roles'][0]['id'])
        self.assertFalse(result['native_loaded'])
        self.assertFalse(result['authority_verified'])

    def test_empty_agents_allowed(self):
        self.s['agents'] = []
        self.assertEqual(render(self.b, self.s)['codex_files'], {})

    def test_multiple_arbitrary_agents(self):
        a = copy.deepcopy(self.s['agents'][0])
        a['name'] = 'forge-delay-comparison'
        self.s['agents'].append(a)
        self.assertEqual(len(render(self.b, self.s)['codex_files']), 2)

    def test_unknown_role(self):
        self.s['agents'][0]['role_id'] = 'ROLE-MISSING'
        with self.assertRaises(ValueError):
            render(self.b, self.s)

    def test_other_project(self):
        self.s['project_id'] = 'PROJECT-OTHER'
        with self.assertRaises(ValueError):
            render(self.b, self.s)

    def test_duplicate_name(self):
        self.s['agents'].append(copy.deepcopy(self.s['agents'][0]))
        with self.assertRaises(ValueError):
            render(self.b, self.s)

    def test_builtin_or_path_name_rejected(self):
        for name in ('explorer', '../forge-escape', 'forge-a/b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.s['agents'][0]['name'] = name
                render(self.b, self.s)

    def test_permission_override_rejected(self):
        self.s['agents'][0]['sandbox_mode'] = 'danger-full-access'
        with self.assertRaises(ValueError):
            render(self.b, self.s)
