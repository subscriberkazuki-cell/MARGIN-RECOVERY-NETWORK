# MARGIN RECOVERY NETWORK

EC事業者向け 配送費・物流請求の監査事業（成功報酬＋継続監視）の事業立ち上げリポジトリ。

## 現時点の方針（v0.3：2026-11-10）

**小規模サロン向けの「定額・半自動の固定費チェック」から始め、4週間で検証する。** EC配送費の監査は Phase 2（成熟後）。

| 項目 | 内容 |
|---|---|
| 対象 | 美容室・ネイル・エステ・まつげ（1〜5店舗） |
| 商品 | 固定費・集客費チェック 19,800円（見直し余地が診断料未満なら返金）＋月額2,980円の見直し通知（検証後に判断） |
| 仕組み | 5分の質問票 → 決定論的プログラムで判定（[tools/salon/](tools/salon/fixed_cost_check.py)）→ 15分の説明。書類の受領・AIへの顧客データ入力なし。見直しはオーナー自身が実行 |
| 販路 | サロン専門の税理士・会計事務所などの紹介元が主軸 |
| 検証 | 4週間・追加投資10万円以内。合格基準と撤退基準は [方針転換 v0.3](docs/decisions/2026-11-10b_方針転換v0.3_サロン定額モデル.md) |
| 計画 | [サロン検証4週間計画](docs/06_plan/05_サロン検証4週間計画.md)、[収益試算](docs/06_plan/04_サロン定額モデル_シミュレーション結果.md) |
| 事業形態 | 個人事業（変更なし） |

以下の成果物一覧の多くは v0.2（EC配送費・成功報酬）の資料で、**Phase 2 の資産として保持**している。EC版の弁護士見積依頼は送らない。

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
| **サロン固定費チェック・ブラウザ版** | オフラインで動く1ファイルのHTML。オーナーと一緒に入力しその場で結果・PDF。外部通信なし | `tools/salon/check.html` をブラウザで開く |
| **サロン固定費チェック（v0.3）** | 質問票の回答から、決済手数料・ツール重複・未使用回線・電気単価・集客の費用対効果を判定。確度（確定/推定/要確認）と根拠つき | `python3 tools/salon/fixed_cost_check.py --input tools/salon/samples/answers_sample.json`（テスト10件。ブラウザ版との一致確認を含む：`python3 -m unittest discover -s tools/salon/tests`） |
| サロン定額モデル試算（v0.3） | 3シナリオ・18か月 | `python3 finance/simulate_salon.py` |
| 宅配便請求監査エンジン | 請求CSV×契約運賃表を照合し、重複請求・契約単価超過・サイズ区分の過大候補・小型便候補を根拠付きで出力。不正な入力行は報告（仕様：[tools/audit/INPUT_SPEC.md](tools/audit/INPUT_SPEC.md)） | `python3 tools/audit/shipping_audit.py --shipments tools/audit/samples/shipments_sample.csv --ratecard tools/audit/samples/ratecard_sample.json` |
| テスト | 判定ロジック・入力チェックの単体テスト（14件） | `python3 -m unittest discover -s tools/audit/tests` |
| 収益シミュレーター | 3シナリオ×5収益モデル、18か月の立ち上がり（月次後払い）、感度分析 | `python3 finance/simulate.py` |
| LP | 静的HTML（ダークモード・スマホ対応）。Cloudflare Pages に `site/` を公開 | ブラウザで `site/index.html` を開く |
| KPIテンプレート | 週次KPI・案件管理・ヒアリング候補・ヒアリングログ | `kpi/*.csv` をスプレッドシートに取り込み |

サンプルデータはすべて架空。**顧客の実データはこのリポジトリにコミットしない**（`.gitignore` で `client_data/` を除外）。

## 次のアクション（W1：2026-11-16〜）

| 優先 | アクション | 資料 |
|---:|---|---|
| 1 | 個人事業の開始準備（開業日・届出・青色申告・口座・ドメイン・MFA） | [docs/06_plan/03_個人事業開始と法人化判定.md](docs/06_plan/03_個人事業開始と法人化判定.md) |
| 2 | **協力店1店で初回テスト診断**（オフラインのブラウザ版ツールで、その場で判定） | [初回サロン実施ガイド](docs/06_plan/06_初回サロン実施ガイド.md)、[tools/salon/check.html](tools/salon/check.html) |
| 3 | 協力店から2〜3店の紹介をもらい、W2〜3で計10店のヒアリング・テスト診断3件以上 | [サロン検証4週間計画](docs/06_plan/05_サロン検証4週間計画.md) |
| 4 | 商品が機能すると確認できたら（W3以降）、紹介でつながれる税理士事務所に打診 | 同上 第6節 |
