---
type: knowledge
status: 仮説
updated: {{DATE}}
---
# AI_ROUTING（どのAI・ツールを何に使うか）

> PHASE 0 の調査結果で「導入済み/未導入」を更新する。未導入・未承認のものは使わない。

| 用途 | 担当 | 状態 | 備考 |
|---|---|---|---|
| 司令塔・高度な推論・企画・重要な分析 | Claude Code（Claude Pro） | 導入予定 | APIキーは設定しない |
| 調査 | research-analyst（Claude サブエージェント） | 導入 | |
| 独立レビュー・Red Team | quality-reviewer（Claude サブエージェント） | 導入 | 別コンテキストで審査 |
| コード検査 | technical-qa（Claude サブエージェント） | 導入 | 編集権限なし |
| 別モデルによるコードレビュー | Codex CLI | 未確認 | ChatGPT の有料プラン等が必要な可能性。費用を確認してから判断 |
| 長文レビュー・Google Workspace | Gemini CLI / Antigravity | 未確認 | 無料枠と利用条件を確認してから判断 |
| 軽い分類・整形・抽出 | ローカル Qwen（Ollama） | 未確認 | VRAM 6GB。7B の量子化モデルまで。重要判断には使わない |
| 最終意思決定 | 人間 | — | |

## 判断の原則
- 1つの仕事に複数AIを並列で使わない。難易度・費用・期待効果で選ぶ
- 追加費用が発生するものは、持ち主の承認なしに使わない
