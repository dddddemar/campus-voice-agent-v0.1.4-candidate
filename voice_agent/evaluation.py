"""现有看板与读取入口。策略代码和统计逻辑分离，候选人可新增指标。"""
import json
from math import ceil
from pathlib import Path


def load_scenes(path):
    scenes = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    ids = [s["id"] for s in scenes]
    if not scenes or len(ids) != len(set(ids)):
        raise ValueError("scenario IDs must be nonempty and unique")
    return scenes


def percentile(values, q):
    if not values:
        return None
    return sorted(values)[max(0, ceil(q * len(values)) - 1)]


def summarize(runs):
    if not runs:
        raise ValueError("no runs")
    # 沿用旧看板字段名：只检查助手拿到工具回执，不等于核验用户目标。
    accepted = sum(r["acknowledged"] for r in runs)
    return {
        "sessions": len(runs),
        "legacy_task_success": {"numerator": accepted, "denominator": len(runs),
                                "rate": accepted / len(runs)},
        "p95_latency_ms": percentile([r["latency_ms"] for r in runs], 0.95),
        "mean_model_cost_usd": round(sum(r["model_cost_usd"] for r in runs) / len(runs), 6),
    }
