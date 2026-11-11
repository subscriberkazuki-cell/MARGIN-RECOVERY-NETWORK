# PreToolUse ガード（Bash / PowerShell ツール）。Windows PowerShell 5.1 互換。
# 危険なコマンドは deny、確認が必要なものは ask を返す。該当なしは何も出力せず終了（通常の権限判定に任せる）。
# 判定パターン: 同じフォルダの guard-patterns.json
$ErrorActionPreference = 'Stop'
try { [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false); [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch {}
function ConvertTo-AsciiJson([string]$s) { return [regex]::Replace($s, '[^\x00-\x7F]', { param($m) '\u{0:x4}' -f [int][char]$m.Value }) }
try {
  $raw = [Console]::In.ReadToEnd()
  $in = $raw | ConvertFrom-Json
  $cmd = [string]$in.tool_input.command
  if (-not $cmd) { exit 0 }
  $pat = Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot 'guard-patterns.json') | ConvertFrom-Json
  $opt = [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
  foreach ($level in @('deny', 'ask')) {
    foreach ($p in $pat.$level) {
      if ([regex]::IsMatch($cmd, $p.re, $opt)) {
        $reason = "[AI-Ecosystem ガード:$($p.id)] $($p.why)。" + $(if ($level -eq 'deny') { 'この操作は自動では実行しない。必要なら人間が自分で実行する。' } else { '人間の確認が必要。' })
        $o = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = $level; permissionDecisionReason = $reason } }
        [Console]::Out.Write((ConvertTo-AsciiJson ($o | ConvertTo-Json -Depth 5 -Compress)))
        exit 0
      }
    }
  }
  exit 0
} catch {
  # ガード自体の故障で作業が止まらないよう、失敗時は通常の権限判定に任せる（permissions の deny/ask は別途効いている）
  [Console]::Error.Write("guard-pretooluse: $($_.Exception.Message)")
  exit 1
}
