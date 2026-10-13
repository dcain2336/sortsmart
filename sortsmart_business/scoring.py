"""SortSmart Business sustainability scoring (0-100).

Transparent, explainable scoring — every point is traceable to an input.
Not a certification; a directional business tool.
"""

from .costs import BUSINESS_PROFILES, STREAM_MAP, PACKAGING


def score_business(profile):
    """Score a business sustainability profile 0-100.

    profile keys (all optional, sensible defaults applied):
      - business_type: key in BUSINESS_PROFILES
      - diversion_rate_pct: current waste diversion rate (0-100)
      - packaging: key in PACKAGING (primary outbound packaging)
      - composts_food: bool
      - ewaste_program: bool (has dedicated e-waste collection)
      - hazmat_program: bool (has hazardous waste handling)
      - monthly_shipments: int (for packaging impact weighting)

    Returns {"score": int, "grade": str, "breakdown": {...}, "top_levers": [...]}.
    """
    breakdown = {}
    levers = []

    # 1. Diversion rate — 40 points. 80%+ diversion is best-in-class.
    div = max(0.0, min(100.0, float(profile.get("diversion_rate_pct", 25))))
    div_pts = round(div / 100.0 * 40)
    breakdown["diversion"] = {"points": div_pts, "max": 40,
                              "detail": f"{div:.0f}% diversion rate"}
    if div < 50:
        levers.append({"lever": "Raise diversion rate",
                       "why": f"At {div:.0f}%, most waste still goes to landfill — the most expensive stream.",
                       "potential_points": 40 - div_pts})

    # 2. Packaging — 25 points.
    pkg = profile.get("packaging", "poly_mailer")
    spec = PACKAGING.get(pkg, PACKAGING["poly_mailer"])
    pkg_pts = 0
    if spec["recyclable"]:
        pkg_pts += 13
    if spec["compostable"]:
        pkg_pts += 12
    if pkg == "reused_box":
        pkg_pts = 25
    breakdown["packaging"] = {"points": pkg_pts, "max": 25,
                              "detail": f"Primary packaging: {pkg.replace('_', ' ')}"}
    if pkg_pts < 20:
        better = [n for n, s in PACKAGING.items()
                  if (s["recyclable"] or s["compostable"]) and n != pkg]
        levers.append({"lever": f"Switch packaging to {better[0].replace('_', ' ')}",
                       "why": "Packaging is the most visible sustainability signal to customers.",
                       "potential_points": 25 - pkg_pts})

    # 3. Food waste / composting — 15 points.
    btype = profile.get("business_type", "office")
    food_heavy = btype in ("restaurant",)
    if profile.get("composts_food"):
        food_pts = 15
    elif food_heavy:
        food_pts = 0
        levers.append({"lever": "Start composting food waste",
                       "why": "Food waste is heavy and landfilling it is the priciest option per ton.",
                       "potential_points": 15})
    else:
        food_pts = 10  # not material for this business type
    breakdown["food_waste"] = {"points": food_pts, "max": 15,
                               "detail": "Composting program active" if profile.get("composts_food")
                               else ("High-impact opportunity" if food_heavy else "Low materiality for this business")}
    # 4. E-waste program — 10 points.
    ew_pts = 10 if profile.get("ewaste_program") else 0
    breakdown["ewaste"] = {"points": ew_pts, "max": 10,
                           "detail": "Dedicated e-waste collection" if ew_pts else "No e-waste program"}
    if not ew_pts:
        levers.append({"lever": "Set up e-waste collection",
                       "why": "E-waste is free to drop off and keeps toxins out of landfill.",
                       "potential_points": 10})

    # 5. Hazardous handling — 10 points.
    hz_pts = 10 if profile.get("hazmat_program") else 5
    breakdown["hazardous"] = {"points": hz_pts, "max": 10,
                              "detail": "Hazmat program in place" if profile.get("hazmat_program")
                              else "Assumed basic compliance"}
    if not profile.get("hazmat_program"):
        levers.append({"lever": "Formalize hazardous waste handling",
                       "why": "Hazmat disposal is ~8x landfill cost per ton — reduction pays fast.",
                       "potential_points": 5})

    total = div_pts + pkg_pts + food_pts + ew_pts + hz_pts
    grade = "A" if total >= 85 else "B" if total >= 70 else "C" if total >= 50 else "D" if total >= 30 else "F"

    levers.sort(key=lambda l: l["potential_points"], reverse=True)
    return {
        "score": total,
        "grade": grade,
        "breakdown": breakdown,
        "top_levers": levers[:3],
        "business_type": BUSINESS_PROFILES.get(btype, {}).get("label", btype),
    }
