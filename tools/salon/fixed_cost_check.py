"""サロン固定費・集客費チェック（MVP・決定論的）

オーナーが質問票（約5分）に答えた数値だけで判定する。請求書の提出・AIへの顧客データ入力は不要。
数値は推測で埋めない。ベンチマークは benchmarks.json（出典・確認日つき）からのみ使う。

    python3 tools/salon/fixed_cost_check.py --input tools/salon/samples/answers_sample.json
    python3 tools/salon/fixed_cost_check.py --input answers.json --out-md report.md --out-json result.json

判定する5領域：
  1. キャッシュレス決済手数料（料率差 × キャッシュレス売上）
  2. 予約・POS・SaaS の機能重複と未使用
  3. 通信（固定電話・回線の本数と用途）
  4. 電気（kWh単価の算出のみ。比較は要確認として人が行う）
  5. 集客媒体の費用対効果（新規1人あたり獲得コスト vs 新規客の1年目の粗利）
  6. 税理士・記帳の費用（記帳込みの契約 vs 会計アプリで記帳＋申告のみの相場）
     ※ 税務相談・税務判断はしない（税理士法52条）。相場との比較だけを示す
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent


@dataclass
class Item:
    area: str
    title: str
    confidence: str           # 確定（計算のみ）/ 推定（条件変更が前提）/ 要確認（人が比較）
    monthly_low: int          # 見直し余地の下限（円/月）
    monthly_high: int         # 上限
    basis: str                # 計算根拠（式と入力値）
    action: str               # オーナー自身が行うこと
    caution: str = ""         # 業務影響・契約上の注意


@dataclass
class Result:
    salon: str
    items: list[Item] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def monthly_low(self) -> int:
        return sum(i.monthly_low for i in self.items)

    @property
    def monthly_high(self) -> int:
        return sum(i.monthly_high for i in self.items)


def _r(v: float) -> int:
    """100円単位に四捨五入（精度を装わない）。ブラウザ版 check.html と同じ丸め方にする。"""
    return int(v / 100.0 + 0.5) * 100 if v >= 0 else -int(-v / 100.0 + 0.5) * 100


def check_payment(a: dict, bm: dict, res: Result) -> None:
    p = a.get("payment")
    if not p:
        res.notes.append("決済：未回答のため判定なし")
        return
    cashless = a["monthly_revenue"] * p["cashless_ratio"]
    cur = p["card_fee_rate"]
    low_rate, high_rate = bm["payment"]["alt_rate_high"], bm["payment"]["alt_rate_low"]
    diff_low = max(cur - low_rate, 0)   # 保守的な代替料率との差
    diff_high = max(cur - high_rate, 0)
    fixed = p.get("monthly_fixed_fee", 0)
    lo, hi = _r(cashless * diff_low), _r(cashless * diff_high + fixed)
    if hi <= 0:
        res.notes.append(f"決済：現在の料率 {cur:.2%} は比較対象の範囲内。見直し余地なし")
        return
    res.items.append(Item(
        "決済", "キャッシュレス決済手数料の料率見直し", "推定", lo, hi,
        f"キャッシュレス売上 {cashless:,.0f}円/月 ×（現在 {cur:.2%} − 比較料率 {high_rate:.2%}〜{low_rate:.2%}）"
        + (f" ＋ 月額固定費 {fixed:,}円" if fixed else ""),
        "利用中の決済サービスの手数料プラン・中小事業者向けプログラムの有無を確認し、他サービスの料率と比較する",
        "端末の買い替え・入金サイクル・対応ブランド・既存契約の解約条件を確認。料率の税区分（税込/非課税）をそろえて比較する",
    ))


def check_saas(a: dict, bm: dict, res: Result) -> None:
    tools = a.get("tools", [])
    # 未使用の有料ツールは「確定」で別に計上するため、重複判定から除く（二重計上防止）
    active = [t for t in tools if not (t.get("monthly_fee", 0) > 0 and t.get("used_last_3_months") is False)]
    by_func: dict[str, list[dict]] = {}
    for t in active:
        for f in t.get("functions", []):
            by_func.setdefault(f, []).append(t)
    seen: set[str] = set()
    for func, ts in sorted(by_func.items()):
        paid = [t for t in ts if t.get("monthly_fee", 0) > 0]
        if len(ts) >= 2 and paid:
            cheapest_paid = min(t["monthly_fee"] for t in paid)
            names = "・".join(t["name"] for t in ts)
            key = func + names
            if key in seen:
                continue
            seen.add(key)
            res.items.append(Item(
                "予約・POS・SaaS", f"「{bm['functions'].get(func, func)}」の機能が重複（{names}）", "推定",
                0, cheapest_paid,
                f"同じ機能を持つツールが{len(ts)}つ。うち有料の最安 {cheapest_paid:,}円/月",
                "どのツールで代替できるかを確認し、不要な方の解約・プラン変更を検討する",
                "顧客カルテ・予約データの移行、スタッフの操作変更、解約月・最低利用期間を確認",
            ))
    for t in tools:
        if t.get("monthly_fee", 0) > 0 and t.get("used_last_3_months") is False:
            res.items.append(Item(
                "予約・POS・SaaS", f"直近3か月使っていない有料ツール（{t['name']}）", "確定",
                t["monthly_fee"], t["monthly_fee"],
                f"月額 {t['monthly_fee']:,}円、直近3か月の利用なし（オーナー回答）",
                "解約またはプラン変更", "データのエクスポートが必要か確認",
            ))


def check_telecom(a: dict, bm: dict, res: Result) -> None:
    tc = a.get("telecom")
    if not tc:
        return
    unused = [l for l in tc.get("lines", []) if l.get("in_use") is False]
    for l in unused:
        res.items.append(Item(
            "通信", f"使っていない回線（{l['name']}）", "確定", l["monthly_fee"], l["monthly_fee"],
            f"月額 {l['monthly_fee']:,}円、利用なし（オーナー回答）", "解約", "電話番号を残す必要があるか確認",
        ))
    years = tc.get("years_since_review")
    total = sum(l["monthly_fee"] for l in tc.get("lines", []) if l.get("in_use") is not False)
    if years is not None and years >= bm["telecom"]["review_after_years"] and total > 0:
        res.items.append(Item(
            "通信", f"{years}年以上プランを見直していない回線（合計 {total:,}円/月）", "要確認", 0, 0,
            "見直し余地は契約内容次第のため金額は計上しない",
            "現在のプラン名・割引の適用状況を確認し、同等サービスの現行プランと比較する",
            "契約期間・解約金、工事費の残債を確認",
        ))


def check_electricity(a: dict, bm: dict, res: Result) -> None:
    e = a.get("electricity")
    if not e:
        return
    unit = e["monthly_cost"] / e["monthly_kwh"] if e.get("monthly_kwh") else None
    if unit is None:
        res.notes.append("電気：使用量(kWh)が未回答のため単価を算出できない")
        return
    res.items.append(Item(
        "電気", f"電気の実質単価 {unit:.1f}円/kWh（{e.get('plan', 'プラン不明')}）", "要確認", 0, 0,
        f"月額 {e['monthly_cost']:,}円 ÷ {e['monthly_kwh']:,}kWh。燃料費調整額・支援策で毎月変動するため削減額は計上しない",
        "同じ月の検針票で、地域の電力会社の標準メニューと料金を比較する",
        bm["electricity"]["caution"],
    ))


def check_acquisition(a: dict, bm: dict, res: Result) -> None:
    for m in a.get("media", []):
        new = m.get("new_customers_per_month") or 0
        cost = m["monthly_listing_fee"] + m.get("monthly_variable_fee", 0)
        if new <= 0:
            res.items.append(Item(
                "集客", f"{m['name']}：新規来店が0人/月（月 {cost:,}円）", "要確認", 0, cost,
                f"掲載費等 {cost:,}円/月 ÷ 新規 0人", "掲載プラン・掲載内容の見直し、またはプラン縮小を検討",
                "掲載をやめると予約導線がなくなる。既存客の予約経路も確認する",
            ))
            continue
        cpa = cost / new
        u = a["unit_economics"]
        first_year_gp = u["avg_ticket"] * u["visits_first_year"] * u["gross_margin"]
        if cpa > first_year_gp:
            excess = _r((cpa - first_year_gp) * new)
            res.items.append(Item(
                "集客", f"{m['name']}：新規1人あたり獲得コスト {cpa:,.0f}円 ＞ 新規客の1年目の粗利 {first_year_gp:,.0f}円",
                "推定", 0, excess,
                f"（掲載費等 {cost:,}円 ÷ 新規 {new}人）vs（客単価 {u['avg_ticket']:,}円 × 1年目の来店 {u['visits_first_year']}回 × 粗利率 {u['gross_margin']:.0%}）",
                "掲載プラン・クーポン・掲載エリアの見直し。プラン縮小時の新規数の減少を試算してから判断",
                "新規数が減ると売上も減る。上限額は「粗利を超えて払っている額」であり、そのまま削減できる額ではない",
            ))
        else:
            res.notes.append(f"集客：{m['name']} は新規1人あたり {cpa:,.0f}円で、1年目の粗利 {first_year_gp:,.0f}円 以内")


def check_accounting(a: dict, bm: dict, res: Result) -> None:
    ac = a.get("accounting")
    if not ac or not ac.get("annual_fee"):
        return
    b = bm["accounting"]
    fee = ac["annual_fee"]
    annual_revenue = a.get("monthly_revenue", 0) * 12
    band = next((x for x in b["spot_filing_bands"] if annual_revenue < x["revenue_under"]), None)
    if band is None:
        res.items.append(Item(
            "税理士・記帳", f"税理士への支払い 年{fee:,}円（年商 {annual_revenue:,}円）", "要確認", 0, 0,
            "この年商帯の比較相場を持っていないため金額は計上しない",
            "契約の内訳（記帳代行・申告・相談）を確認し、必要なら複数の事務所から見積を取る", b["caution"]))
        return
    if not ac.get("includes_bookkeeping"):
        if fee > band["high"]:
            res.items.append(Item(
                "税理士・記帳", f"申告のみの契約で年{fee:,}円（相場 {band['low']:,}〜{band['high']:,}円）", "要確認", 0, 0,
                "相場より高いが、契約内容（相談・届出・その他業務）次第のため金額は計上しない",
                "契約の内訳を確認する", b["caution"]))
        else:
            res.notes.append(f"税理士・記帳：申告のみの契約で年{fee:,}円。相場（{band['low']:,}〜{band['high']:,}円）の範囲内")
        return
    alt_low = b["app_annual_low"] + band["low"]
    alt_high = b["app_annual_high"] + band["high"]
    if fee <= alt_low:
        res.notes.append(f"税理士・記帳：記帳込みで年{fee:,}円。会計アプリ＋申告のみの目安（年{alt_low:,}〜{alt_high:,}円）以下")
        return
    lo, hi = _r(max(fee - alt_high, 0) / 12), _r((fee - alt_low) / 12)
    res.items.append(Item(
        "税理士・記帳", f"記帳代行込みの税理士契約 年{fee:,}円 → 会計アプリで自分で記帳＋申告のみ依頼", "推定", lo, hi,
        f"現在 年{fee:,}円 −（会計アプリ 年{b['app_annual_low']:,}〜{b['app_annual_high']:,}円 ＋ 申告のみの相場 年{band['low']:,}〜{band['high']:,}円）を12で割った額",
        "レシート・カード・口座の記録を会計アプリで自分で行い、税理士には申告（と確認）だけを依頼する形の見積を、今の税理士と他の事務所から取る",
        b["caution"] + ("。従業員の給与計算・年末調整の費用は別途確認" if ac.get("has_employees") else "")))


def run(answers: dict, bm: dict) -> Result:
    res = Result(answers.get("salon_name", "（サロン名）"))
    for fn in (check_payment, check_saas, check_telecom, check_electricity, check_acquisition, check_accounting):
        fn(answers, bm, res)
    return res


def render_md(res: Result, bm: dict, price: int) -> str:
    lines = [f"# 固定費・集客費チェック 結果：{res.salon}", "",
             "> ご回答の数値にもとづく機械的な判定です。見直しの判断・実行はお客様ご自身で行ってください。"
             "当方は契約先との交渉・手続きの代行は行いません。金額は目安で、削減を保証するものではありません。", "",
             f"- 見直し余地の目安：**月 {res.monthly_low:,}〜{res.monthly_high:,}円**（年 {res.monthly_low*12:,}〜{res.monthly_high*12:,}円）",
             f"- 「確定」項目の合計：月 {sum(i.monthly_low for i in res.items if i.confidence == '確定'):,}円", ""]
    if price and res.monthly_high * 12 < price:
        lines += [f"**見直し余地の上限（年 {res.monthly_high*12:,}円）が診断料 {price:,}円 を下回るため、返金保証の対象です。**", ""]
    lines += ["| 領域 | 項目 | 確度 | 月の目安 | 根拠 | お客様が行うこと | 注意 |", "|---|---|---|---:|---|---|---|"]
    for i in res.items:
        if not i.monthly_high:
            amt = "—"
        elif i.monthly_low == i.monthly_high:
            amt = f"{i.monthly_high:,}"
        else:
            amt = f"{i.monthly_low:,}〜{i.monthly_high:,}"
        lines.append(f"| {i.area} | {i.title} | {i.confidence} | {amt} | {i.basis} | {i.action} | {i.caution} |")
    if res.notes:
        lines += ["", "## 問題が見つからなかった項目・判定できなかった項目", ""] + [f"- {n}" for n in res.notes]
    lines += ["", "## 比較に使った基準値", ""]
    for k, v in bm["sources"].items():
        lines.append(f"- {k}：{v}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--benchmarks", type=Path, default=HERE / "benchmarks.json")
    ap.add_argument("--price", type=int, default=19_800, help="診断料（返金保証の判定に使う）")
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--out-json", type=Path)
    a = ap.parse_args()
    bm = json.loads(a.benchmarks.read_text(encoding="utf-8"))
    res = run(json.loads(a.input.read_text(encoding="utf-8")), bm)
    md = render_md(res, bm, a.price)
    if a.out_md:
        a.out_md.write_text(md, encoding="utf-8")
    else:
        print(md)
    if a.out_json:
        a.out_json.write_text(json.dumps({"salon": res.salon, "monthly_low": res.monthly_low,
                                          "monthly_high": res.monthly_high,
                                          "items": [asdict(i) for i in res.items], "notes": res.notes},
                                         ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
