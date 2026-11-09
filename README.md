# MARGIN RECOVERY NETWORK

EC事業者向け 配送費・物流請求の監査事業（成功報酬＋継続監視）の事業立ち上げリポジトリ。

## 現時点の方針（2026-11-10 経営判断：条件付きGO）

- **事業形態**：個人事業で開始。顧客の実データ受領・有償契約の前に合同会社化を判定
- **初期市場**：年商1〜10億円のEC事業者（美容室は1社あたり報酬が小さすぎるため却下）
- **初期商品**：宅配便請求監査に限定（3PL請求・決済手数料は第2段階）
- **成功報酬**：実際に請求へ反映された削減額×25%、最大12か月・月次後払い（叩き台。弁護士レビュー後に確定）
- **最初の60日**：10社ヒアリング（売り込みなし・データ受領なし）と弁護士レビューを先に行い、その後に無料診断3件
- **収益見込み（標準）**：月利益50万円は16か月目、累積黒字化は12か月目。必要資金は約60〜110万円で上限100万円を超える可能性あり（`docs/00_事業計画書.md` 第7節）

経営判断の原文：[docs/decisions/2026-11-10_経営判断・実行方針報告書.md](docs/decisions/2026-11-10_経営判断・実行方針報告書.md)

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
| 12 | 顧客ヒアリングシート（10社ヒアリング キット） | [docs/05_operations/01_顧客ヒアリングシート.md](docs/05_operations/01_顧客ヒアリングシート.md) |
| 13 | 無料診断フォーム設計 | [docs/05_operations/02_無料診断フォーム設計.md](docs/05_operations/02_無料診断フォーム設計.md) |
| 14 | 支出監査チェックリスト | [docs/05_operations/03_支出監査チェックリスト.md](docs/05_operations/03_支出監査チェックリスト.md) |
| 15 | 顧客向け監査レポートテンプレート | [docs/05_operations/04_監査レポートテンプレート.md](docs/05_operations/04_監査レポートテンプレート.md) |
| 16 | 成功報酬契約の論点整理 | [docs/02_offer/04_成功報酬契約の論点整理.md](docs/02_offer/04_成功報酬契約の論点整理.md) |
| 17 | MARGIN WATCH 商品設計 | [docs/02_offer/03_MARGIN_WATCH商品設計.md](docs/02_offer/03_MARGIN_WATCH商品設計.md) |
| 18 | KPI管理表 | [kpi/](kpi/README.md) |
| 19 | LP・Webサイト構成 | [docs/07_web/01_LP・Webサイト構成.md](docs/07_web/01_LP・Webサイト構成.md)、実装 [site/index.html](site/index.html) |
| 20 | 初期運用マニュアル | [docs/05_operations/05_初期運用マニュアル.md](docs/05_operations/05_初期運用マニュアル.md) |
| — | 弁護士見積依頼書・業務フロー・データ取扱規程 | [docs/legal/](docs/legal/01_弁護士見積依頼書.md) |
| — | 個人事業の開始と法人化判定 | [docs/06_plan/03_個人事業開始と法人化判定.md](docs/06_plan/03_個人事業開始と法人化判定.md) |
| — | 出典一覧 | [docs/sources.md](docs/sources.md) |

## 構築済みのもの（TASK 7）

| 成果物 | 内容 | 使い方 |
|---|---|---|
| 宅配便請求監査エンジン | 請求CSV×契約運賃表を照合し、重複請求・契約単価超過・サイズ区分の過大候補・小型便候補を根拠付きで出力。不正な入力行は報告（仕様：[tools/audit/INPUT_SPEC.md](tools/audit/INPUT_SPEC.md)） | `python3 tools/audit/shipping_audit.py --shipments tools/audit/samples/shipments_sample.csv --ratecard tools/audit/samples/ratecard_sample.json` |
| テスト | 判定ロジック・入力チェックの単体テスト（14件） | `python3 -m unittest discover -s tools/audit/tests` |
| 収益シミュレーター | 3シナリオ×5収益モデル、18か月の立ち上がり（月次後払い）、感度分析 | `python3 finance/simulate.py` |
| LP | 静的HTML（ダークモード・スマホ対応）。Cloudflare Pages に `site/` を公開 | ブラウザで `site/index.html` を開く |
| KPIテンプレート | 週次KPI・案件管理・ヒアリング候補・ヒアリングログ | `kpi/*.csv` をスプレッドシートに取り込み |

サンプルデータはすべて架空。**顧客の実データはこのリポジトリにコミットしない**（`.gitignore` で `client_data/` を除外）。

## 次のアクション（W1：2026-11-16〜）

| 優先 | アクション | 資料 |
|---:|---|---|
| 1 | 弁護士2〜3先へ見積依頼（{　}を埋めて送付） | [docs/legal/01_弁護士見積依頼書.md](docs/legal/01_弁護士見積依頼書.md) |
| 2 | 個人事業の開始準備（開業日・届出・青色申告・口座・ドメイン・MFA） | [docs/06_plan/03_個人事業開始と法人化判定.md](docs/06_plan/03_個人事業開始と法人化判定.md) |
| 3 | ヒアリング候補30〜40社のリスト作成と依頼（紹介・知人経由を優先） | `kpi/hearing_candidates.csv`、[メールH1・H2](docs/04_sales/02_営業メールテンプレート.md) |
| 4 | W2〜3で10社ヒアリング（データは受け取らない） | [ヒアリング キット](docs/05_operations/01_顧客ヒアリングシート.md) |
