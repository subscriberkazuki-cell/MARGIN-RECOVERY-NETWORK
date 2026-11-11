# SETUP_REPORT

更新：2026-11-11 ／ 状態：**PHASE 0 未実施（PC 上での実行待ち）**。構成一式はクラウド側で作成・検証済み、PC への適用前。

## 1. 正直な現状

| 項目 | 状態 |
|---|---|
| PC の実機調査（PHASE 0） | **未実施**。この作業はクラウド上の Claude Code セッションで行ったため、Windows PC に接続できなかった（PC のフォルダが共有されていない）。`phase0/phase0_diagnose.ps1` を PC で実行して行う |
| Obsidian Vault の場所 | **未確認**。PHASE 0 の結果で特定する（推測で選ばない） |
| Muse AI | **未確認**。PHASE 0 でインストール状況・データの場所を調べる。連携手段が見つからなければ連携しない |
| 参考動画（KEITO【AI&WEB ch】2026-11-07） | 視聴していない。持ち主の要約にもとづいて設計 |
| 「Jev（TypeSafe Jev）」 | 一般に入手できる製品か確認できていない。指示どおり、別コンテキストの quality-reviewer / technical-qa と機械的な検証（テスト・Stop フック）で代替 |
| Claude Code の仕様 | 2026-11-11 に公式ドキュメント（skills / sub-agents / hooks / settings / permissions / memory / mcp / setup / authentication / remote-control）で確認して設定を作成 |
| ガードの判定パターン | Python で 50 件のテスト（拒否22・確認16・通過12）に合格 |
| PowerShell スクリプトの実動作 | **未検証**（このクラウド環境では PowerShell を使えなかった）。PC で `test-hooks.ps1` を実行して確認する |

## 2. PHASE 1 の暫定判断（PHASE 0 の結果で確定する）

### 初期導入するもの
| ツール | 判断 | 費用 |
|---|---|---|
| Claude Code（Claude Pro でログイン） | 導入（未導入なら公式の PowerShell インストーラー or WinGet） | 追加なし |
| Git for Windows | 推奨（Claude Code の Bash ツールが使える。無くても PowerShell ツールで動く） | 無料 |
| Obsidian（既存 Vault） | 使用 | 無料 |
| 本キット（設定・スキル・エージェント・フック） | 導入 | 無料 |

### 条件付き（PHASE 0 の結果と持ち主の承認で判断）
| ツール | 条件 | 想定費用 |
|---|---|---|
| Codex CLI | 既に使える契約があり、追加費用なしで使える場合のみ。独立コードレビュー用 | 契約次第（要確認） |
| Gemini CLI / Google Antigravity | 無料枠・利用条件を公式で確認してから。長文レビュー・Google Workspace 用 | 要確認 |
| Google Workspace MCP | 公式の参加要件（Developer Preview 等）を確認してから | 要確認 |
| Ollama＋Qwen2.5 7B（既存） | 既に入っていれば軽量処理に限って使う。新しいモデルは承認なしにダウンロードしない | 無料（電気代のみ） |
| GitHub 連携 | 既存プロジェクトで必要になったとき（gh CLI または GitHub MCP） | 無料 |
| ブラウザ操作（Playwright 等） | 必要な業務が出たとき | 無料 |
| 字幕取得ツール（yt-dlp 等） | /content-production で使う場合。導入は承認後 | 無料 |
| Remote Control（スマホから操作） | 基本環境が安定してから。Pro で利用可、PC で claude が動いている必要あり | 追加なし |

### 不要と判断したもの（現時点）
| ツール | 理由 |
|---|---|
| Discord Bot・常時稼働サーバー | 指示どおり、基本環境の安定後に検討 |
| OpenClaw・Hermes 等の常時稼働エージェント | 必要性が確認できていない。権限管理が複雑になる |
| 動画の全部入りツール群（Remotion・HyperFrames 等） | 実際に動画制作を自動化する段階で個別に判断 |
| Obsidian 専用 MCP | Vault は通常のファイル操作で読み書きできるため不要 |
| Activepieces・n8n 等 | Claude Code のスキル＋フックで足りる間は不要 |

### 想定される追加費用
- 初期構成：**0円**（Claude Pro の範囲内）
- 注意：Claude Pro には利用枠がある。サブエージェントを多用すると枠を早く消費するため、同時2体まで・簡単な作業には使わないルールにしている

## 3. 実装ロードマップ
| PHASE | 内容 | 担当 | 状態 |
|---|---|---|---|
| 0 | PC の実機調査（読み取り専用） | 持ち主がスクリプトを実行（約1分） | 未実施 |
| 1 | 構成の確定（Vault の決定、外部AIの採否） | Claude（PC 上のセッション） | 暫定案あり（本書） |
| 2 | 基本環境：インストーラーで追加（既存は上書きしない） | Claude が計画を表示 → 持ち主が承認 | 準備済み |
| 3 | 外部AI・MCP（必要なものだけ・承認後） | Claude＋持ち主 | 未着手 |
| 4 | 品質管理（Reviewer・Red Team・フック）の実動作テスト | Claude | 準備済み（test-hooks.ps1） |
| 5 | 業務ワークフロー（調査 → 株式 → 事業 → 開発 → コンテンツ） | Claude | スキル作成済み |
| 6 | 最終検証（下の表） | Claude＋持ち主 | 未実施 |

## 4. PHASE 6 の検証項目（PC 上で実施して結果を記入）
| # | 検証 | 方法 | 結果 |
|---|---|---|---|
| 1 | Obsidian の情報を読める | 「PROJECT_INDEX を読んで状況を教えて」 | |
| 2 | 新しい記憶を保存できる | 「/remember テスト：好きな色は青」 | |
| 3 | 次のセッションで取得できる | 新しいセッションで「私の好きな色は？」 | |
| 4 | スキルを呼び出せる | `/research Claude Code のスキル機能` | |
| 5 | サブエージェントを使える | 「research-analyst に〜を調べさせて」 | |
| 6 | レビューが動く | 「quality-reviewer にこの文章を審査させて」 | |
| 7 | 危険な操作を止める | `test-hooks.ps1` の全項目が OK | |
| 8 | 既存ファイルを壊さない | インストーラーの計画表示で「上書き」がないこと、バックアップの確認 | |
| 9 | 余計な従量課金がない | `/status` で Claude Pro のログインが使われていること、ANTHROPIC_API_KEY が無いこと | |
| 10 | 日本語が文字化けしない | ガードが止めたときの理由表示・起動時の索引表示 | |
