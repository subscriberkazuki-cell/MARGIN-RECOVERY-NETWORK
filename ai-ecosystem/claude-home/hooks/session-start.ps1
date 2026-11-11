# SessionStart: AI_Hub の場所と、記憶の索引（短い要約）だけを渡す。全記憶は読み込まない。
# 設定: %USERPROFILE%\.claude\ai-ecosystem.json（インストーラーが作成）
$ErrorActionPreference = 'Stop'
try { [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false); [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch {}
try {
  $cfgPath = Join-Path $env:USERPROFILE '.claude\ai-ecosystem.json'
  if (-not (Test-Path $cfgPath)) { exit 0 }
  $cfg = Get-Content -Raw -Encoding UTF8 $cfgPath | ConvertFrom-Json
  $hub = $cfg.ai_hub
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add("[AI-Ecosystem] 長期記憶（Obsidian）: $hub")
  $lines.Add("記憶の使い方: 必要なときだけ 00_Home/MEMORY_INDEX.md と PROJECT_INDEX.md から辿って該当ノートを読む。保存は /remember。")
  foreach ($name in @('PROJECT_INDEX.md', 'MEMORY_INDEX.md')) {
    $f = Join-Path $hub "00_Home\$name"
    if (Test-Path $f) {
      $body = (Get-Content -Encoding UTF8 $f | Where-Object { $_ -notmatch '^\s*$' } | Select-Object -First 40) -join "`n"
      if ($body.Length -gt 3000) { $body = $body.Substring(0, 3000) + "`n…（以下省略。必要ならファイルを読む）" }
      $lines.Add("--- $name（先頭のみ） ---")
      $lines.Add($body)
    }
  }
  # 古い編集記録（2日以上前）を掃除
  Get-ChildItem $env:TEMP -Filter 'ai-ecosystem-edits-*' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-2) } | Remove-Item -Force -ErrorAction SilentlyContinue
  [Console]::Out.Write(($lines -join "`n"))
  exit 0
} catch {
  [Console]::Error.Write("session-start: $($_.Exception.Message)")
  exit 1
}
