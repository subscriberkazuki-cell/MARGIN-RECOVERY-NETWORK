"""MARGIN RECOVERY NETWORK 収益シミュレーション（決定論的計算）

使い方:
    python3 finance/simulate.py            # Markdown を標準出力
    python3 finance/simulate.py > docs/05_収益シミュレーション_結果.md

すべての前提値は仮説。実績データが出たら SCENARIOS を更新して再実行する。
金額は円・月次。
"""
from __future__ import annotations

from dataclasses import dataclass, replace

TARGET_PROFIT = 500_000


@dataclass(frozen=True)
class Scenario:
    name: str
    # --- 直接営業ファネル ---
    contacts: int            # 月間アプローチ数（法令上送信可能と確認済みの宛先のみ）
    reply_rate: float        # 返信率
    meeting_rate: float      # 返信→商談
    diag_rate: float         # 商談→無料診断の実施
    # --- 提携チャネル ---
    partner_diags: float     # 提携先からの月間診断件数
    partner_fee_share: float # 提携先に支払う紹介料（当社成功報酬に対する比率）
    # --- 共通 ---
    contract_rate: float     # 診断→本監査契約
    success_rate: float      # 本監査→削減実現
    monthly_saving: int      # 成功顧客1社あたり月間削減額（単価差×実数量）
    fee_rate: float          # 成功報酬率
    fee_months: int          # 成功報酬の算定月数
    bad_debt: float          # 未回収率
    watch_conv: float        # 成功顧客→MARGIN WATCH 移行率
    watch_price: int         # MARGIN WATCH 月額
    watch_churn: float       # MARGIN WATCH 月次解約率
    hours_meeting: float = 1.0  # 1商談の人手時間（準備含む）
    hours_sales_ops: float = 20.0  # 月間の営業運用時間（リスト確認・送信承認・返信対応）
    hours_diag: float = 1.0  # 1診断の人手時間（AI前処理後）
    hours_audit: float = 6.0 # 1本監査の人手時間
    hours_success: float = 4.0  # 変更支援・効果検証の人手時間
    var_cost_audit: int = 3_000   # AI/API/OCR 等の1監査あたり変動費
    sales_cost: int = 30_000      # 月間営業ツール費（メール配信・リスト等）
    fixed_cost: int = 60_000      # 月間固定費（Workspace/ドメイン/ホスティング/会計/保険等）


def funnel(s: Scenario) -> dict:
    replies = s.contacts * s.reply_rate
    meetings = replies * s.meeting_rate
    direct_diags = meetings * s.diag_rate
    diags = direct_diags + s.partner_diags
    audits = diags * s.contract_rate
    successes = audits * s.success_rate
    partner_successes = s.partner_diags * s.contract_rate * s.success_rate
    fee_per_success = s.monthly_saving * s.fee_months * s.fee_rate
    fee_rev = successes * fee_per_success * (1 - s.bad_debt)
    partner_payout = partner_successes * fee_per_success * s.partner_fee_share * (1 - s.bad_debt)
    # MARGIN WATCH 定常状態の契約数 = 月間新規 / 解約率
    watch_new = successes * s.watch_conv
    watch_subs_ss = watch_new / s.watch_churn if s.watch_churn else 0
    watch_rev_ss = watch_subs_ss * s.watch_price
    hours = s.hours_sales_ops + meetings * s.hours_meeting + diags * s.hours_diag + audits * s.hours_audit + successes * s.hours_success
    var_cost = audits * s.var_cost_audit + watch_subs_ss * 500  # WATCH 1社あたり処理費 500円
    cost = var_cost + s.sales_cost + s.fixed_cost + partner_payout
    profit_ss = fee_rev + watch_rev_ss - cost
    # 目標利益達成に必要な月間成功件数（保守的に WATCH 収益を含めない）
    partner_ratio = s.partner_diags / diags if diags else 0
    per_success_net = fee_per_success * (1 - s.bad_debt) * (1 - partner_ratio * s.partner_fee_share) \
        - s.var_cost_audit / s.success_rate
    need_success = (TARGET_PROFIT + s.sales_cost + s.fixed_cost) / per_success_net
    return dict(
        replies=replies, meetings=meetings, diags=diags, audits=audits,
        successes=successes, fee_per_success=fee_per_success, fee_rev=fee_rev,
        partner_payout=partner_payout, watch_subs_ss=watch_subs_ss,
        watch_rev_ss=watch_rev_ss, hours=hours, cost=cost, profit_ss=profit_ss,
        gross_margin=(fee_rev + watch_rev_ss - var_cost - partner_payout)
        / max(fee_rev + watch_rev_ss, 1),
        need_success=need_success,
    )


def ramp(s: Scenario, months: int = 18, start_delay: int = 2, lag: int = 3) -> list[dict]:
    """月次の立ち上がり（2026-11-10 経営判断を反映）。

    - 最初の start_delay か月はヒアリング・弁護士レビュー期間で営業ファネルなし（固定費のみ）
    - 営業開始後のファネル量は 40% → 70% → 100% で立ち上がる
    - 診断から削減が実請求に反映されるまで lag か月
    - 成功報酬は「実際に反映された削減額 × 25%」を反映月の翌月から最大 fee_months か月、毎月後払いで受領
      （一括請求しない。月次の削減額は monthly_saving で一定と仮定）
    """
    f = funnel(s)
    horizon = months + lag + s.fee_months + 2
    ramp_factor = [0.0] * start_delay + [0.4, 0.7] + [1.0] * horizon
    succ_by_month = [0.0] * horizon
    for m in range(months):
        if m + lag < horizon:
            succ_by_month[m + lag] += f["successes"] * ramp_factor[m]
    monthly_fee_unit = s.monthly_saving * s.fee_rate * (1 - s.bad_debt)
    partner_ratio = (s.partner_diags / f["diags"]) if f["diags"] else 0
    rows, watch_subs, cum = [], 0.0, 0.0
    for m in range(months):
        # 反映月 k の顧客は k+1 〜 k+fee_months 月に報酬を支払う
        paying = sum(succ_by_month[k] for k in range(max(0, m - s.fee_months), m))
        fee = paying * monthly_fee_unit
        watch_subs = watch_subs * (1 - s.watch_churn) + succ_by_month[m] * s.watch_conv
        watch = watch_subs * s.watch_price
        audits = f["audits"] * ramp_factor[m]
        sales_cost = s.sales_cost if m >= start_delay else 0
        cost = (audits * s.var_cost_audit + watch_subs * 500 + sales_cost + s.fixed_cost
                + fee * partner_ratio * s.partner_fee_share)
        profit = fee + watch - cost
        cum += profit
        rows.append(dict(month=m + 1, fee=fee, watch=watch, cost=cost, profit=profit, cum=cum,
                         watch_subs=watch_subs, paying=paying))
    return rows


# ------------------------------------------------------------------
# 前提値（すべて仮説。初期ターゲット = 年商1〜10億円のEC事業者）
# ------------------------------------------------------------------
BASE = dict(partner_fee_share=0.2, fee_rate=0.25, fee_months=12, bad_debt=0.05)

EC_PESSIMISTIC = Scenario(
    "悲観", contacts=300, reply_rate=0.015, meeting_rate=0.5, diag_rate=0.7,
    partner_diags=0.5, contract_rate=0.35, success_rate=0.65, monthly_saving=50_000,
    watch_conv=0.25, watch_price=19_800, watch_churn=0.06, **BASE)
EC_STANDARD = Scenario(
    "標準", contacts=500, reply_rate=0.03, meeting_rate=0.5, diag_rate=0.7,
    partner_diags=2, contract_rate=0.5, success_rate=0.8, monthly_saving=80_000,
    watch_conv=0.4, watch_price=19_800, watch_churn=0.04, **BASE)
EC_OPTIMISTIC = Scenario(
    "楽観", contacts=600, reply_rate=0.04, meeting_rate=0.55, diag_rate=0.75,
    partner_diags=3, contract_rate=0.6, success_rate=0.85, monthly_saving=120_000,
    watch_conv=0.5, watch_price=19_800, watch_churn=0.03, **BASE)

# 収益モデル比較（標準シナリオを基準に変形）
MODELS = {
    "成功報酬中心（WATCHなし）": replace(EC_STANDARD, name="成功報酬中心", watch_conv=0.0),
    "成功報酬＋月額（推奨）": EC_STANDARD,
    "直接営業中心（提携ゼロ）": replace(EC_STANDARD, name="直接営業中心", partner_diags=0),
    "代理店経由中心": replace(EC_STANDARD, name="代理店経由中心", contacts=100, partner_diags=6,
                       sales_cost=10_000),
    "月額課金中心（美容室・3,980円）": replace(
        EC_STANDARD, name="月額中心(美容室)", contacts=800, reply_rate=0.02, partner_diags=3,
        monthly_saving=20_000, watch_conv=0.6, watch_price=3_980, watch_churn=0.05),
}

# 比較用：美容室（1〜3店舗）を初期市場にした場合の標準シナリオ
SALON_STANDARD = replace(
    EC_STANDARD, name="美容室・標準", contacts=500, reply_rate=0.02, partner_diags=2,
    monthly_saving=20_000, watch_conv=0.5, watch_price=3_980, watch_churn=0.05,
    hours_audit=4.0, hours_success=3.0)


def yen(v: float) -> str:
    return f"{v:,.0f}"


def render() -> str:
    out = ["# 収益シミュレーション結果（自動生成）",
           "",
           "> `python3 finance/simulate.py` で再生成。前提値はすべて仮説であり、実績で置き換える。",
           "> 定常状態 = 立ち上がり完了後に毎月同じ件数が流れ続けた場合の月次値。MARGIN WATCH は 新規/解約率 で収束した契約数で、到達には数年かかる。",
           "> **意思決定には「12か月目・18か月目」と「WATCH除外」の数字を使うこと**（収束値は上限の目安）。",
           "> 成功報酬は月次後払い（最大12か月）のため、定常状態の売上は営業開始から約15か月後に到達する。",
           "> 本シミュレーションは経営目標の試算であり、予測実績として外部に表示しない。",
           ""]
    out += ["## 1. EC事業者・3シナリオ（定常状態）", "",
            "| 指標 | " + " | ".join(s.name for s in (EC_PESSIMISTIC, EC_STANDARD, EC_OPTIMISTIC)) + " |",
            "|---|---:|---:|---:|"]
    fs = [funnel(s) for s in (EC_PESSIMISTIC, EC_STANDARD, EC_OPTIMISTIC)]
    ss = (EC_PESSIMISTIC, EC_STANDARD, EC_OPTIMISTIC)
    rows = [
        ("月間アプローチ数", lambda s, f: yen(s.contacts)),
        ("返信率", lambda s, f: f"{s.reply_rate:.1%}"),
        ("返信数", lambda s, f: f"{f['replies']:.1f}"),
        ("商談数", lambda s, f: f"{f['meetings']:.1f}"),
        ("無料診断数（提携含む）", lambda s, f: f"{f['diags']:.1f}"),
        ("本監査契約数", lambda s, f: f"{f['audits']:.1f}"),
        ("削減実現（成功）件数", lambda s, f: f"{f['successes']:.2f}"),
        ("1社あたり月間削減額", lambda s, f: yen(s.monthly_saving)),
        ("1社あたり成功報酬（25%×12か月）", lambda s, f: yen(f['fee_per_success'])),
        ("成功報酬売上/月", lambda s, f: yen(f['fee_rev'])),
        ("MARGIN WATCH 契約数（収束値）", lambda s, f: f"{f['watch_subs_ss']:.0f}"),
        ("MARGIN WATCH 売上/月", lambda s, f: yen(f['watch_rev_ss'])),
        ("総費用/月（紹介料含む）", lambda s, f: yen(f['cost'])),
        ("**営業利益/月**", lambda s, f: f"**{yen(f['profit_ss'])}**"),
        ("粗利益率", lambda s, f: f"{f['gross_margin']:.0%}"),
        ("人手作業時間/月", lambda s, f: f"{f['hours']:.0f}h"),
        ("月利益50万円に必要な成功件数/月（WATCH除外）", lambda s, f: f"{f['need_success']:.2f}"),
    ]
    for label, fn in rows:
        out.append(f"| {label} | " + " | ".join(fn(s, f) for s, f in zip(ss, fs)) + " |")
    out.append("")

    out += ["## 2. 18か月の立ち上がり（標準シナリオ）", "",
            "前提：1〜2か月目はヒアリング・弁護士レビューで営業なし。3か月目から営業開始。"
            "成功報酬は実請求に反映された削減額の25%を最大12か月、毎月後払い（2026-11-10 経営判断）。", "",
            "| 月 | 報酬支払中の顧客数 | 成功報酬 | WATCH売上 | WATCH契約数 | 費用 | 営業利益 | 累積利益 |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in ramp(EC_STANDARD):
        out.append(f"| {r['month']} | {r['paying']:.1f} | {yen(r['fee'])} | {yen(r['watch'])} | {r['watch_subs']:.1f} | "
                   f"{yen(r['cost'])} | {yen(r['profit'])} | {yen(r['cum'])} |")
    out.append("")
    for label, sc in (("悲観", EC_PESSIMISTIC), ("楽観", EC_OPTIMISTIC)):
        r = ramp(sc)
        first = next((x["month"] for x in r if x["profit"] >= TARGET_PROFIT), None)
        be = next((x["month"] for x in r if x["cum"] >= 0), None)
        out.append(f"- {label}: 12か月目の営業利益 {yen(r[11]['profit'])}円、18か月目 {yen(r[-1]['profit'])}円、累積 {yen(r[-1]['cum'])}円、"
                   f"月利益50万円到達 {'%dか月目' % first if first else '18か月以内に未達'}、"
                   f"累積黒字化 {'%dか月目' % be if be else '18か月以内に未達'}")
    r = ramp(EC_STANDARD)
    first = next((x["month"] for x in r if x["profit"] >= TARGET_PROFIT), None)
    be = next((x["month"] for x in r if x["cum"] >= 0), None)
    out.append(f"- 標準: 12か月目の営業利益 {yen(r[11]['profit'])}円、月利益50万円到達 {'%dか月目' % first if first else '18か月以内に未達'}、"
               f"累積黒字化 {'%dか月目' % be if be else '18か月以内に未達'}")
    out.append("")

    out += ["## 3. 収益モデル比較（定常状態）", "",
            "| モデル | 成功件数/月 | 成功報酬 | WATCH売上(収束値) | 費用 | 営業利益(収束値) | 12か月目利益 | 18か月目利益 | 必要成功件数(WATCH除外) | 作業時間 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for label, sc in MODELS.items():
        f = funnel(sc)
        r = ramp(sc)
        out.append(f"| {label} | {f['successes']:.2f} | {yen(f['fee_rev'])} | {yen(f['watch_rev_ss'])} | "
                   f"{yen(f['cost'])} | {yen(f['profit_ss'])} | {yen(r[11]['profit'])} | {yen(r[-1]['profit'])} | "
                   f"{f['need_success']:.1f} | {f['hours']:.0f}h |")
    out.append("")

    f = funnel(SALON_STANDARD)
    out += ["## 4. 参考：美容室を初期市場にした場合（標準）", "",
            f"- 成功報酬/社: {yen(f['fee_per_success'])}円、成功件数/月: {f['successes']:.2f}",
            f"- 12か月目営業利益: {yen(ramp(SALON_STANDARD)[11]['profit'])}円/月、収束値: {yen(f['profit_ss'])}円/月、月利益50万円に必要な成功件数: {f['need_success']:.1f}件/月",
            f"- 必要成功件数を満たすための月間無料診断数（契約率{SALON_STANDARD.contract_rate:.0%}×成功率{SALON_STANDARD.success_rate:.0%}）: "
            f"{f['need_success'] / (SALON_STANDARD.contract_rate * SALON_STANDARD.success_rate):.0f}件/月",
            ""]

    out += ["## 5. 感度：1社あたり月間削減額 × 月間成功件数 → 成功報酬のみの月間営業利益（WATCH除外・標準の費用構造）", "",
            "| 月間削減額＼成功件数 | 1 | 2 | 3 | 4 | 6 |", "|---:|---:|---:|---:|---:|---:|"]
    for saving in (30_000, 50_000, 80_000, 120_000, 200_000):
        cells = []
        for n in (1, 2, 3, 4, 6):
            s = replace(EC_STANDARD, monthly_saving=saving, watch_conv=0.0)
            f = funnel(s)
            scale = n / f["successes"]
            s2 = replace(s, contacts=round(s.contacts * scale), partner_diags=s.partner_diags * scale)
            cells.append(yen(funnel(s2)["profit_ss"]))
        out.append(f"| {yen(saving)} | " + " | ".join(cells) + " |")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    print(render())
