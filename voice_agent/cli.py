import argparse
import importlib.util
import json
from pathlib import Path
from . import policy as baseline
from .evaluation import load_scenes, summarize
from .simulator import run


def load_policy(path):
    if path is None:
        return baseline
    spec = importlib.util.spec_from_file_location("submitted_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description="Replay synthetic Voice Agent scenarios")
    parser.add_argument("--scenarios", default="data/public_scenarios.jsonl")
    parser.add_argument("--policy", help="Optional standalone policy file (internal comparison)")
    parser.add_argument("--out", default="runs/current")
    args = parser.parse_args()
    scenes = load_scenes(args.scenarios)
    selected_policy = load_policy(args.policy)
    runs = [run(scene, selected_policy) for scene in scenes]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "traces.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in runs))
    summary = summarize(runs)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "ok", "summary": summary, "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
