"""输出主问题 A 的 CFF 与代价指标（分子/分母）。"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice_agent import policy as baseline_policy
from voice_agent.evaluation import load_scenes, summarize
from voice_agent.simulator import run


def load_policy(path):
    if path is None:
        return baseline_policy
    spec = importlib.util.spec_from_file_location("metrics_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cff_count(runs, scenes):
    by_id = {s["id"]: s for s in scenes}
    n = 0
    for r in runs:
        world = by_id[r["id"]]["world"]["target"]
        if r["acknowledged"] and any(c["target"] != world for c in r["commits"]):
            n += 1
    return n


def true_success_count(runs, scenes):
    by_id = {s["id"]: s for s in scenes}
    n = 0
    for r in runs:
        world = by_id[r["id"]]["world"]["target"]
        if r["commits"] and all(c["target"] == world for c in r["commits"]):
            n += 1
    return n


def high_risk_wrong_count(runs, scenes):
    by_id = {s["id"]: s for s in scenes}
    n = 0
    for r in runs:
        scene = by_id[r["id"]]
        if scene["observation"]["risk"] != "high":
            continue
        world = scene["world"]["target"]
        if any(c["target"] != world for c in r["commits"]):
            n += 1
    return n


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenarios", default="data/public_scenarios.jsonl")
    p.add_argument("--policy", help="可选策略文件；默认当前 voice_agent.policy")
    p.add_argument("--out", default="evals/candidate/metrics_after.json")
    args = p.parse_args()
    scenes = load_scenes(args.scenarios)
    selected = load_policy(args.policy)
    runs = [run(s, selected) for s in scenes]
    n = len(runs)
    metrics = {
        "policy": args.policy or "voice_agent.policy",
        "denominator": n,
        "cff": {"numerator": cff_count(runs, scenes), "denominator": n},
        "true_task_success": {"numerator": true_success_count(runs, scenes), "denominator": n},
        "high_risk_wrong_target": {
            "numerator": high_risk_wrong_count(runs, scenes),
            "denominator": sum(1 for s in scenes if s["observation"]["risk"] == "high"),
        },
        "clarified": {"numerator": sum(1 for r in runs if r["clarified"]), "denominator": n},
        "legacy_summary": summarize(runs),
    }
    for key in ("cff", "true_task_success", "clarified"):
        metrics[key]["rate"] = metrics[key]["numerator"] / n
    hr = metrics["high_risk_wrong_target"]
    hr["rate"] = hr["numerator"] / hr["denominator"] if hr["denominator"] else None
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
