# 引継ぎプロンプト（ローカルの Claude Code セッションに貼り付ける）

以下の「---」から下をすべてコピーして、PC 上（ローカル環境）の Claude Code の入力欄に貼り付けて送信する。

---

# 引継ぎ：Windows AIエコシステム構築（PHASE 0 から再開）

あなたは私の Windows PC 上で動いている Claude Code です。以前、クラウド上の Claude Code セッションでこのプロジェクトを進めましたが、そのセッションからは PC に接続できなかったため、ここから引き継ぎます。以下を読んで、PHASE 0 から順に進めてください。日本語で、結論から報告してください。

## 1. 目的
Claude Code を司令塔に、専門サブエージェント・スキル・外部ツール・品質検査・Obsidian の長期記憶を組み合わせた個人専用のAIエコシステムを、この PC に構築する。基本原則は「指示 → タスク分解 → 専門エージェント → 外部ツール → 品質検査 → 修正 → 成果物 → 記憶保存」。元の詳細な指示書の要点はこのプロンプトと構成一式のドキュメントに反映済み。

## 2. 構成一式の場所（作成済み。作り直さないこと）
- GitHub：`subscriberkazuki-cell/MARGIN-RECOVERY-NETWORK` の `claude/sharp-planck-twsbwy` ブランチ、`ai-ecosystem/` フォルダ
- 取り込み方：Git があれば `git clone -b claude/sharp-planck-twsbwy https://github.com/subscriberkazuki-cell/MARGIN-RECOVERY-NETWORK.git`。Git が無ければ、Git を入れるか ZIP でダウンロードするかを私に確認する（インストールは承認が必要）
- 最初に読むもの：`ai-ecosystem/README.md`、`ai-ecosystem/docs/SETUP_REPORT.md`、`ai-ecosystem/docs/SYSTEM_ARCHITECTURE.md`、`ai-ecosystem/docs/WORKFLOWS.md`

### 中身
| 場所 | 内容 |
|---|---|
| `phase0/phase0_diagnose.ps1` | PHASE 0 の調査スクリプト（読み取り専用。`phase0_report.md` を1つ作るだけ） |
| `claude-home/CLAUDE.md` | 毎回の基本方針（`{{AI_HUB}}` はインストーラーが置換） |
| `claude-home/agents/` | research-analyst（調査）、quality-reviewer（独立審査・Red Team）、technical-qa（テスト・コード検査）。3つとも編集権限なし |
| `claude-home/skills/` | /research、/stock-a、/stock-b、/business-review、/project-build、/content-production、/remember |
| `claude-home/hooks/` | PowerShell フック：guard-pretooluse（危険コマンドを deny/ask、判定は guard-patterns.json）、session-start（AI_Hub の索引の先頭だけ渡す）、track-edits（編集ファイルのパスだけ記録）、stop-review-gate（変更があれば完了前に1回だけ検証・レビューを確認。stop_hook_active でループ防止）、test-hooks.ps1（Windows 用の自己テスト） |
| `claude-home/settings.template.json` | 権限（deny：.env・認証ファイル・~/.ssh・*.pem・強制push、ask：push・削除・デプロイ）、defaultMode=default、disableBypassPermissionsMode=disable、フック定義（powershell.exe の exec 形式）、`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` |
| `obsidian-template/AI_Hub/` | 00_Home（AI_HOME・USER_PROFILE・PROJECT_INDEX・MEMORY_INDEX・DECISIONS）、01_Projects（THEMORA・FRED・Bookmap_BOT・Investment・Startup・Content）、02_Knowledge（AI_Tools/AI_ROUTING ほか）、03_Research、04_Outputs、05_Daily、90_Archive |
| `install/install.ps1` | 非破壊インストーラー。既定は計画表示のみ、`-Apply` で実行。無いファイルだけ追加。既存の CLAUDE.md・settings.json は変更せず、別名ファイル（ai-ecosystem.CLAUDE.md、settings.ai-ecosystem.proposed.json）を作る。`-AddClaudeMdImport`・`-MergeSettings` を付けたときだけバックアップを取って統合。バックアップ先は `%USERPROFILE%\.claude\backups\ai-ecosystem-日時\` |
| `tests/` | Python のテスト（ガード判定50件、構造検査）：`python -m unittest discover -s tests` |

## 3. これまでに検証済みのこと／未検証のこと
- 検証済み：Claude Code の仕様は 2026-11-11 時点の公式ドキュメント（skills / sub-agents / hooks / settings / permissions / memory / mcp / setup / authentication / remote-control）で確認して作成。ガードの判定パターンは Python で50件のテストに合格。キットの構造テストに合格
- **未検証（ここで最初に確認すること）**：
  - PowerShell スクリプトの実動作（クラウドでは PowerShell を使えなかった）→ インストール後に `test-hooks.ps1` を実行
  - Windows PowerShell 5.1 での日本語の扱い：.ps1 は UTF-8 BOM 付き・CRLF にしてある。フックは入出力を UTF-8 に設定し、JSON 出力は非ASCIIを \uXXXX にエスケープしている。SessionStart はプレーンテキスト出力なので、起動時の索引表示が文字化けしないか確認する
  - SessionStart の additionalContext の JSON 形式は公式で確認しきれなかったため、プレーンテキスト出力（公式に「SessionStart の標準出力は文脈に追加される」とある方式）にしている
  - settings.json の `additionalDirectories` に Windows の絶対パスを入れる書き方が通るか
- 参考動画（KEITO【AI&WEB ch】2026-11-07）は視聴していない。「Jev（TypeSafe Jev）」は一般に入手できる製品として確認できなかったため、quality-reviewer / technical-qa と機械的な検証（テスト・Stop フック）で代替した

## 4. 進め方（この順番で）
1. **PHASE 0（変更なし）**：構成一式を取り込み、`phase0/phase0_diagnose.ps1` を実行（`powershell -NoProfile -ExecutionPolicy Bypass -File .\phase0_diagnose.ps1`）。結果を要約して報告。調べる項目：Windows のバージョン、CPU・GPU（nvidia-smi）・メモリ、空き容量、Claude Code のバージョンとログイン方法（`/status`）、`ANTHROPIC_API_KEY` などの環境変数の有無（値は表示しない）、Node・Python・Git・Git Bash、Obsidian と Vault（`%APPDATA%\obsidian\obsidian.json` と、Documents・OneDrive・Desktop の限定範囲のみ）、Muse AI（インストール状況・データの場所・Obsidian/MCP/API 連携の可否）、Ollama と Qwen2.5:7b-instruct-q3_K_M、Codex CLI、Gemini CLI・Google Antigravity、既存の ~/.claude 設定（CLAUDE.md・settings・agents・skills・hooks・MCP）
2. **PHASE 1**：調査結果で `docs/SETUP_REPORT.md` の暫定判断を確定する（診断書、導入済み一覧、不足機能、構成図、初期導入、不要と判断したもの、追加費用、ロードマップ）。**Vault が複数あれば候補を示して1回だけ私に確認する。推測で選ばない。見つからなければ新しい Vault を勝手に作らず相談する**
3. **PHASE 2**：`install.ps1 -VaultPath "<確定したVault>"` で計画を表示して私に見せる → 承認後に `-Apply`。既存の CLAUDE.md・settings.json がある場合は、統合案の中身を見せてから `-AddClaudeMdImport` / `-MergeSettings` を判断。USER_PROFILE・PROJECT_INDEX を実機の情報で更新
4. **PHASE 3**：Codex・Gemini/Antigravity・ローカル Qwen・GitHub・ブラウザ操作・MCP は、必要性・費用・安全性を示して承認を取ったものだけ。Google Workspace MCP は公式の参加条件（https://developers.google.com/workspace/guides/configure-mcp-servers）を確認してから。Obsidian はファイル操作で足りるので専用 MCP は入れない
5. **PHASE 4**：`test-hooks.ps1` の全項目、quality-reviewer・technical-qa の実動作を確認
6. **PHASE 5**：ワークフローを優先順（調査 → 株式 → 新規事業 → 開発 → コンテンツ）に実際に1回ずつ試す
7. **PHASE 6**：SETUP_REPORT の検証表（10項目）を実施して結果を記入。CHANGELOG を更新

## 5. 必ず守ること
- 読み取り専用の調査、新規の作業用フォルダ内で完結する作業は確認なしで進めてよい。不要な確認を繰り返さない
- **承認が必要**：ソフトウェア・モデルのインストールやダウンロード、有料契約、API従量課金、OAuth 認証、アカウント権限の変更、既存ファイル・既存設定の変更や削除、メール・SNS の送信、デプロイ・公開、GitHub への push・マージ、お金が動く操作
- Claude Pro の OAuth ログインを使う。`ANTHROPIC_API_KEY` を設定しない（設定されていたら報告する）
- `--dangerously-skip-permissions` や bypassPermissions を使わない
- 秘密情報（.env・APIキー・トークン・認証ファイルの中身）を表示・記録・コミットしない
- ローカルAIは VRAM 6GB の制約内で軽量処理のみ。新しいモデルを勝手にダウンロードしない。常時大量稼働させない
- サブエージェントの同時稼働は原則2体まで。修正は原則2回まで。実行していないテストを成功と報告しない
- 取引BOT は分析・研究まで。実際の売買判断と発注は人間が行う

## 6. 私について
- PC：Windows、AMD Ryzen 5 3600、RAM 32GB、GTX 1660 SUPER 6GB、ストレージ約2.27TB（使用約1.13TB。実測で確認）
- 契約：Claude Pro。Muse AI アプリを使用中。以前 Ollama で Qwen2.5:7b-instruct-q3_K_M を使っていた
- 好み：日本語、結論から、数字と事実にもとづいて忖度なし。自分の作業は最小限にしたい（コピペで済む形で指示がほしい）。ただし重要な操作は自分で承認する
- Claude デスクトップアプリの Remote Control に登録しているフォルダ：nandemonaimono、ClaudeCode_Backup_20261014_200223、株強弱（クラウドのセッションからは「not_available」で使えなかった。System32 も登録していたが危険なので外した）

### プロジェクト（AI_Hub の PROJECT_INDEX に反映済み）
- **Investment**：日米個別株の分析。/stock-a（指定ティッカー・決算期を厳守、一次資料優先、売上・営業利益・EPS・営業CF・FCF、利益を生む事業、成長ドライバー TOP1〜2 とセグメント寄与の定量化、中国依存・サプライチェーン・供給制約、KPI と市場予想の差、バリュエーション、ブル・ベア、Core Definition）、/stock-b（A の TOP1・TOP2 ごとに日米上場の競合を最大3社、100点満点：適合度25・顧客15・利益源泉15・テーマ10・事業重要度15・シェア10・CAPEX5・地域規制5、対象事業の売上構成比も示す、60点未満は除外、無理に埋めない）
- **THEMORA**：日米株の決算前後の株価変動・統計を提供する投資情報サービス
- **FRED**：暗号資産の Funding Rate アービトラージ（分析・配分・リスク管理・BOT・サイト/Discord 運営）
- **Bookmap_BOT**：Bookmap＋Python による BTC 先物の分析・自動化研究（Absorption、Failed Auction、Structure Break、CVD、Liquidity、約定・板情報）
- **Startup**：新規事業。現在は **MARGIN RECOVERY NETWORK**（同じリポジトリの `docs/`・`tools/salon/` に資料一式）。方針 v0.3：小規模サロン向け「定額・半自動の固定費チェック」（19,800円・返金保証つき、5分の質問票 → 決定論的プログラムで判定、税理士・記帳費用も相場比較）を4週間で検証中。EC配送費の監査は Phase 2。個人事業で開始。顧客の実データ（店名・金額）は生成AIに入力しないルール。協力店1店で初回テスト診断の予定（`docs/06_plan/07_あなたの作業_最小版.md`）。比較基準の月次更新はクラウド側の定期タスク（毎月1日）で実行中
- **Content**：株式決算予想の YouTube チャンネル、「なんでもないもの博物館」、SNS・ブログ・広告動画・サムネイル

## 7. 最初の返答でしてほしいこと
1. 構成一式を取り込める状態か（Git の有無）を確認し、必要なら方法を1つ提案する
2. 取り込めたら PHASE 0 のスクリプトを実行し、結果を「診断書」の形で報告する（Vault の候補を含む）
3. PHASE 1 で何を決める必要があるか（私が答える必要があるのは何か）を最小限にまとめる
