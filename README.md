# MARGIN RECOVERY NETWORK

EC事業者向け 配送費・物流請求の監査事業（成功報酬＋継続監視）の事業立ち上げリポジトリ。

## 現時点の結論（2026-11-09）

- **初期市場：年商1〜10億円のEC事業者**（美容室は1社あたり報酬が小さすぎるため却下。100点満点の採点でEC 77点、美容室 50点）
- **初期商品：MARGIN AUDIT for EC**（宅配運賃・3PL請求・決済手数料の監査。成功報酬は実現削減額×12か月×25%）
- **継続収益：MARGIN WATCH**（19,800円/月が基本）
- **標準シナリオで月利益50万円の到達は8か月目。** 悲観シナリオでは未達のため、60日・90日時点の撤退・転換基準を設定
- **開始前の必須事項：弁護士レビュー**（弁護士法72条・特定電子メール法・成功報酬契約）

## 成果物の一覧（要件の20項目との対応）

| # | 成果物 | ファイル |
|---|---|---|
| 1 | 事業計画書 | [docs/00_事業計画書.md](docs/00_事業計画書.md) |
| 2 | 市場・競合分析レポート | [docs/01_strategy/02_市場・競合分析.md](docs/01_strategy/02_市場・競合分析.md) |
| 3 | 初期ターゲット選定レポート（TASK1） | [docs/01_strategy/01_事業構想の再評価_TASK1.md](docs/01_strategy/01_事業構想の再評価_TASK1.md) |
| 4 | 料金・成功報酬設計書 | [docs/02_offer/02_料金・成功報酬設計書.md](docs/02_offer/02_料金・成功報酬設計書.md)、[初期サービス定義（TASK3）](docs/02_offer/01_初期サービス定義_TASK3.md) |
| 5 | 3パターンの収益シミュレーション | [docs/06_plan/02_収益シミュレーション結果.md](docs/06_plan/02_収益シミュレーション結果.md)（生成元 [finance/simulate.py](finance/simulate.py)） |
| 6 | 90日間の実行計画 | [docs/06_plan/01_90日実行計画.md](docs/06_plan/01_90日実行計画.md) |
| 7 | AIエージェント組織図 | [docs/03_system/02_AIエージェント組織とシステム構成.md](docs/03_system/02_AIエージェント組織とシステム構成.md) |
| 8 | 使用サービス一覧・料金一覧 | [docs/03_system/01_使用サービス一覧・料金.md](docs/03_system/01_使用サービス一覧・料金.md) |
| 9 | システム構成図 | 7と同じファイル（第4〜6節） |
| 10 | 営業フロー | [docs/04_sales/01_営業フロー.md](docs/04_sales/01_営業フロー.md) |
| 11 | 営業メールテンプレート | [docs/04_sales/02_営業メールテンプレート.md](docs/04_sales/02_営業メールテンプレート.md) |
| 12 | 顧客ヒアリングシート | [docs/05_operations/01_顧客ヒアリングシート.md](docs/05_operations/01_顧客ヒアリングシート.md) |
| 13 | 無料診断フォーム設計 | [docs/05_operations/02_無料診断フォーム設計.md](docs/05_operations/02_無料診断フォーム設計.md) |
| 14 | 支出監査チェックリスト | [docs/05_operations/03_支出監査チェックリスト.md](docs/05_operations/03_支出監査チェックリスト.md) |
| 15 | 顧客向け監査レポートテンプレート | [docs/05_operations/04_監査レポートテンプレート.md](docs/05_operations/04_監査レポートテンプレート.md) |
| 16 | 成功報酬契約の論点整理 | [docs/02_offer/04_成功報酬契約の論点整理.md](docs/02_offer/04_成功報酬契約の論点整理.md) |
| 17 | MARGIN WATCH 商品設計 | [docs/02_offer/03_MARGIN_WATCH商品設計.md](docs/02_offer/03_MARGIN_WATCH商品設計.md) |
| 18 | KPI管理表 | [kpi/](kpi/README.md) |
| 19 | LP・Webサイト構成 | [docs/07_web/01_LP・Webサイト構成.md](docs/07_web/01_LP・Webサイト構成.md)、実装 [site/index.html](site/index.html) |
| 20 | 初期運用マニュアル | [docs/05_operations/05_初期運用マニュアル.md](docs/05_operations/05_初期運用マニュアル.md) |
| — | 出典一覧 | [docs/sources.md](docs/sources.md) |

## 構築済みのもの（TASK 7）

| 成果物 | 内容 | 使い方 |
|---|---|---|
| 配送費監査エンジン | 出荷CSV×契約料金表を照合し、重複請求・契約単価超過・サイズ区分の過大請求・小型便候補を根拠付きで出力 | `python3 tools/audit/shipping_audit.py --shipments tools/audit/samples/shipments_sample.csv --ratecard tools/audit/samples/ratecard_sample.json` |
| テスト | 判定ロジックの単体テスト（8件） | `python3 -m unittest discover -s tools/audit/tests` |
| 収益シミュレーター | 3シナリオ×5収益モデル、12か月の立ち上がり、感度分析 | `python3 finance/simulate.py` |
| LP | 静的HTML（ダークモード・スマホ対応）。Cloudflare Pages に `site/` を公開 | ブラウザで `site/index.html` を開く |
| KPIテンプレート | 週次KPI・案件管理・ヒアリングログ | `kpi/*.csv` をスプレッドシートに取り込み |

サンプルデータはすべて架空。**顧客の実データはこのリポジトリにコミットしない**（`.gitignore` で `client_data/` を除外）。

## 人間が行う必要がある次のアクション

1. 事業形態（個人事業／合同会社）の決定、ドメイン取得、Google Workspace 開設
2. 契約書一式の弁護士レビュー依頼（論点：`docs/02_offer/04_成功報酬契約の論点整理.md`）
3. EC事業者10社へのヒアリング（課題検証。営業ではない）
4. Googleフォーム作成と LP の `data-form-url` 差し替え、会社情報の記入
