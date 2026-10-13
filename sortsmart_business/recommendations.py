"""SortSmart Business recommendations engine.

Turns cost + scoring data into prioritized, dollar-quantified actions
for specific business types.
"""

from .costs import (
    BUSINESS_PROFILES, monthly_disposal_cost, packaging_comparison,
    composting_savings, diversion_roi,
)
from .scoring import score_business


def business_brief(business_type="retail", monthly_shipments=0,
                   packaging="poly_mailer", diversion_rate_pct=25,
                   composts_food=False, ewaste_program=False,
                   hazmat_program=False):
    """Build a full advisory brief for a business.

    Returns a dict with costs, score, and ranked recommendations —
    everything the LLM layer needs to give grounded advice.
    """
    profile_key = business_type if business_type in BUSINESS_PROFILES else "retail"
    waste = BUSINESS_PROFILES[profile_key]["waste_lbs_month"]

    costs = monthly_disposal_cost(waste)
    score = score_business({
        "business_type": profile_key,
        "diversion_rate_pct": diversion_rate_pct,
        "packaging": packaging,
        "composts_food": composts_food,
        "ewaste_program": ewaste_program,
        "hazmat_program": hazmat_program,
        "monthly_shipments": monthly_shipments,
    })

    recommendations = []

    # Packaging recommendation (for shippers)
    if monthly_shipments > 0:
        options = packaging_comparison(monthly_shipments, current=packaging)
        current_opt = next(o for o in options if o["material"] == packaging)
        # best sustainable option: cheapest recyclable-or-compostable
        green = [o for o in options if o["recyclable"] or o["compostable"]]
        if green:
            best_green = min(green, key=lambda o: o["monthly_cost"])
            if best_green["material"] != packaging:
                recommendations.append({
                    "action": f"Switch outbound packaging to {best_green['material'].replace('_', ' ')}",
                    "monthly_cost_delta": best_green["delta_vs_current"],
                    "annual_cost_delta": round(best_green["delta_vs_current"] * 12, 2),
                    "impact": "Customer-visible sustainability win; recyclable/compostable packaging.",
                    "priority": "high" if monthly_shipments >= 500 else "medium",
                })

    # Composting recommendation (food-heavy businesses)
    if profile_key == "restaurant" and not composts_food:
        food_lbs = waste.get("food_scraps", 0)
        if food_lbs:
            sv = composting_savings(food_lbs)
            recommendations.append({
                "action": "Start commercial composting for food waste",
                "monthly_cost_delta": -sv["monthly_savings"],
                "annual_cost_delta": -sv["annual_savings"],
                "impact": f"Diverts {food_lbs:,} lbs/month from landfill; cuts hauling weight.",
                "priority": "high",
            })

    # Diversion ROI
    monthly_tons = sum(waste.values()) / 2000.0
    roi = diversion_roi(diversion_rate_pct, min(80, diversion_rate_pct + 30), monthly_tons)
    if roi["annual_savings"] > 0:
        recommendations.append({
            "action": f"Lift diversion rate from {diversion_rate_pct}% toward {min(80, diversion_rate_pct + 30)}%",
            "monthly_cost_delta": -roi["monthly_savings"],
            "annual_cost_delta": -roi["annual_savings"],
            "impact": "Staff training + labeled bins; the cheapest lever per dollar saved.",
            "priority": "high",
        })

    # Score levers that aren't covered above
    for lever in score["top_levers"]:
        if not any(lever["lever"].lower() in r["action"].lower() for r in recommendations):
            recommendations.append({
                "action": lever["lever"],
                "monthly_cost_delta": None,
                "annual_cost_delta": None,
                "impact": lever["why"],
                "priority": "medium",
            })

    def _rank(r):
        # negative annual delta = savings; rank biggest savings first
        savings = -(r["annual_cost_delta"] or 0)
        prio = {"high": 0, "medium": 1, "low": 2}[r["priority"]]
        return (prio, -savings)

    recommendations.sort(key=_rank)

    return {
        "business_type": BUSINESS_PROFILES[profile_key]["label"],
        "monthly_disposal": costs,
        "sustainability": score,
        "recommendations": recommendations,
        "assumptions": "US national average costs; validate against local hauler rates.",
    }
