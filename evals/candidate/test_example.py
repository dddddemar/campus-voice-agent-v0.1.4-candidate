"""演示候选人评测的运行方式；请扩展为与你所选问题相关的场景。"""
import unittest
from voice_agent import policy
from voice_agent.simulator import run
from voice_agent.evaluation import load_scenes


class Example(unittest.TestCase):
    def test_basic_explicit_command(self):
        s = load_scenes("data/public_scenarios.jsonl")[0]
        result = run(s, policy)
        self.assertTrue(result["acknowledged"])
        self.assertEqual(result["commits"][0]["target"], s["world"]["target"])
