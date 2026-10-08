#!/usr/bin/env python3
"""SortSmart end-to-end demo. Exercises the advisor, the Lambda handler
(API Gateway events), and the weekly tracker. Exits 0 on success."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sortsmart import advise, diversion_counts  # noqa: E402
from sortsmart.tracker import log_item, weekly_summary  # noqa: E402

# 'lambda' is a Python keyword, so load lambda/handler.py by path.
import importlib.util  # noqa: E402
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sortsmart_lambda_handler", os.path.join(_here, "lambda", "handler.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
lambda_handler = _mod.lambda_handler

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{PASS if cond else FAIL}] {name}" + (f" — {detail}" if detail and not cond else ""))


def main():
    print("== SortSmart demo ==\n")

    # 1. Advisor: tricky items get the right stream
    print("1. Waste-stream advice (the tricky ones):")
    cases = [
        ("greasy pizza box", "compost"),
        ("AA battery", "ewaste"),
        ("plastic bottle", "recycle"),
        ("banana peel", "compost"),
        ("old phone", "ewaste"),
        ("paint can", "hazardous"),
        ("chip bag", "landfill"),
        ("old jacket", "donate"),
    ]
    for item, expected in cases:
        got = advise(item)["category"]
        check(f"advise({item!r}) -> {expected}", got == expected, f"got {got}")
        a = advise(item)
        print(f"     {a['emoji']} {a['label']}: {a['why'][:80]}...")

    # 2. Lambda handler with API Gateway proxy events (no AWS needed)
    print("\n2. Lambda handler (API Gateway events, local):")
    ev = {"path": "/advise", "queryStringParameters": {"item": "wine bottle"}}
    resp = lambda_handler(ev)
    body = json.loads(resp["body"])
    check("GET /advise -> 200 + recycle", resp["statusCode"] == 200 and body["category"] == "recycle",
          f"{resp['statusCode']} {body.get('category')}")
    ev2 = {"path": "/advise", "queryStringParameters": {}}
    check("GET /advise (no item) -> 400", lambda_handler(ev2)["statusCode"] == 400)
    ev3 = {"path": "/nope", "queryStringParameters": {}}
    check("unknown route -> 404", lambda_handler(ev3)["statusCode"] == 404)

    # 3. Weekly tracker with a temp log (does not touch ~/.sortsmart_log.json)
    print("\n3. Weekly diversion tracker:")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        tmplog = tf.name
    for it in ["plastic bottle", "banana peel", "AA battery", "chip bag"]:
        log_item(it, path=tmplog)
    s = weekly_summary(path=tmplog)
    os.unlink(tmplog)
    check("4 items logged", s["items_logged"] == 4, str(s))
    check("diversion rate 75%", s["diversion_rate_pct"] == 75.0, str(s))
    print(f"     diversion rate: {s['diversion_rate_pct']}% ({s['diverted']}/{s['items_logged']} diverted)")
    d, t, r = diversion_counts([])
    check("empty log -> 0%", (d, t, r) == (0, 0, 0.0))

    failed = [n for n, ok in results if not ok]
    print(f"\n== demo complete: {len(results) - len(failed)}/{len(results)} passed ==")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
