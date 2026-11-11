# CHANGELOG

## 0.1.0 — 2026-11-11（クラウド側で作成。PC への適用前）
- PHASE 0 の読み取り専用の調査スクリプト（`phase0/phase0_diagnose.ps1`）
- Claude Code 設定一式：CLAUDE.md、サブエージェント3つ（research-analyst / quality-reviewer / technical-qa）、スキル7つ（research / stock-a / stock-b / business-review / project-build / content-production / remember）、フック4つ（SessionStart / PreToolUse ガード / PostToolUse 編集記録 / Stop 完了前チェック）、権限設定の雛形
- Obsidian AI_Hub の雛形（00_Home〜90_Archive、USER_PROFILE・PROJECT_INDEX・MEMORY_INDEX・DECISIONS・AI_ROUTING）
- 非破壊インストーラー（既定は計画表示のみ、既存ファイルは上書きしない、変更時はバックアップ）
- テスト：ガード判定パターン（Python で検証）、キット構造の検査。Windows 上の実動作は `test-hooks.ps1` で PHASE 6 に確認
- 仕様は 2026-11-11 時点の公式ドキュメント（code.claude.com/docs）で確認
