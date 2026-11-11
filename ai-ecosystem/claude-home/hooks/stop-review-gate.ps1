# Stop: このセッションでファイルを編集していたら、完了前に1回だけ検証・レビューの報告を求める。
# 無限ループ防止: stop_hook_active が true のときは何もしない。確認後は記録を .reviewed に改名し、新たな編集があるまで再発動しない。
$ErrorActionPreference = 'Stop'
try { [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false); [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch {}
function ConvertTo-AsciiJson([string]$s) { return [regex]::Replace($s, '[^\x00-\x7F]', { param($m) '\u{0:x4}' -f [int][char]$m.Value }) }
try {
  $in = [Console]::In.ReadToEnd() | ConvertFrom-Json
  if ($in.stop_hook_active -eq $true) { exit 0 }
  $sid = ([string]$in.session_id) -replace '[^A-Za-z0-9-]', ''
  $f = Join-Path $env:TEMP "ai-ecosystem-edits-$sid.txt"
  if (-not (Test-Path $f)) { exit 0 }
  $files = @(Get-Content -Encoding UTF8 $f | Sort-Object -Unique)
  Move-Item -Force $f "$f.reviewed"
  if ($files.Count -eq 0) { exit 0 }
  $reason = "[AI-Ecosystem 完了前チェック] このセッションで $($files.Count) 件のファイルを変更した。完了報告の前に次を確認し、報告に書くこと: " +
    "(1) 実行できるテスト・検証を実際に実行したか（実行していないものを成功と書かない） " +
    "(2) 重要な変更・成果物なら technical-qa または quality-reviewer サブエージェントで独立レビューしたか（軽微なら『軽微のため省略』と書く） " +
    "(3) Obsidian に残すべき決定・知見があれば /remember したか。確認済みならそのまま完了してよい。"
  [Console]::Out.Write((ConvertTo-AsciiJson (@{ decision = 'block'; reason = $reason } | ConvertTo-Json -Compress)))
  exit 0
} catch {
  [Console]::Error.Write("stop-review-gate: $($_.Exception.Message)")
  exit 1
}
