"""离线、确定性模拟。模拟事实和计费，不执行真实设备动作或网络请求。"""
from copy import deepcopy

MODELS = {
    "small": {"latency_ms": 100, "cost_usd": 0.001},
    "standard": {"latency_ms": 250, "cost_usd": 0.003},
    "strong": {"latency_ms": 700, "cost_usd": 0.009},
}


def validate(scene):
    obs = scene["observation"]
    if obs["action"] not in ("set_power", "toggle", "send_message"):
        raise ValueError("unsupported action")
    if obs["risk"] not in ("low", "high"):
        raise ValueError("risk must be low or high")
    if scene["world"]["timeout"] not in ("none", "after_commit", "before_commit"):
        raise ValueError("invalid timeout")
    if not isinstance(scene["world"]["clarification_answered"], bool):
        raise ValueError("clarification_answered must be boolean")
    if not isinstance(scene["world"]["target"], str):
        raise ValueError("world target must be a string")
    for model in MODELS:
        pred = scene["models"][model]
        if not pred["candidates"]:
            raise ValueError("model candidates cannot be empty")
        for item in pred["candidates"]:
            if not isinstance(item["target"], str) or not 0 <= item["confidence"] <= 1:
                raise ValueError("invalid candidate")
    return scene


def run(scene, policy):
    validate(scene)
    obs, world = deepcopy(scene["observation"]), scene["world"]
    events = []
    model = policy.select_model(deepcopy(obs))
    if model not in MODELS:
        raise ValueError("unknown model selected")
    timing = MODELS[model]
    latency, cost = timing["latency_ms"], timing["cost_usd"]
    prediction = deepcopy(scene["models"][model])
    events.append({"type": "model", "model": model, "prediction": prediction})
    decision = policy.choose_action(deepcopy(obs), deepcopy(prediction))
    kind = decision.get("kind")
    if kind not in ("execute", "clarify", "abstain"):
        raise ValueError("decision kind must be execute, clarify or abstain")
    clarified, target, acknowledged = kind == "clarify", None, False
    if clarified:
        latency += 1200 if obs.get("interaction_mode") == "busy" else 600
        answered = world["clarification_answered"]
        events.append({"type": "clarification", "answered": answered})
        if answered:
            target = world["target"]
    elif kind == "execute":
        target = decision["target"]
        if target not in [v["target"] for v in prediction["candidates"]]:
            raise ValueError("execute target must come from selected model candidates")
    commits, seen_keys = [], set()
    first_key = obs["request_id"] + ":action"

    def commit(key):
        if key in seen_keys:
            events.append({"type": "deduplicated", "key": key})
            return
        seen_keys.add(key)
        effect = {"target": target, "action": obs["action"], "key": key}
        commits.append(effect)
        events.append({"type": "tool_committed", **effect})

    if target is not None:
        mode = world["timeout"]
        latency += 80 if mode == "none" else 500
        if mode != "before_commit":
            commit(first_key)
        if mode == "none":
            acknowledged = True
        else:
            events.append({"type": "tool_timeout", "key": first_key})
            retry = policy.retry_key(deepcopy(obs), {
                "original_key": first_key, "target": target, "attempt": 1,
            })
            if retry is not None:
                if not isinstance(retry, str) or not retry:
                    raise ValueError("retry key must be nonempty string or None")
                latency += 80
                commit(retry)  # same key gives original receipt; new key is a new command
                acknowledged = True
    events.append({"type": "assistant_response", "accepted": acknowledged})
    if any(c["target"] != world["target"] for c in commits):
        events.append({"type": "user_signal", "signal": "user_correction"})
    if len(commits) > 1 and obs["action"] in ("toggle", "send_message"):
        events.append({"type": "user_signal", "signal": "user_complaint"})
    for signal in world.get("signals", []):
        events.append({"type": "user_signal", "signal": signal})
    return {
        "id": scene["id"], "observation": deepcopy(obs), "events": events,
        "latency_ms": latency, "model_cost_usd": cost,
        "clarified": clarified, "acknowledged": acknowledged,
        "commits": commits,
    }
