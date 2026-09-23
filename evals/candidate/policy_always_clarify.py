"""中间实验方案（已不作为最终策略）：无 explicit_target 时一律澄清。

保留供对照复现：
  uv run --quiet --offline --no-project python -m voice_agent.cli \\
    --policy evals/candidate/policy_always_clarify.py --out runs/experiment_always_clarify
"""


def select_model(request):
    if request['risk'] == 'high' and request['explicit_target'] is None:
        return 'small'
    if request['explicit_target']:
        return 'standard'
    if request['history']:
        return 'strong'
    return 'standard'


def choose_action(request, prediction):
    ranked = sorted(prediction['candidates'], key=lambda c: c['confidence'], reverse=True)
    explicit = request['explicit_target']
    if explicit is None:
        return {'kind': 'clarify'}
    if any(c['target'] == explicit for c in ranked):
        return {'kind': 'execute', 'target': explicit}
    return {'kind': 'clarify'}


def retry_key(request, timeout):
    return timeout['original_key']
