"""SortSmart weekly tracker: log sorted items, see your diversion rate."""
import json
import os
from datetime import date
from .advisor import advise, diversion_counts

DEFAULT_LOG = os.path.expanduser("~/.sortsmart_log.json")


def load_log(path=DEFAULT_LOG):
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def log_item(item_description, path=DEFAULT_LOG):
    """Advise on an item and append the result to the weekly log. Returns advice."""
    advice = advise(item_description)
    entries = load_log(path)
    entries.append({
        "date": date.today().isoformat(),
        "item": advice["item"],
        "category": advice["category"],
    })
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)
    return advice


def weekly_summary(path=DEFAULT_LOG):
    entries = load_log(path)
    cats = [e["category"] for e in entries]
    diverted, total, rate = diversion_counts(cats)
    return {
        "items_logged": total,
        "diverted": diverted,
        "landfilled": total - diverted,
        "diversion_rate_pct": rate,
    }
