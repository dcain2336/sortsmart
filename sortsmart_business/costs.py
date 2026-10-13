"""SortSmart Business Advisor — cost models for commercial waste decisions.

All figures are US national averages (2024-2025 data) and are clearly labeled
as estimates. Businesses should validate against local hauler rates.
Sources: EPA Advancing Sustainable Materials Management, Waste Business
Journal tipping fee surveys, industry packaging catalogs.
"""

# --- Disposal costs: USD per ton, US national average ---
TIPPING_FEES = {
    "landfill": 57.0,    # national average landfill tipping fee
    "recycle": 35.0,     # average MRF processing fee (varies widely by market)
    "compost": 30.0,     # average commercial composting fee
    "ewaste": 0.0,       # most business e-waste programs are free drop-off
    "hazardous": 450.0,  # hazmat disposal is expensive — strong incentive to reduce
    "donate": -15.0,     # donations can yield tax deductions (conservative estimate)
    "reuse": -25.0,      # reuse avoids purchase of new packaging/materials
}

# --- Packaging cost comparisons: USD per unit ---
# Format: {material: {unit_cost, recyclable, compostable, notes}}
PACKAGING = {
    "poly_mailer": {
        "unit_cost": 0.18,
        "recyclable": False,
        "compostable": False,
        "notes": "Cheapest upfront; plastic film — landfill only in most areas.",
    },
    "corrugated_mailer": {
        "unit_cost": 0.42,
        "recyclable": True,
        "compostable": True,
        "notes": "Widely recyclable; higher upfront cost, strong sustainability story.",
    },
    "padded_paper_mailer": {
        "unit_cost": 0.35,
        "recyclable": True,
        "compostable": False,
        "notes": "Curbside recyclable paper; good middle ground on cost.",
    },
    "compostable_mailer": {
        "unit_cost": 0.52,
        "recyclable": False,
        "compostable": True,
        "notes": "Certified compostable (BPI); needs commercial composting access.",
    },
    "reused_box": {
        "unit_cost": 0.05,
        "recyclable": True,
        "compostable": True,
        "notes": "Reused inbound boxes; near-zero cost, best sustainability story.",
    },
}

# --- Business archetypes: typical monthly waste profile (lbs) ---
# Used to seed estimates when a business doesn't provide their own numbers.
BUSINESS_PROFILES = {
    "retail": {
        "label": "Retail store",
        "waste_lbs_month": {"cardboard": 800, "plastic_film": 120, "general": 300, "ewaste": 10},
        "notes": "Cardboard-heavy; back-of-house baling common.",
    },
    "restaurant": {
        "label": "Restaurant",
        "waste_lbs_month": {"food_scraps": 1500, "cardboard": 400, "glass": 200, "general": 500},
        "notes": "Food waste is the big lever — composting cuts hauling weight.",
    },
    "office": {
        "label": "Office",
        "waste_lbs_month": {"paper": 300, "general": 400, "ewaste": 25, "food_scraps": 100},
        "notes": "Paper and e-waste dominate; easy wins on both.",
    },
    "warehouse": {
        "label": "Warehouse / fulfillment",
        "waste_lbs_month": {"cardboard": 2500, "plastic_film": 400, "pallets": 300, "general": 600},
        "notes": "Cardboard is revenue-adjacent — baled OCC has resale value.",
    },
    "ecommerce": {
        "label": "E-commerce shipper",
        "waste_lbs_month": {"cardboard": 1200, "plastic_film": 200, "general": 250},
        "notes": "Packaging choice IS the sustainability story for shippers.",
    },
}

# Map waste-profile keys to disposal streams for cost math.
STREAM_MAP = {
    "cardboard": "recycle",
    "plastic_film": "landfill",
    "general": "landfill",
    "food_scraps": "compost",
    "glass": "recycle",
    "paper": "recycle",
    "ewaste": "ewaste",
    "pallets": "reuse",
}


def monthly_disposal_cost(waste_lbs_month):
    """Estimate monthly disposal cost from a {material: lbs} dict.

    Returns {"by_stream": {stream: cost}, "total": float, "notes": [...]}.
    Costs are estimates — see module docstring.
    """
    by_stream = {}
    notes = []
    for material, lbs in waste_lbs_month.items():
        stream = STREAM_MAP.get(material, "landfill")
        tons = lbs / 2000.0
        cost = tons * TIPPING_FEES.get(stream, TIPPING_FEES["landfill"])
        by_stream[stream] = round(by_stream.get(stream, 0.0) + cost, 2)
    total = round(sum(by_stream.values()), 2)
    if total < 0:
        notes.append("Negative cost = net savings from donations/reuse tax benefits.")
    return {"by_stream": by_stream, "total": total, "notes": notes,
            "disclaimer": "Estimates based on US national averages; validate against local hauler rates."}


def packaging_comparison(monthly_shipments, current="poly_mailer"):
    """Compare packaging options for a monthly shipment volume.

    Returns list of options sorted by total monthly cost, each with
    sustainability flags and the delta vs current choice.
    """
    if current not in PACKAGING:
        raise ValueError(f"Unknown packaging: {current}")
    current_monthly = PACKAGING[current]["unit_cost"] * monthly_shipments
    results = []
    for name, spec in PACKAGING.items():
        monthly = spec["unit_cost"] * monthly_shipments
        results.append({
            "material": name,
            "unit_cost": spec["unit_cost"],
            "monthly_cost": round(monthly, 2),
            "delta_vs_current": round(monthly - current_monthly, 2),
            "recyclable": spec["recyclable"],
            "compostable": spec["compostable"],
            "notes": spec["notes"],
        })
    results.sort(key=lambda r: r["monthly_cost"])
    return results


def composting_savings(food_lbs_month):
    """Estimate monthly savings from composting food waste vs landfilling it."""
    tons = food_lbs_month / 2000.0
    landfill_cost = tons * TIPPING_FEES["landfill"]
    compost_cost = tons * TIPPING_FEES["compost"]
    savings = landfill_cost - compost_cost
    return {
        "food_lbs_month": food_lbs_month,
        "landfill_cost": round(landfill_cost, 2),
        "compost_cost": round(compost_cost, 2),
        "monthly_savings": round(savings, 2),
        "annual_savings": round(savings * 12, 2),
    }


def diversion_roi(baseline_rate_pct, target_rate_pct, monthly_tons):
    """Estimate annual savings from improving the diversion rate.

    Assumes diverted tons shift from landfill cost to a blended
    diverted-stream cost (recycle/compost average).
    """
    if not (0 <= baseline_rate_pct <= 100 and 0 <= target_rate_pct <= 100):
        raise ValueError("Rates must be 0-100.")
    if target_rate_pct <= baseline_rate_pct:
        return {"annual_savings": 0.0, "note": "Target must exceed baseline."}
    diverted_cost = (TIPPING_FEES["recycle"] + TIPPING_FEES["compost"]) / 2.0
    tons_shifted = monthly_tons * (target_rate_pct - baseline_rate_pct) / 100.0
    monthly_savings = tons_shifted * (TIPPING_FEES["landfill"] - diverted_cost)
    return {
        "tons_shifted_month": round(tons_shifted, 2),
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(monthly_savings * 12, 2),
    }
