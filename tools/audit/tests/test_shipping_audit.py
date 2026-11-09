import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import shipping_audit as sa  # noqa: E402

RATECARD = json.loads((ROOT / "samples" / "ratecard_sample.json").read_text(encoding="utf-8"))


def row(tn, size="60", charged=720, dims=("30", "20", "8"), w="1.2", pref="東京都"):
    return dict(tracking_no=tn, ship_date="2026-10-01", carrier="宅配便A", service="通常",
                billed_size=size, weight_kg=w, length_cm=dims[0], width_cm=dims[1],
                height_cm=dims[2], dest_pref=pref, charged_yen=str(charged))


class AuditTest(unittest.TestCase):
    def kinds(self, rows):
        return [f.kind for f in sa.audit(rows, RATECARD)]

    def test_clean_row_has_no_finding(self):
        self.assertEqual(self.kinds([row("A1")]), [])

    def test_duplicate_charge(self):
        fs = sa.audit([row("A1"), row("A1")], RATECARD)
        self.assertEqual([f.kind for f in fs], ["DUPLICATE_CHARGE"])
        self.assertEqual(fs[0].diff_yen, 720)

    def test_over_contract_rate_uses_prefecture_price(self):
        self.assertEqual(self.kinds([row("A1", charged=1150, pref="北海道")]), [])
        fs = sa.audit([row("A1", charged=1200, pref="北海道")], RATECARD)
        self.assertEqual(fs[0].kind, "OVER_CONTRACT_RATE")
        self.assertEqual(fs[0].diff_yen, 50)

    def test_size_overbilled(self):
        fs = sa.audit([row("A1", size="100", charged=1180, dims=("35", "25", "15"), w="3")], RATECARD)
        self.assertEqual(fs[0].kind, "SIZE_OVERBILLED")
        self.assertEqual(fs[0].expected_yen, 930)  # 75cm/3kg → 80サイズ

    def test_weight_drives_size(self):
        # 3辺60cm以内でも 4kg なら 80サイズが正しい → 指摘なし
        self.assertEqual(self.kinds([row("A1", size="80", charged=930, dims=("30", "20", "8"), w="4")]), [])

    def test_small_packet_candidate(self):
        fs = sa.audit([row("A1", dims=("32", "23", "2.5"), w="0.4")], RATECARD)
        self.assertEqual(fs[0].kind, "SMALL_PACKET_ELIGIBLE")
        self.assertEqual(fs[0].diff_yen, 720 - 330)

    def test_missing_dims_only_checks_price(self):
        self.assertEqual(self.kinds([row("A1", dims=("", "", ""), w="")]), [])

    def test_summary_monthly_normalisation(self):
        rows = [row("A1"), row("A1")]
        s = sa.summarize(rows, sa.audit(rows, RATECARD), months=2)
        self.assertEqual(s["by_kind"]["DUPLICATE_CHARGE"]["monthly_yen"], 360)
        self.assertEqual(s["confirmed_yen"], 720)


class InputValidationTest(unittest.TestCase):
    def run_audit(self, rows):
        issues = []
        fs = sa.audit(rows, RATECARD, issues)
        return fs, issues

    def test_non_numeric_charge_is_error_and_skipped(self):
        fs, issues = self.run_audit([row("A1", charged="abc"), row("A1")])
        self.assertEqual(fs, [])  # 不正行は重複判定にも使わない
        self.assertEqual([i.level for i in issues], ["ERROR"])
        self.assertEqual(issues[0].line, 2)

    def test_missing_tracking_no_is_error(self):
        _, issues = self.run_audit([row("")])
        self.assertTrue(any(i.level == "ERROR" and "追跡番号" in i.message for i in issues))

    def test_unknown_service_is_warning_not_crash(self):
        r = row("A1")
        r["service"] = "クール"
        fs, issues = self.run_audit([r])
        self.assertEqual(fs, [])
        self.assertTrue(any(i.level == "WARN" and "契約運賃表" in i.message for i in issues))

    def test_partial_dims_warns_and_skips_size_checks(self):
        fs, issues = self.run_audit([row("A1", size="100", charged=1180, dims=("35", "", "15"), w="3")])
        self.assertEqual(fs, [])
        self.assertTrue(any("一部のみ" in i.message for i in issues))

    def test_comma_formatted_amount_is_accepted(self):
        fs, issues = self.run_audit([row("A1", charged="1,200", pref="北海道")])
        self.assertEqual(issues, [])
        self.assertEqual(fs[0].diff_yen, 50)

    def test_summary_counts_issues_and_ignores_bad_amounts(self):
        rows = [row("A1", charged="abc"), row("A2")]
        issues = []
        fs = sa.audit(rows, RATECARD, issues)
        s = sa.summarize(rows, fs, 1, issues)
        self.assertEqual(s["input_errors"], 1)
        self.assertEqual(s["total_charged_yen"], 720)


if __name__ == "__main__":
    unittest.main()
