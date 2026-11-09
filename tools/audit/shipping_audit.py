"""EC配送費監査エンジン（MVP・決定論的ルール）

AI の推測ではなく、契約料金表と出荷実績CSVの突合で「根拠付き」の指摘だけを出す。
LLM はこの出力の文章化・顧客説明にのみ使う（数値は必ずこのスクリプトの計算値を使う）。

使い方:
    python3 tools/audit/shipping_audit.py \
        --shipments tools/audit/samples/shipments_sample.csv \
        --ratecard tools/audit/samples/ratecard_sample.json \
        --out-md report.md --out-json findings.json

出荷CSVの列（ヘッダ必須）:
    tracking_no, ship_date, carrier, service, billed_size, weight_kg,
    length_cm, width_cm, height_cm, dest_pref, charged_yen
    ※ 寸法・重量が空欄の行はサイズ判定系チェックを行わない（請求額チェックのみ）。
    ※ 不正な行は黙って捨てず「入力データの問題」として報告する（仕様: tools/audit/INPUT_SPEC.md）。

指摘の種類と確度:
    DUPLICATE_CHARGE      確定  同一追跡番号の重複請求
    OVER_CONTRACT_RATE    確定  契約単価を超える請求
    SIZE_OVERBILLED       要確認 実測寸法・重量より大きいサイズ区分で請求
    SMALL_PACKET_ELIGIBLE 推定  小型サービス（例: 薄型・軽量便）で送れた可能性
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIDENCE = {
    "DUPLICATE_CHARGE": "確定",
    "OVER_CONTRACT_RATE": "確定",
    "SIZE_OVERBILLED": "要確認",
    "SMALL_PACKET_ELIGIBLE": "推定",
}
LABEL = {
    "DUPLICATE_CHARGE": "重複請求",
    "OVER_CONTRACT_RATE": "契約単価超過",
    "SIZE_OVERBILLED": "サイズ区分の過大請求の疑い",
    "SMALL_PACKET_ELIGIBLE": "小型配送サービスへの切替候補",
}


@dataclass
class Finding:
    kind: str
    tracking_no: str
    ship_date: str
    detail: str
    charged_yen: int
    expected_yen: int

    @property
    def diff_yen(self) -> int:
        return max(self.charged_yen - self.expected_yen, 0)


def _num(v: str | None) -> float | None:
    v = (v or "").strip().replace(",", "")
    return float(v) if v else None


@dataclass
class InputIssue:
    """監査できなかった行・注意が必要な行。黙って捨てずに必ず報告する。"""
    level: str          # "ERROR"（その行は監査対象外）/ "WARN"（一部チェックのみ実施）
    line: int           # CSV の行番号（ヘッダ=1）
    tracking_no: str
    message: str


def validate_row(r: dict, line: int, ratecard: dict) -> list[InputIssue]:
    tn = (r.get("tracking_no") or "").strip()
    issues: list[InputIssue] = []
    if not tn:
        issues.append(InputIssue("ERROR", line, "", "追跡番号が空欄"))
    for key in ("carrier", "service", "billed_size"):
        if not (r.get(key) or "").strip():
            issues.append(InputIssue("ERROR", line, tn, f"{key} が空欄"))
    try:
        v = _num(r.get("charged_yen"))
        if v is None:
            issues.append(InputIssue("ERROR", line, tn, "charged_yen（運賃）が空欄"))
        elif v < 0:
            issues.append(InputIssue("ERROR", line, tn, f"charged_yen が負の値: {v}"))
    except ValueError:
        issues.append(InputIssue("ERROR", line, tn, f"charged_yen が数値でない: {r.get('charged_yen')!r}"))
    try:
        dims = [_num(r.get(k)) for k in ("length_cm", "width_cm", "height_cm")]
        w = _num(r.get("weight_kg"))
        present = [d for d in dims if d is not None]
        if 0 < len(present) < 3:
            issues.append(InputIssue("WARN", line, tn, "3辺寸法の一部のみ入力。サイズ判定をスキップ"))
        if any(d is not None and d <= 0 for d in dims + [w]):
            issues.append(InputIssue("WARN", line, tn, "寸法または重量が0以下。サイズ判定をスキップ"))
    except ValueError:
        issues.append(InputIssue("WARN", line, tn, "寸法・重量に数値でない値。サイズ判定をスキップ"))
    if not any(i.level == "ERROR" for i in issues):
        key = f"{r['carrier'].strip()}:{r['service'].strip()}"
        svc = ratecard.get("services", {}).get(key)
        if svc is None:
            issues.append(InputIssue("WARN", line, tn, f"契約運賃表に {key} がない。契約単価・サイズの照合不可"))
        elif r["billed_size"].strip() not in svc["sizes"]:
            issues.append(InputIssue("WARN", line, tn, f"契約運賃表に {r['billed_size'].strip()} サイズがない。契約単価の照合不可"))
        elif r.get("dest_pref") is None or not r.get("dest_pref", "").strip():
            issues.append(InputIssue("WARN", line, tn, "届け先都道府県が空欄。地域別単価の照合は基本単価で実施"))
    return issues


def load_shipments(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"tracking_no", "ship_date", "carrier", "service", "billed_size", "charged_yen"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"出荷CSVに必須列がありません: {sorted(missing)}")
    return rows


def contract_price(ratecard: dict, carrier: str, service: str, size: str, pref: str) -> int | None:
    svc = ratecard.get("services", {}).get(f"{carrier}:{service}")
    if not svc:
        return None
    tier = svc["sizes"].get(str(size))
    if not tier:
        return None
    return int(tier.get("pref_prices", {}).get(pref, tier["price"]))


def smallest_fitting_size(svc: dict, dims_sum: float, weight: float) -> str | None:
    tiers = sorted(svc["sizes"].items(), key=lambda kv: kv[1]["max_sum_cm"])
    for code, t in tiers:
        if dims_sum <= t["max_sum_cm"] and weight <= t["max_kg"]:
            return code
    return None


def fits_small_packet(sp: dict, dims: list[float], weight: float) -> bool:
    longest, middle, thickness = sorted(dims, reverse=True)
    return (thickness <= sp["max_thickness_cm"] and longest <= sp["max_long_cm"]
            and middle <= sp["max_short_cm"] and weight <= sp["max_kg"])


def audit(rows: list[dict], ratecard: dict, issues: list[InputIssue] | None = None) -> list[Finding]:
    """issues にリストを渡すと、入力の問題（ERROR/WARN）を追記する。ERROR 行は監査しない。"""
    findings: list[Finding] = []
    seen: dict[str, int] = defaultdict(int)
    small_packet = ratecard.get("small_packet")
    for line, r in enumerate(rows, start=2):
        row_issues = validate_row(r, line, ratecard)
        if issues is not None:
            issues.extend(row_issues)
        if any(i.level == "ERROR" for i in row_issues):
            continue
        tn = r["tracking_no"].strip()
        charged = int(_num(r["charged_yen"]))
        carrier, service, size = r["carrier"].strip(), r["service"].strip(), r["billed_size"].strip()
        pref = (r.get("dest_pref") or "").strip()
        seen[tn] += 1
        if seen[tn] > 1:
            findings.append(Finding("DUPLICATE_CHARGE", tn, r["ship_date"],
                                    f"追跡番号 {tn} が{seen[tn]}回目の請求", charged, 0))
            continue
        expected = contract_price(ratecard, carrier, service, size, pref)
        if expected is not None and charged > expected:
            findings.append(Finding("OVER_CONTRACT_RATE", tn, r["ship_date"],
                                    f"{carrier} {service} {size}サイズ 契約単価{expected:,}円に対し{charged:,}円",
                                    charged, expected))
        if any(i.message.endswith("サイズ判定をスキップ") for i in row_issues):
            continue
        dims = [_num(r.get(k)) for k in ("length_cm", "width_cm", "height_cm")]
        weight = _num(r.get("weight_kg"))
        if None in dims or weight is None:
            continue
        svc = ratecard.get("services", {}).get(f"{carrier}:{service}")
        base_price = expected if expected is not None else charged
        if svc:
            fit = smallest_fitting_size(svc, sum(dims), weight)
            if fit is not None and svc["sizes"][fit]["max_sum_cm"] < svc["sizes"].get(size, {}).get("max_sum_cm", 0):
                fit_price = contract_price(ratecard, carrier, service, fit, pref)
                if fit_price is not None and fit_price < base_price:
                    findings.append(Finding(
                        "SIZE_OVERBILLED", tn, r["ship_date"],
                        f"実測 3辺計{sum(dims):.0f}cm/{weight}kg → {fit}サイズ相当だが{size}サイズで請求",
                        base_price, fit_price))
                    continue
        if small_packet and fits_small_packet(small_packet, dims, weight) and small_packet["price"] < base_price:
            findings.append(Finding(
                "SMALL_PACKET_ELIGIBLE", tn, r["ship_date"],
                f"厚さ{min(dims):.1f}cm/{weight}kg → {small_packet['name']}（{small_packet['price']:,}円）対象の可能性",
                base_price, small_packet["price"]))
    return findings


def _safe_yen(v: str | None) -> int:
    try:
        n = _num(v)
        return int(n) if n is not None and n >= 0 else 0
    except ValueError:
        return 0


def summarize(rows: list[dict], findings: list[Finding], months: float,
              issues: list[InputIssue] | None = None) -> dict:
    issues = issues or []
    total = sum(_safe_yen(r.get("charged_yen")) for r in rows)
    by_kind: dict[str, dict] = {}
    for f in findings:
        k = by_kind.setdefault(f.kind, {"count": 0, "diff_yen": 0})
        k["count"] += 1
        k["diff_yen"] += f.diff_yen
    monthly_factor = 1 / months if months else 1
    for k in by_kind.values():
        k["monthly_yen"] = round(k["diff_yen"] * monthly_factor)
        k["annual_yen"] = k["monthly_yen"] * 12
    return {
        "shipments": len(rows),
        "total_charged_yen": total,
        "period_months": months,
        "by_kind": by_kind,
        "confirmed_yen": sum(v["diff_yen"] for k, v in by_kind.items() if CONFIDENCE[k] == "確定"),
        "potential_monthly_yen": sum(v["monthly_yen"] for v in by_kind.values()),
        "input_errors": sum(1 for i in issues if i.level == "ERROR"),
        "input_warnings": sum(1 for i in issues if i.level == "WARN"),
    }


def render_md(summary: dict, findings: list[Finding], client: str,
              issues: list[InputIssue] | None = None) -> str:
    issues = issues or []
    s = summary
    lines = [
        f"# 配送費監査 一次結果：{client}",
        "",
        "> 本結果は提出データと契約料金表の機械的な突合結果です。「確定」は請求データ上の不整合、"
        "「要確認」「推定」は実物・契約条件の確認後に確定します。削減を保証するものではありません。",
        "",
        f"- 対象出荷数: {s['shipments']:,}件 / 対象期間: {s['period_months']}か月 / 請求総額: {s['total_charged_yen']:,}円",
        f"- 確定した過請求額（期間中）: **{s['confirmed_yen']:,}円**",
        f"- 改善余地の月額換算（全区分合計・確認前）: **{s['potential_monthly_yen']:,}円/月**",
        f"- 入力データの問題: エラー {s.get('input_errors', 0)}行（監査対象外）／警告 {s.get('input_warnings', 0)}件"
        "（年額換算は期間中の発生率が続く前提。重複請求など単発の差異は年額換算をそのまま使わない）",
        "",
        "| 区分 | 確度 | 件数 | 期間中の差額 | 月額換算 | 年額換算 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for kind in CONFIDENCE:
        v = s["by_kind"].get(kind)
        if v:
            lines.append(f"| {LABEL[kind]} | {CONFIDENCE[kind]} | {v['count']} | {v['diff_yen']:,} | "
                         f"{v['monthly_yen']:,} | {v['annual_yen']:,} |")
    lines += ["", "## 根拠明細（先頭50件）", "",
              "| 区分 | 追跡番号 | 出荷日 | 内容 | 請求額 | あるべき額 | 差額 |",
              "|---|---|---|---|---:|---:|---:|"]
    for f in findings[:50]:
        lines.append(f"| {LABEL[f.kind]} | {f.tracking_no} | {f.ship_date} | {f.detail} | "
                     f"{f.charged_yen:,} | {f.expected_yen:,} | {f.diff_yen:,} |")
    if issues:
        lines += ["", "## 入力データの問題（先頭50件）", "",
                  "| 区分 | CSV行 | 追跡番号 | 内容 |", "|---|---:|---|---|"]
        for i in issues[:50]:
            lines.append(f"| {i.level} | {i.line} | {i.tracking_no} | {i.message} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shipments", required=True, type=Path)
    ap.add_argument("--ratecard", required=True, type=Path)
    ap.add_argument("--months", type=float, default=1.0, help="出荷CSVの対象期間（月数）")
    ap.add_argument("--client", default="（顧客名）")
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--out-json", type=Path)
    a = ap.parse_args()
    rows = load_shipments(a.shipments)
    ratecard = json.loads(a.ratecard.read_text(encoding="utf-8"))
    issues: list[InputIssue] = []
    findings = audit(rows, ratecard, issues)
    summary = summarize(rows, findings, a.months, issues)
    md = render_md(summary, findings, a.client, issues)
    if a.out_md:
        a.out_md.write_text(md, encoding="utf-8")
    if a.out_json:
        a.out_json.write_text(json.dumps(
            {"summary": summary,
             "findings": [asdict(f) | {"diff_yen": f.diff_yen, "confidence": CONFIDENCE[f.kind]} for f in findings],
             "input_issues": [asdict(i) for i in issues]},
            ensure_ascii=False, indent=2), encoding="utf-8")
    if not a.out_md:
        print(md)


if __name__ == "__main__":
    main()
