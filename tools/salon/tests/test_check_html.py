"""ブラウザ版 check.html と Python 版 fixed_cost_check.py が同じ判定をすることを確認する（6領域）。"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fixed_cost_check as fc  # noqa: E402

HTML = (ROOT / "check.html").read_text(encoding="utf-8")
BM = json.loads((ROOT / "benchmarks.json").read_text(encoding="utf-8"))


def block(script_id: str) -> str:
    m = re.search(rf'<script id="{script_id}"[^>]*>(.*?)</script>', HTML, re.S)
    assert m, script_id
    return m.group(1)


CASES = [
    json.loads((ROOT / "samples" / "answers_sample.json").read_text(encoding="utf-8")),
    {"salon_name": "a", "monthly_revenue": 1_234_567, "payment": {"cashless_ratio": 0.37, "card_fee_rate": 0.0325, "monthly_fixed_fee": 990},
     "unit_economics": {"avg_ticket": 6000, "visits_first_year": 1.8, "gross_margin": 0.35},
     "media": [{"name": "M1", "monthly_listing_fee": 120000, "new_customers_per_month": 0},
               {"name": "M2", "monthly_listing_fee": 30000, "monthly_variable_fee": 4000, "new_customers_per_month": 3},
               {"name": "M3", "monthly_listing_fee": 10000, "new_customers_per_month": 9}]},
    {"salon_name": "b", "monthly_revenue": 800000, "payment": {"cashless_ratio": 0.5, "card_fee_rate": 0.0248},
     "tools": [{"name": "A", "monthly_fee": 3000, "functions": ["booking", "pos"], "used_last_3_months": True},
               {"name": "B", "monthly_fee": 0, "functions": ["pos"], "used_last_3_months": True},
               {"name": "C", "monthly_fee": 2000, "functions": ["booking"], "used_last_3_months": True}],
     "telecom": {"years_since_review": 2, "lines": [{"name": "L", "monthly_fee": 5000, "in_use": True}]},
     "electricity": {"plan": "x", "monthly_cost": 20000, "monthly_kwh": 0}},
    {"salon_name": "c", "monthly_revenue": 800000, "accounting": {"annual_fee": 240000, "includes_bookkeeping": True, "has_employees": True}},
    {"salon_name": "d", "monthly_revenue": 1500000, "accounting": {"annual_fee": 250000, "includes_bookkeeping": False}},
    {"salon_name": "e", "monthly_revenue": 1500000, "accounting": {"annual_fee": 90000, "includes_bookkeeping": True}},
]


def py_result(a):
    r = fc.run(a, BM)
    return {"items": [[i.area, i.title, i.confidence, i.monthly_low, i.monthly_high] for i in r.items],
            "notes": r.notes, "low": r.monthly_low, "high": r.monthly_high}


@unittest.skipUnless(shutil.which("node"), "node が必要")
class HtmlParityTest(unittest.TestCase):
    def test_benchmarks_embedded_match(self):
        self.assertEqual(json.loads(block("benchmarks")), BM)

    def test_same_results_as_python(self):
        with tempfile.TemporaryDirectory() as d:
            logic = Path(d) / "logic.js"
            logic.write_text(block("logic"), encoding="utf-8")
            runner = Path(d) / "run.js"
            runner.write_text(
                "const {runCheck} = require(process.argv[2]);\n"
                "const bm = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));\n"
                "const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n"
                "console.log(JSON.stringify(cases.map(a => { const r = runCheck(a, bm);\n"
                "  return {items: r.items.map(i => [i.area, i.title, i.confidence, i.monthly_low, i.monthly_high]),\n"
                "          notes: r.notes, low: r.monthly_low, high: r.monthly_high}; })));\n", encoding="utf-8")
            out = subprocess.run(["node", str(runner), str(logic), str(ROOT / "benchmarks.json")],
                                 input=json.dumps(CASES, ensure_ascii=False), capture_output=True, text=True, check=True)
        js = json.loads(out.stdout)
        for case, j in zip(CASES, js):
            p = py_result(case)
            self.assertEqual([x[2:] for x in j["items"]], [x[2:] for x in p["items"]], case["salon_name"])
            self.assertEqual([x[0] for x in j["items"]], [x[0] for x in p["items"]])
            self.assertEqual((j["low"], j["high"]), (p["low"], p["high"]))
            self.assertEqual(len(j["notes"]), len(p["notes"]))


if __name__ == "__main__":
    unittest.main()
