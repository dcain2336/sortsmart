"""SortSmart advisor: match a described item to a waste stream."""
import re
from .knowledge import ITEMS, CATEGORY_INFO


def _normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def advise(item_description):
    """Return advice dict for an item description.

    Result: {"item", "category", "label", "emoji", "why", "tip", "confidence"}
    confidence: high | medium | low
    """
    query = _normalize(item_description)
    if not query:
        return _unknown(item_description)

    best, best_score = None, 0
    for entry in ITEMS:
        for kw in entry["keywords"]:
            kw_norm = _normalize(kw)
            if not kw_norm:
                continue
            if kw_norm == query:
                score = 100 + len(kw_norm)
            elif query in kw_norm or kw_norm in query:
                score = 50 + len(kw_norm)
            else:
                # token overlap
                q_tokens, k_tokens = set(query.split()), set(kw_norm.split())
                overlap = q_tokens & k_tokens
                if not overlap:
                    continue
                score = 10 * len(overlap) + sum(len(t) for t in overlap) / 10
            if score > best_score:
                best, best_score = entry, score

    if best is None:
        return _unknown(item_description)

    info = CATEGORY_INFO[best["category"]]
    confidence = "high" if best_score >= 50 else "medium" if best_score >= 20 else "low"
    return {
        "item": item_description.strip(),
        "category": best["category"],
        "label": info["label"],
        "emoji": info["emoji"],
        "why": best["why"],
        "tip": best["tip"],
        "confidence": confidence,
    }


def _unknown(item_description):
    return {
        "item": item_description.strip(),
        "category": "landfill",
        "label": CATEGORY_INFO["landfill"]["label"],
        "emoji": "❓",
        "why": "I don't have a rule for this item yet — when in doubt, keep it out of recycling (one wrong item contaminates the bin).",
        "tip": "Check your local waste authority's search tool, or ask me about a similar item.",
        "confidence": "low",
    }


def diversion_counts(log_entries):
    """Given a list of category strings, return (diverted, total, rate_pct)."""
    total = len(log_entries)
    if not total:
        return 0, 0, 0.0
    diverted = sum(1 for c in log_entries if CATEGORY_INFO.get(c, {}).get("diverts"))
    return diverted, total, round(100.0 * diverted / total, 1)
