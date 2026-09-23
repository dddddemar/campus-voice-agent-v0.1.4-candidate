"""Current production policies: safe high-risk handling and basic routing already work."""
from .history_resolve import resolve_structured_reference


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
    cand_targets = [c['target'] for c in ranked]
    explicit = request['explicit_target']
    if explicit is not None:
        if any(c['target'] == explicit for c in ranked):
            return {'kind': 'execute', 'target': explicit}
        return {'kind': 'clarify'}
    # No confirmed target: do not trust model confidence alone (silent wrong executes).
    # High-risk stays clarify-only. Low-risk may execute only via structured history refs.
    if request['risk'] == 'high':
        return {'kind': 'clarify'}
    resolved = resolve_structured_reference(request, cand_targets)
    if resolved is not None and resolved in cand_targets:
        return {'kind': 'execute', 'target': resolved}
    return {'kind': 'clarify'}


def retry_key(request, timeout):
    return timeout['original_key']
