import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fixed_cost_check as fc  # noqa: E402

BM = json.loads((ROOT / "benchmarks.json").read_text(encoding="utf-8"))
SAMPLE = json.loads((ROOT / "samples" / "answers_sample.json").read_text(encoding="utf-8"))


def base(**kw):
    a = {"salon_name": "t", "monthly_revenue": 1_000_000,
         "unit_economics": {"avg_ticket": 8000, "visits_first_year": 3, "gross_margin": 0.5}}
    a.update(kw)
    return a


class SalonCheckTest(unittest.TestCase):
    def areas(self, res):
        return [(i.area, i.confidence) for i in res.items]

    def test_payment_range_uses_benchmarks(self):
        r = fc.run(base(payment={"cashless_ratio": 0.5, "card_fee_rate": 0.0324}), BM)
        it = r.items[0]
        # 500,000 × (3.24−2.98)% = 1,300 ／ 500,000 × (3.24−2.48)% = 3,800
        self.assertEqual((it.monthly_low, it.monthly_high), (1300, 3800))

    def test_payment_already_cheap_gives_note_only(self):
        r = fc.run(base(payment={"cashless_ratio": 0.5, "card_fee_rate": 0.0248}), BM)
        self.assertEqual(r.items, [])
        self.assertTrue(any("見直し余地なし" in n for n in r.notes))

    def test_unused_paid_tool_is_confirmed(self):
        r = fc.run(base(tools=[{"name": "X", "monthly_fee": 3000, "functions": ["pos"], "used_last_3_months": False}]), BM)
        self.assertEqual(self.areas(r), [("予約・POS・SaaS", "確定")])
        self.assertEqual(r.monthly_low, 3000)

    def test_overlap_requires_a_paid_tool(self):
        free_only = [{"name": "A", "monthly_fee": 0, "functions": ["booking"]},
                     {"name": "B", "monthly_fee": 0, "functions": ["booking"]}]
        self.assertEqual(fc.run(base(tools=free_only), BM).items, [])

    def test_electricity_never_claims_saving(self):
        r = fc.run(base(electricity={"monthly_cost": 30000, "monthly_kwh": 1000}), BM)
        self.assertEqual(r.items[0].confidence, "要確認")
        self.assertEqual(r.monthly_high, 0)

    def test_acquisition_flags_only_when_cpa_exceeds_first_year_profit(self):
        ok = fc.run(base(media=[{"name": "M", "monthly_listing_fee": 50000, "new_customers_per_month": 10}]), BM)
        self.assertEqual(ok.items, [])  # CPA 5,000 < 粗利 12,000
        ng = fc.run(base(media=[{"name": "M", "monthly_listing_fee": 150000, "new_customers_per_month": 10}]), BM)
        self.assertEqual(ng.items[0].confidence, "推定")
        self.assertEqual(ng.items[0].monthly_high, 30000)  # (15,000−12,000)×10

    def test_unused_tool_not_double_counted_as_overlap(self):
        tools = [{"name": "A", "monthly_fee": 9800, "functions": ["messaging"], "used_last_3_months": True},
                 {"name": "D", "monthly_fee": 5500, "functions": ["messaging"], "used_last_3_months": False}]
        r = fc.run(base(tools=tools), BM)
        self.assertEqual([i.confidence for i in r.items], ["確定"])
        self.assertEqual(r.monthly_high, 5500)

    def test_sample_report_renders(self):
        r = fc.run(SAMPLE, BM)
        md = fc.render_md(r, BM, 19800)
        self.assertIn("見直し余地の目安", md)
        self.assertGreater(r.monthly_high, 0)


if __name__ == "__main__":
    unittest.main()
