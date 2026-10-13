"""Tests for SortSmart Business Advisor (no LLM needed for most)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sortsmart_business.costs import (
    monthly_disposal_cost, packaging_comparison, composting_savings,
    diversion_roi, BUSINESS_PROFILES, PACKAGING,
)
from sortsmart_business.scoring import score_business
from sortsmart_business.recommendations import business_brief
from sortsmart_llm.client import LLMClient


class TestCosts(unittest.TestCase):
    def test_monthly_disposal_cost(self):
        r = monthly_disposal_cost({"cardboard": 800, "general": 300})
        self.assertGreater(r["total"], 0)
        self.assertIn("recycle", r["by_stream"])
        self.assertIn("landfill", r["by_stream"])

    def test_packaging_comparison_sorted(self):
        opts = packaging_comparison(2000, current="poly_mailer")
        costs = [o["monthly_cost"] for o in opts]
        self.assertEqual(costs, sorted(costs))
        cur = next(o for o in opts if o["material"] == "poly_mailer")
        self.assertEqual(cur["delta_vs_current"], 0.0)

    def test_packaging_unknown_raises(self):
        with self.assertRaises(ValueError):
            packaging_comparison(100, current="nope")

    def test_composting_savings(self):
        r = composting_savings(1500)
        self.assertGreater(r["annual_savings"], 0)
        self.assertAlmostEqual(r["monthly_savings"] * 12, r["annual_savings"], places=1)

    def test_diversion_roi(self):
        r = diversion_roi(25, 55, 2.0)
        self.assertGreater(r["annual_savings"], 0)

    def test_diversion_roi_no_gain(self):
        r = diversion_roi(50, 40, 2.0)
        self.assertEqual(r["annual_savings"], 0.0)

    def test_profiles_valid(self):
        for key, prof in BUSINESS_PROFILES.items():
            self.assertIn("waste_lbs_month", prof)
            self.assertTrue(prof["waste_lbs_month"])


class TestScoring(unittest.TestCase):
    def test_perfect_score(self):
        s = score_business({
            "diversion_rate_pct": 100, "packaging": "reused_box",
            "composts_food": True, "ewaste_program": True, "hazmat_program": True,
        })
        self.assertEqual(s["score"], 100)
        self.assertEqual(s["grade"], "A")

    def test_terrible_score(self):
        s = score_business({
            "diversion_rate_pct": 0, "packaging": "poly_mailer",
            "business_type": "restaurant",
        })
        self.assertLess(s["score"], 30)
        self.assertEqual(s["grade"], "F")
        self.assertTrue(len(s["top_levers"]) > 0)

    def test_score_bounds(self):
        for div in (0, 25, 50, 75, 100):
            s = score_business({"diversion_rate_pct": div})
            self.assertTrue(0 <= s["score"] <= 100)


class TestBrief(unittest.TestCase):
    def test_ecommerce_brief(self):
        b = business_brief(business_type="ecommerce", monthly_shipments=2000)
        self.assertIn("recommendations", b)
        self.assertTrue(len(b["recommendations"]) > 0)
        self.assertIn("sustainability", b)
        rec = b["recommendations"][0]
        self.assertIn("action", rec)
        self.assertIn("annual_cost_delta", rec)

    def test_restaurant_brief_has_composting(self):
        b = business_brief(business_type="restaurant")
        actions = " ".join(r["action"].lower() for r in b["recommendations"])
        self.assertIn("compost", actions)


class TestLLMClient(unittest.TestCase):
    def test_mock_mode(self):
        os.environ["LLM_MOCK"] = "true"
        try:
            c = LLMClient()
            reply = c.chat([{"role": "user", "content": "GROUNDED FACTS: test"}])
            self.assertIn("MOCK", reply)
        finally:
            del os.environ["LLM_MOCK"]

    def test_missing_config_raises(self):
        for var in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_MOCK"):
            os.environ.pop(var, None)
        with self.assertRaises(Exception):
            LLMClient()


if __name__ == "__main__":
    unittest.main(verbosity=2)
