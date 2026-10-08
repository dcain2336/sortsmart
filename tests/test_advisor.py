import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sortsmart import advise  # noqa: E402


def test_tricky_items():
    assert advise("greasy pizza box")["category"] == "compost"
    assert advise("AA battery")["category"] == "ewaste"
    assert advise("plastic bag")["category"] == "reuse"  # never curbside!
    assert advise("receipt")["category"] == "landfill"  # thermal paper


def test_confidence_present():
    r = advise("wine bottle")
    assert r["confidence"] in ("high", "medium", "low")
    assert r["category"] == "recycle"


def test_unknown_item_safe_default():
    r = advise("quantum flux capacitor")
    assert r["category"] == "landfill"
    assert r["confidence"] == "low"
