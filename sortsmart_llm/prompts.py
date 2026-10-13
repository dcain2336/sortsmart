"""Prompt templates for the SortSmart Business Advisor persona."""

SYSTEM_PROMPT = """You are the SortSmart Business Advisor, an AI consultant that helps \
businesses cut waste costs and improve sustainability. You combine a verified \
rule-based waste knowledge engine with live cost models.

Rules you MUST follow:
1. Every dollar figure you cite MUST come from the GROUNDED FACTS section — \
never invent costs, savings, or rates.
2. Always label estimates as estimates and note they are US national averages.
3. Be concrete and commercial: lead with the money, then the planet.
4. Keep answers focused — 3 recommendations max, each with a dollar figure.
5. If the grounded facts don't cover the question, say so and give the closest \
relevant guidance, clearly marked as general advice.
6. Never recommend anything illegal or unsafe. Hazardous waste always goes to \
licensed collection.
"""

ADVISOR_PROMPT = """Answer the business question below using ONLY the grounded facts \
provided. Follow the system rules strictly.

BUSINESS QUESTION:
{question}

GROUNDED FACTS (from SortSmart rule engine + cost models — treat as authoritative):
{facts}

Write your answer as:
1. A one-line bottom line with the biggest dollar figure.
2. Up to 3 ranked recommendations, each with: action, estimated annual dollar \
impact, and one sentence of why.
3. One line on what data would sharpen these estimates (e.g. actual hauler rates).
"""


def build_facts_block(brief, item_advice=None):
    """Render the business brief + optional item advice as a facts block."""
    lines = []
    lines.append(f"Business type: {brief['business_type']}")
    disp = brief["monthly_disposal"]
    lines.append(f"Estimated monthly disposal cost: ${disp['total']:.2f} "
                 f"(by stream: {', '.join(f'{k} ${v:.2f}' for k, v in disp['by_stream'].items())})")
    s = brief["sustainability"]
    lines.append(f"Sustainability score: {s['score']}/100 (grade {s['grade']})")
    lines.append("Recommendations (pre-computed):")
    for r in brief["recommendations"][:5]:
        delta = r["annual_cost_delta"]
        money = (f"saves ~${-delta:,.0f}/yr" if delta is not None and delta < 0
                 else f"costs ~${delta:,.0f}/yr" if delta is not None and delta > 0
                 else "cost impact not modeled")
        lines.append(f"  - {r['action']} — {money}. {r['impact']}")
    if item_advice:
        lines.append("Item lookup:")
        lines.append(f"  - '{item_advice['item']}' -> {item_advice['label']} "
                     f"(confidence {item_advice['confidence']}). Why: {item_advice['why']}")
    lines.append("Assumption: " + brief["assumptions"])
    return "\n".join(lines)
