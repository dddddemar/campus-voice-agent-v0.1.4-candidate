"""Resolve referential asks from observable history text only (no world)."""


def candidate_mentions_in_order(history, candidates):
    """Return candidate target ids in order of first appearance in history strings."""
    text = " ".join(history or [])
    if not text or not candidates:
        return []
    # Longer names first so hall_light is not split by a shorter token if any overlap.
    targets = sorted(set(candidates), key=len, reverse=True)
    hits = []
    for target in targets:
        start = 0
        while True:
            idx = text.find(target, start)
            if idx < 0:
                break
            hits.append((idx, target))
            start = idx + len(target)
    hits.sort(key=lambda item: item[0])
    ordered = []
    for _, target in hits:
        if not ordered or ordered[-1] != target:
            ordered.append(target)
    return ordered


def resolve_structured_reference(request, candidates):
    """
    If the user utterance encodes an ordinal/revision over history mentions,
    return that target when it is in the candidate list; else None (caller should clarify).
    """
    text = request.get("text") or ""
    order = candidate_mentions_in_order(request.get("history"), candidates)
    if not order:
        return None
    if "前一个" in text:
        return order[0]
    if "后一个" in text:
        return order[-1]
    # Last confirmed change in the visible dialogue.
    if "改好" in text or "换成" in text:
        return order[-1]
    return None
