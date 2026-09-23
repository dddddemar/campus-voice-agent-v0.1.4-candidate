"""主问题 A：无明确目标时禁止高置信盲执行；允许结构化 history 序数/修订解析。"""
import copy
import importlib.util
import unittest

from voice_agent import policy
from voice_agent.evaluation import load_scenes
from voice_agent.simulator import run


def cff(result, world_target):
    """acknowledged 且存在错误目标 commit。"""
    return bool(result["acknowledged"]) and any(
        c["target"] != world_target for c in result["commits"]
    )


def load_policy_file(path):
    spec = importlib.util.spec_from_file_location("exp_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AmbiguousHighConfExecute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = {s["id"]: s for s in load_scenes("data/public_scenarios.jsonl")}
        cls.extra = {s["id"]: s for s in load_scenes("evals/candidate/ambiguous_scenarios.jsonl")}
        cls.always = load_policy_file("evals/candidate/policy_always_clarify.py")

    def test_failure_cases_no_longer_cff(self):
        """原 public 失败案：改后不得再贡献 CFF；含糊「那个」仍应澄清。"""
        for sid in ("s-259ea45b42008319", "s-5b75abb97be5852c"):
            scene = self.scenes[sid]
            result = run(scene, policy)
            self.assertFalse(cff(result, scene["world"]["target"]), sid)
            self.assertTrue(result["clarified"], sid)

    def test_new_deictic_instances_clarify(self):
        """同原则新实例：无结构信号的歧义指代 → clarify。"""
        for sid, scene in self.extra.items():
            if not sid.startswith("new-deictic"):
                continue
            obs = scene["observation"]
            pred = scene["models"]["standard"]
            decision = policy.choose_action(copy.deepcopy(obs), copy.deepcopy(pred))
            self.assertEqual(decision["kind"], "clarify", sid)
            result = run(scene, policy)
            self.assertFalse(cff(result, scene["world"]["target"]), sid)

    def test_ordinal_and_revision_new_instances(self):
        """细分流新实例：前一个/后一个/改好 在澄清会失败时应仍能执行对目标。"""
        for sid in ("new-ordinal-first", "new-ordinal-last", "new-revision-last"):
            scene = self.extra[sid]
            result = run(scene, policy)
            self.assertFalse(result["clarified"], sid)
            self.assertEqual(result["commits"][0]["target"], scene["world"]["target"], sid)
            # 对照：一律澄清在 clarification_answered=false 时会失败
            always_result = run(scene, self.always)
            self.assertEqual(always_result["commits"], [], sid)

    def test_unstructured_deictic_not_forced_by_confidence(self):
        """可推翻：仅「刚才那个」+ 高 conf 不得执行（避免复活 CFF）。"""
        scene = self.extra["falsify-ordinal-wrong-order"]
        obs = scene["observation"]
        pred = scene["models"]["strong"]
        ranked = sorted(pred["candidates"], key=lambda c: c["confidence"], reverse=True)
        margin = ranked[0]["confidence"] - ranked[1]["confidence"]
        self.assertGreaterEqual(ranked[0]["confidence"], 0.8)
        self.assertGreaterEqual(margin, 0.4)
        decision = policy.choose_action(copy.deepcopy(obs), copy.deepcopy(pred))
        self.assertEqual(decision["kind"], "clarify")
        result = run(scene, policy)
        self.assertFalse(cff(result, scene["world"]["target"]))

    def test_explicit_regression_still_executes(self):
        """正常回归：明确目标且在候选中 → execute 正确目标。"""
        scene = self.scenes["s-b4513a630fe7ab1f"]
        result = run(scene, policy)
        self.assertFalse(result["clarified"])
        self.assertEqual(result["commits"][0]["target"], scene["world"]["target"])
        self.assertTrue(result["acknowledged"])

    def test_high_risk_no_explicit_still_clarifies(self):
        """边界：高风险无明确目标仍澄清（保留已有保障）。"""
        for scene in self.scenes.values():
            obs = scene["observation"]
            if obs["risk"] == "high" and obs["explicit_target"] is None:
                pred = scene["models"][policy.select_model(copy.deepcopy(obs))]
                decision = policy.choose_action(copy.deepcopy(obs), copy.deepcopy(pred))
                self.assertEqual(decision["kind"], "clarify", scene["id"])
                break
        else:
            self.fail("no high-risk no-explicit scene found")

    def test_falsify_high_conf_no_longer_auto_executes(self):
        """可推翻点：若无 explicit 仍按高 conf/margin 执行，则主张不成立。"""
        scene = self.extra["new-deictic-01"]
        obs = scene["observation"]
        pred = scene["models"]["standard"]
        ranked = sorted(pred["candidates"], key=lambda c: c["confidence"], reverse=True)
        top = ranked[0]
        margin = top["confidence"] - (ranked[1]["confidence"] if len(ranked) > 1 else 0)
        self.assertGreaterEqual(top["confidence"], 0.8)
        self.assertGreaterEqual(margin, 0.4)
        decision = policy.choose_action(copy.deepcopy(obs), copy.deepcopy(pred))
        self.assertEqual(decision["kind"], "clarify")

    def test_public_cff_is_zero(self):
        """全集主指标：CFF 分子为 0，分母 100。"""
        bad = []
        for scene in self.scenes.values():
            result = run(scene, policy)
            if cff(result, scene["world"]["target"]):
                bad.append(scene["id"])
        self.assertEqual(bad, [], f"CFF cases: {bad}")

    def test_final_beats_always_clarify_on_true_success(self):
        """最终方案相对中间「一律澄清」：CFF 同为 0，真成功不更差。"""
        def score(pol):
            cff_n = true_n = 0
            for scene in self.scenes.values():
                result = run(scene, pol)
                world = scene["world"]["target"]
                wrong = any(c["target"] != world for c in result["commits"])
                if result["acknowledged"] and wrong:
                    cff_n += 1
                if result["commits"] and not wrong:
                    true_n += 1
            return cff_n, true_n

        cff_final, true_final = score(policy)
        cff_always, true_always = score(self.always)
        self.assertEqual(cff_final, 0)
        self.assertEqual(cff_always, 0)
        self.assertGreaterEqual(true_final, true_always)
