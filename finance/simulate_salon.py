"""サロン向け「定額・半自動の固定費チェック」モデルの収益シミュレーション（v0.3 比較用）

    python3 finance/simulate_salon.py

前提はすべて仮説。成功報酬ではなく、定額の診断料（返金保証つき）と月額の見直し通知で収益化する。
顧客（サロン）が自分で見直しを実行し、当社は交渉・代理・成果連動の報酬を行わない。
"""
from __future__ import annotations

from dataclasses import dataclass

TARGET = 500_000


@dataclass(frozen=True)
class Salon:
    name: str
    diag_steady: float        # 立ち上がり後の月間診断件数（直接＋紹介元）
    partner_share_of_diag: float  # 紹介元経由の比率
    partner_rev_share: float  # 紹介元への支払い（売上に対する比率）
    price: int                # 診断料（税別）
    refund_rate: float        # 返金保証の発動率（見直し余地が診断料未満だった場合）
    watch_conv: float         # 診断 → 月額 移行率
    watch_price: int          # 月額
    watch_churn: float        # 月次解約率
    hours_diag: float = 1.0   # 1診断の人手（半自動：取込・確認・15分説明）
    hours_watch: float = 0.1  # 月額1件あたりの人手
    var_diag: int = 500       # OCR/API 等
    var_watch: int = 100
    fixed: int = 30_000       # 実費ベースの固定費（Workspace・ドメイン・会計・保険積立）
    sales_cost: int = 10_000  # 名刺・資料・小額広告


RAMP = [0.2, 0.4, 0.6, 0.8] + [1.0] * 30  # 紹介元の開拓に時間がかかる前提


def run(s: Salon, months: int = 18) -> list[dict]:
    rows, subs, cum = [], 0.0, 0.0
    for m in range(months):
        d = s.diag_steady * RAMP[m]
        diag_rev = d * s.price * (1 - s.refund_rate)
        subs = subs * (1 - s.watch_churn) + d * s.watch_conv
        watch_rev = subs * s.watch_price
        partner = (diag_rev + watch_rev) * s.partner_share_of_diag * s.partner_rev_share
        cost = d * s.var_diag + subs * s.var_watch + s.fixed + s.sales_cost + partner
        profit = diag_rev + watch_rev - cost
        cum += profit
        rows.append(dict(month=m + 1, diags=d, subs=subs, diag_rev=diag_rev, watch_rev=watch_rev,
                         cost=cost, profit=profit, cum=cum,
                         hours=d * s.hours_diag + subs * s.hours_watch))
    return rows


COMMON = dict(partner_rev_share=0.3, price=19_800, refund_rate=0.15, watch_price=2_980)
SCENARIOS = [
    Salon("悲観", diag_steady=8, partner_share_of_diag=0.3, watch_conv=0.2, watch_churn=0.08, **COMMON),
    Salon("標準", diag_steady=20, partner_share_of_diag=0.6, watch_conv=0.3, watch_churn=0.05, **COMMON),
    Salon("楽観", diag_steady=35, partner_share_of_diag=0.7, watch_conv=0.4, watch_churn=0.04, **COMMON),
]


def yen(v: float) -> str:
    return f"{v:,.0f}"


def render() -> str:
    out = ["# サロン向け 定額・半自動モデル 収益シミュレーション（自動生成）", "",
           "> `python3 finance/simulate_salon.py` で再生成。前提はすべて仮説。経営目標の試算であり対外的に表示しない。",
           "> 診断料19,800円（返金保証つき）＋月額2,980円。紹介元（サロン専門税理士等）に売上の30%を支払う前提。", "",
           "| 指標 | " + " | ".join(s.name for s in SCENARIOS) + " |", "|---|---:|---:|---:|"]
    res = [run(s) for s in SCENARIOS]

    def first(rows, key, cond):
        return next((r["month"] for r in rows if cond(r[key])), None)

    lines = [
        ("立ち上がり後の月間診断件数", lambda s, r: f"{s.diag_steady:.0f}"),
        ("6か月目の営業利益", lambda s, r: yen(r[5]["profit"])),
        ("12か月目の営業利益", lambda s, r: yen(r[11]["profit"])),
        ("18か月目の営業利益", lambda s, r: yen(r[17]["profit"])),
        ("12か月目の月額契約数", lambda s, r: f"{r[11]['subs']:.0f}"),
        ("12か月目の人手時間/月", lambda s, r: f"{r[11]['hours']:.0f}h"),
        ("運転資金の最大不足", lambda s, r: yen(min(0, min(x["cum"] for x in r)))),
        ("月利益50万円の到達", lambda s, r: (lambda m: f"{m}か月目" if m else "18か月以内に未達")(first(r, "profit", lambda v: v >= TARGET))),
        ("累積黒字化", lambda s, r: (lambda m: f"{m}か月目" if m else "18か月以内に未達")(first(r, "cum", lambda v: v >= 0))),
    ]
    for label, fn in lines:
        out.append(f"| {label} | " + " | ".join(fn(s, r) for s, r in zip(SCENARIOS, res)) + " |")
    out += ["", "## 月利益50万円に必要な月間診断件数（立ち上がり後・月額の積み上がり12か月時点）", ""]
    for n in (10, 15, 20, 25, 30, 40):
        s = Salon("x", diag_steady=n, partner_share_of_diag=0.6, watch_conv=0.3, watch_churn=0.05, **COMMON)
        out.append(f"- 月{n}件 → 12か月目の営業利益 {yen(run(s)[11]['profit'])}円、18か月目 {yen(run(s)[17]['profit'])}円")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print(render())
