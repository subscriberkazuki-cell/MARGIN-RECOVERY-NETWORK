# 個人AIエコシステム（Claude Code 司令塔 × Obsidian 長期記憶）

Windows PC 上の Claude Code を司令塔に、専門エージェント・スキル・安全装置・Obsidian の長期記憶を組み合わせる構成一式。
**現状：構成はできているが、PC にはまだ適用していない。**（理由と詳細は [docs/SETUP_REPORT.md](docs/SETUP_REPORT.md)）

## できるようになること
- 「〜を調べて」「NVDA を A分析で」「この事業はいける？」「この機能を作って」「この動画を記事にして」と頼むだけで、分解 → 専門エージェント → 検証 → 別エージェントの審査 → 修正 → 成果物 → 記憶保存まで進む
- 過去の決定・判断基準・プロジェクトの状況を Obsidian から必要な分だけ読み出して使う
- 送信・公開・push・課金・削除・インストールは必ず止まって確認する（文章ではなく権限設定とフックで制御）

## 中身
| フォルダ | 内容 |
|---|---|
| `phase0/` | PC の現状調査スクリプト（読み取り専用） |
| `claude-home/` | `%USERPROFILE%\.claude` に入る設定：CLAUDE.md、agents（3）、skills（7）、hooks（4＋自己テスト）、settings の雛形 |
| `obsidian-template/AI_Hub/` | Vault に追加する記憶の構造（USER_PROFILE・PROJECT_INDEX・MEMORY_INDEX・DECISIONS ほか） |
| `install/install.ps1` | 非破壊インストーラー（既定は計画表示のみ） |
| `docs/` | SYSTEM_ARCHITECTURE・WORKFLOWS・SETUP_REPORT・CHANGELOG |
| `tests/` | 構造とガード判定のテスト（`python3 -m unittest discover -s tests`） |

## セットアップ（PC で行う。所要 約15分）
1. **このフォルダを PC に置く**（GitHub からダウンロード、または `git clone`）
2. **PHASE 0：現状調査**（変更なし・約1分）
   ```powershell
   cd <このフォルダ>\phase0
   powershell -NoProfile -ExecutionPolicy Bypass -File .\phase0_diagnose.ps1
   ```
   できた `phase0_report.md` を確認する
3. **PC 上で Claude Code を起動**し、こう伝える：「ai-ecosystem フォルダの README と phase0/phase0_report.md を読んで、PHASE 1 から進めて」
   - Claude Code が未導入なら：PowerShell で `irm https://claude.ai/install.ps1 | iex`（公式）→ `claude` を起動して Claude Pro でログイン
4. Claude Code が Vault を特定し、インストーラーの計画（`install.ps1 -VaultPath ...`、変更なし）を見せる → 内容を確認して承認すると `-Apply` で適用
5. 自己テスト：`powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\hooks\ai-ecosystem\test-hooks.ps1"`
6. PHASE 6 の検証（SETUP_REPORT の表）を Claude Code と一緒に行う

## 起動・停止・復旧
| 操作 | 方法 |
|---|---|
| 起動 | 作業したいフォルダで `claude`（スマホから使うなら後で `claude --remote-control`） |
| 停止 | `/exit` または Ctrl+C（常駐プロセスはない） |
| 状態確認 | セッション内で `/status`（ログイン方法）、`/memory`、`/agents`、`/hooks`、`claude doctor` |
| フックを一時的に止める | `%USERPROFILE%\.claude\settings.json` の `hooks` 節を外す（変更前にコピーを取る） |
| 元に戻す | `%USERPROFILE%\.claude\backups\ai-ecosystem-日時\` に変更前のファイルがある。それを元の場所に戻す。追加したファイル（agents・skills の7＋3、hooks\ai-ecosystem、ai-ecosystem.json、Vault の AI_Hub）は削除すれば元通り |

## 費用
初期構成は追加費用 0円（Claude Pro の範囲内）。`ANTHROPIC_API_KEY` は設定しない（設定すると API 課金側が使われうる）。外部AI・MCP は費用と条件を確認し、承認を得てから追加する。

## 関連ドキュメント
- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) — 構成図・役割分担・記憶設計・安全の仕組み
- [docs/WORKFLOWS.md](docs/WORKFLOWS.md) — 調査・株式・事業・コンテンツ・開発の流れ
- [docs/SETUP_REPORT.md](docs/SETUP_REPORT.md) — 現状・PHASE 1 の暫定判断・検証表
- [docs/CHANGELOG.md](docs/CHANGELOG.md)
- 記憶の雛形：`obsidian-template/AI_Hub/00_Home/USER_PROFILE.md`、`PROJECT_INDEX.md`
