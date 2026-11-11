# PostToolUse (Edit|Write|NotebookEdit): 編集したファイルのパスだけを一時ファイルに記録する（内容は記録しない）。
# Obsidian の AI_Hub 内の編集（記憶の保存）は対象外。Stop フックが完了前のレビュー確認に使う。
$ErrorActionPreference = 'Stop'
try { [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false); [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch {}
try {
  $in = [Console]::In.ReadToEnd() | ConvertFrom-Json
  $path = [string]$in.tool_input.file_path
  if (-not $path) { $path = [string]$in.tool_input.notebook_path }
  if (-not $path) { exit 0 }
  $cfgPath = Join-Path $env:USERPROFILE '.claude\ai-ecosystem.json'
  if (Test-Path $cfgPath) {
    $hub = (Get-Content -Raw -Encoding UTF8 $cfgPath | ConvertFrom-Json).ai_hub
    if ($hub -and $path.ToLower().Replace('/', '\').StartsWith($hub.ToLower().Replace('/', '\'))) { exit 0 }
  }
  $sid = ([string]$in.session_id) -replace '[^A-Za-z0-9-]', ''
  Add-Content -Encoding UTF8 -Path (Join-Path $env:TEMP "ai-ecosystem-edits-$sid.txt") -Value $path
  exit 0
} catch {
  [Console]::Error.Write("track-edits: $($_.Exception.Message)")
  exit 1
}
