"""SortSmart Business Advisor agent — LLM orchestrated over grounded tools.

Pipeline:
  1. Detect business context + item mentions in the user question.
  2. Run the rule engine (advisor) and business models (costs, scoring).
  3. Inject results as GROUNDED FACTS into the LLM prompt.
  4. Return the LLM's synthesized business advice.

The LLM never invents numbers — all figures come from the deterministic layer.
"""
import re

from sortsmart.advisor import advise
from sortsmart_business.recommendations import business_brief
from sortsmart_business.costs import BUSINESS_PROFILES
from .client import LLMClient
from .prompts import SYSTEM_PROMPT, ADVISOR_PROMPT, build_facts_block


def _detect_business_type(question):
    q = question.lower()
    for key, prof in BUSINESS_PROFILES.items():
        if key in q or prof["label"].lower() in q:
            return key
    # keyword hints
    if any(w in q for w in ("ship", "package", "fulfill", "ecommerce", "e-commerce", "mail")):
        return "ecommerce"
    if any(w in q for w in ("food", "kitchen", "menu", "dine")):
        return "restaurant"
    if any(w in q for w in ("store", "shop", "retail")):
        return "retail"
    if any(w in q for w in ("warehouse", "pallet")):
        return "warehouse"
    return "office"


def _detect_shipments(question):
    m = re.search(r"(\d[\d,]*)\s*(packages?|shipments?|orders?)\s*(a|per)?\s*month", question.lower())
    if m:
        return int(m.group(1).replace(",", ""))
    m = re.search(r"(\d[\d,]*)\s*/\s*mo", question.lower())
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


def _detect_item(question):
    """Naive item extraction: look for 'what about X' / 'where does X go' patterns."""
    patterns = [
        r"(?:what about|where does|how do i (?:dispose of|recycle|handle)|dispose of)\s+([^?.!]+)",
    ]
    for pat in patterns:
        m = re.search(pat, question.lower())
        if m:
            candidate = m.group(1).strip().strip("?.!")
            if 2 < len(candidate) < 60:
                return candidate
    return None


class BusinessAdvisor:
    def __init__(self, llm_client=None):
        self.llm = llm_client or LLMClient()

    def ask(self, question, business_type=None, monthly_shipments=None,
            packaging="poly_mailer"):
        """Answer a business sustainability question with grounded numbers."""
        btype = business_type or _detect_business_type(question)
        shipments = monthly_shipments if monthly_shipments is not None else _detect_shipments(question)

        brief = business_brief(
            business_type=btype,
            monthly_shipments=shipments,
            packaging=packaging,
        )

        item_advice = None
        item = _detect_item(question)
        if item:
            item_advice = advise(item)

        facts = build_facts_block(brief, item_advice)
        prompt = ADVISOR_PROMPT.format(question=question.strip(), facts=facts)

        reply = self.llm.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])

        return {
            "question": question,
            "business_type": btype,
            "answer": reply,
            "grounded": {
                "monthly_disposal_usd": brief["monthly_disposal"]["total"],
                "sustainability_score": brief["sustainability"]["score"],
                "sustainability_grade": brief["sustainability"]["grade"],
                "top_recommendation": brief["recommendations"][0]["action"]
                if brief["recommendations"] else None,
                "item_lookup": {"item": item_advice["item"], "category": item_advice["category"]}
                if item_advice else None,
            },
            "model": repr(self.llm),
        }
