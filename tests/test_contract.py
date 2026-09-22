import copy
import json
import unittest
from pathlib import Path
from voice_agent import policy
from voice_agent.simulator import run
from voice_agent.evaluation import load_scenes, percentile


def scene():
    return load_scenes("data/public_scenarios.jsonl")[0]


class Contract(unittest.TestCase):
    def test_deterministic_and_no_mutation(self):
        s = scene()
        before = copy.deepcopy(s)
        self.assertEqual(run(s, policy), run(s, policy))
        self.assertEqual(s, before)

    def test_same_key_deduplicates_after_timeout(self):
        class P:
            select_model = staticmethod(lambda r: "strong")
            choose_action = staticmethod(lambda r, p: {"kind": "execute", "target": p["candidates"][0]["target"]})
            retry_key = staticmethod(lambda r, t: t["original_key"])
        s = scene()
        s["world"]["timeout"] = "after_commit"
        self.assertEqual(len(run(s, P)["commits"]), 1)
        s["world"]["timeout"] = "before_commit"
        self.assertEqual(len(run(s, P)["commits"]), 1)

    def test_new_key_is_new_command(self):
        class P:
            select_model = staticmethod(lambda r: "strong")
            choose_action = staticmethod(lambda r, p: {"kind": "execute", "target": p["candidates"][0]["target"]})
            retry_key = staticmethod(lambda r, t: t["original_key"] + ":another")
        s = scene()
        s["world"]["timeout"] = "after_commit"
        self.assertEqual(len(run(s, P)["commits"]), 2)

    def test_unanswered_clarification_does_not_execute(self):
        class P:
            select_model = staticmethod(lambda r: "strong")
            choose_action = staticmethod(lambda r, p: {"kind": "clarify"})
            retry_key = staticmethod(lambda r, t: None)
        s = scene()
        s["world"]["clarification_answered"] = False
        result = run(s, P)
        self.assertEqual(result["commits"], [])
        self.assertEqual(result["latency_ms"], 1300)

    def test_world_not_given_to_policy(self):
        class P:
            @staticmethod
            def select_model(r):
                self.assertNotIn("world", r)
                return "strong"
            choose_action = staticmethod(lambda r, p: {"kind": "abstain"})
            retry_key = staticmethod(lambda r, t: None)
        self.assertFalse(run(scene(), P)["acknowledged"])

    def test_nearest_rank_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], .95), 5)
        self.assertIsNone(percentile([], .95))


if __name__ == "__main__":
    unittest.main()
