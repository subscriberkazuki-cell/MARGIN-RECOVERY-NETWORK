<#
  PHASE 0：PC現状調査（読み取り専用）
  - 何もインストール・変更・削除しない。外部への送信もしない。
  - 秘密情報（APIキー・トークン・認証ファイルの中身）は表示しない。存在の有無だけを書く。
  - 結果はカレントフォルダの phase0_report.md に保存する（この1ファイルの作成だけが唯一の書き込み）。

  実行方法（PowerShell を開いて、このファイルのあるフォルダで）：
    powershell -NoProfile -ExecutionPolicy Bypass -File .\phase0_diagnose.ps1
  ※ -ExecutionPolicy Bypass はこの1回の実行にだけ効く（PCの設定は変わらない）。

  Windows PowerShell 5.1 互換で書いている。
#>
$ErrorActionPreference = 'SilentlyContinue'
$out = New-Object System.Collections.Generic.List[string]
function Add([string]$s) { $out.Add($s) }
function H([string]$s) { Add ''; Add "## $s"; Add '' }
function Mask([string]$s) {
  if (-not $s) { return $s }
  return ($s -replace '(?i)("?[A-Za-z0-9_]*(key|token|secret|password|auth)[A-Za-z0-9_]*"?\s*[:=]\s*)"?[^",\s}]+"?', '$1"***"')
}
function Run([string]$exe, [string[]]$argv, [int]$timeoutSec = 20) {
  if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { return '（見つからない）' }
  $job = Start-Job -ScriptBlock { param($e, $a) & $e @a 2>&1 | Out-String } -ArgumentList $exe, $argv
  if (Wait-Job $job -Timeout $timeoutSec) { $r = Receive-Job $job } else { Stop-Job $job; $r = "（$timeoutSec 秒でタイムアウト）" }
  Remove-Job $job -Force
  return (Mask ($r | Out-String).Trim())
}
function Exists([string]$p) { if (Test-Path -LiteralPath $p) { 'あり' } else { 'なし' } }

Add "# PHASE 0 調査レポート"
Add ""
Add "- 実行日時: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Add "- ユーザー: $env:USERNAME（ホームフォルダ: $env:USERPROFILE）"
Add "- このレポートに秘密情報は含めていない（キー・トークンは存在の有無のみ）。共有前に念のため目視確認すること。"

H '1. Windows・ハードウェア'
$os = Get-CimInstance Win32_OperatingSystem
Add "- OS: $($os.Caption) / バージョン $($os.Version) / ビルド $($os.BuildNumber) / $($os.OSArchitecture)"
Add "- PowerShell: $($PSVersionTable.PSVersion)"
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
Add "- CPU: $($cpu.Name)（コア $($cpu.NumberOfCores) / スレッド $($cpu.NumberOfLogicalProcessors)）"
Add ("- メモリ: {0:N1} GB（空き {1:N1} GB）" -f ($os.TotalVisibleMemorySize / 1MB), ($os.FreePhysicalMemory / 1MB))
foreach ($g in Get-CimInstance Win32_VideoController) { Add "- GPU: $($g.Name) / ドライバ $($g.DriverVersion)" }
$smi = Run 'nvidia-smi' @('--query-gpu=name,memory.total,memory.used,driver_version', '--format=csv,noheader')
Add "- nvidia-smi: $smi"

H '2. ストレージ'
Add '| ドライブ | 合計 | 使用 | 空き |'
Add '|---|---:|---:|---:|'
foreach ($d in Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3') {
  Add ("| {0} | {1:N0} GB | {2:N0} GB | {3:N0} GB |" -f $d.DeviceID, ($d.Size / 1GB), (($d.Size - $d.FreeSpace) / 1GB), ($d.FreeSpace / 1GB))
}

H '3. 開発ツール'
Add "- Node.js: $(Run 'node' @('--version'))"
Add "- npm: $(Run 'npm' @('--version'))"
Add "- Python: $(Run 'python' @('--version'))"
Add "- py ランチャー: $(Run 'py' @('--version'))"
Add "- Git: $(Run 'git' @('--version'))"
$gitBash = @("$env:ProgramFiles\Git\bin\bash.exe", "${env:ProgramFiles(x86)}\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
Add "- Git Bash: $(if ($gitBash) { $gitBash } else { '見つからない（Claude Code の Bash ツールは使えず PowerShell ツールになる）' })"
Add "- WSL: $(Run 'wsl' @('--status') 10)"
Add "- winget: $(Run 'winget' @('--version'))"

H '4. Claude Code'
Add "- claude コマンド: $(Run 'claude' @('--version'))"
Add "- claude の場所: $((Get-Command claude -ErrorAction SilentlyContinue).Source)"
$cdir = Join-Path $env:USERPROFILE '.claude'
Add "- 設定フォルダ $cdir : $(Exists $cdir)"
Add "- 認証ファイル（.credentials.json）: $(Exists (Join-Path $cdir '.credentials.json'))（中身は読まない）"
foreach ($v in 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CONFIG_DIR', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX') {
  $set = @([Environment]::GetEnvironmentVariable($v, 'Process'), [Environment]::GetEnvironmentVariable($v, 'User'), [Environment]::GetEnvironmentVariable($v, 'Machine')) | Where-Object { $_ }
  Add "- 環境変数 $v : $(if ($set) { '設定あり（値は表示しない）※ ANTHROPIC_API_KEY があると Pro ではなく API 課金側が使われる可能性' } else { 'なし' })"
}
Add "- CLAUDE.md（ユーザー）: $(Exists (Join-Path $cdir 'CLAUDE.md'))"
$cm = Join-Path $cdir 'CLAUDE.md'
if (Test-Path $cm) { Add "  - 行数: $((Get-Content $cm).Count)" }
$sj = Join-Path $cdir 'settings.json'
Add "- settings.json（ユーザー）: $(Exists $sj)"
if (Test-Path $sj) { Add '```json'; Add (Mask (Get-Content $sj -Raw)); Add '```' }
foreach ($sub in 'agents', 'skills', 'commands', 'hooks', 'rules', 'plugins') {
  $p = Join-Path $cdir $sub
  if (Test-Path $p) {
    $names = (Get-ChildItem $p -Name | Select-Object -First 50) -join ', '
    Add "- $sub/: $names"
  } else { Add "- $sub/: なし" }
}
$cj = Join-Path $env:USERPROFILE '.claude.json'
Add "- ~/.claude.json: $(Exists $cj)"
if (Test-Path $cj) {
  try {
    $j = Get-Content $cj -Raw | ConvertFrom-Json
    $mcp = @()
    if ($j.mcpServers) { $mcp += $j.mcpServers.PSObject.Properties | ForEach-Object { "$($_.Name)（ユーザー）" } }
    if ($j.projects) {
      foreach ($pp in $j.projects.PSObject.Properties) {
        if ($pp.Value.mcpServers) { $mcp += $pp.Value.mcpServers.PSObject.Properties | ForEach-Object { "$($_.Name)（$($pp.Name)）" } }
      }
      Add "- Claude Code を使ったことのあるフォルダ数: $(@($j.projects.PSObject.Properties).Count)"
    }
    Add "- 設定済みMCPサーバー: $(if ($mcp) { $mcp -join ', ' } else { 'なし' })"
  } catch { Add '- ~/.claude.json の読み取りに失敗' }
}
Add "- claude mcp list: $(Run 'claude' @('mcp', 'list') 30)"

H '5. Obsidian'
$obsExe = @("$env:LOCALAPPDATA\Programs\Obsidian\Obsidian.exe", "$env:LOCALAPPDATA\Obsidian\Obsidian.exe", "$env:ProgramFiles\Obsidian\Obsidian.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
Add "- Obsidian 本体: $(if ($obsExe) { $obsExe } else { '既定の場所に見つからない' })"
$oj = Join-Path $env:APPDATA 'obsidian\obsidian.json'
Add "- Obsidian 設定（obsidian.json）: $(Exists $oj)"
if (Test-Path $oj) {
  try {
    $o = Get-Content $oj -Raw | ConvertFrom-Json
    Add ''
    Add '| Vault のパス | 存在 | 最後に開いていた | .md の数 |'
    Add '|---|---|---|---:|'
    foreach ($v in $o.vaults.PSObject.Properties) {
      $vp = $v.Value.path
      $n = if (Test-Path $vp) { (Get-ChildItem $vp -Recurse -Filter *.md -File -ErrorAction SilentlyContinue | Measure-Object).Count } else { 0 }
      Add "| $vp | $(Exists $vp) | $(if ($v.Value.open) { 'はい' } else { '' }) | $n |"
    }
  } catch { Add '- obsidian.json の読み取りに失敗' }
}
# 既知の場所に .obsidian フォルダがあるか（深さ3まで・限定範囲のみ）
$roots = @("$env:USERPROFILE\Documents", "$env:USERPROFILE\OneDrive", "$env:USERPROFILE\OneDrive\Documents", "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Obsidian") | Where-Object { Test-Path $_ }
$found = foreach ($r in $roots) { Get-ChildItem $r -Directory -Recurse -Depth 3 -Filter '.obsidian' -Force -ErrorAction SilentlyContinue | ForEach-Object { $_.Parent.FullName } }
Add ''
Add "- 限定範囲（Documents / OneDrive / Desktop / Obsidian）で見つかった Vault 候補: $(if ($found) { ($found | Select-Object -Unique) -join ' ; ' } else { 'なし' })"

H '6. Muse AI'
$uninst = @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
$apps = Get-ItemProperty $uninst -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName } | Select-Object DisplayName, DisplayVersion, InstallLocation
$muse = $apps | Where-Object { $_.DisplayName -match '(?i)muse' }
Add "- インストール済みアプリ（名前に Muse を含む）: $(if ($muse) { ($muse | ForEach-Object { "$($_.DisplayName) $($_.DisplayVersion) [$($_.InstallLocation)]" }) -join ' ; ' } else { 'なし' })"
$appx = Get-AppxPackage -Name '*muse*' -ErrorAction SilentlyContinue
Add "- ストアアプリ（Muse）: $(if ($appx) { ($appx | ForEach-Object { "$($_.Name) $($_.Version)" }) -join ' ; ' } else { 'なし' })"
$museDirs = foreach ($r in @($env:APPDATA, $env:LOCALAPPDATA, "$env:LOCALAPPDATA\Programs")) { Get-ChildItem $r -Directory -Filter '*muse*' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName } }
Add "- データフォルダ候補（AppData 直下の *muse*）: $(if ($museDirs) { $museDirs -join ' ; ' } else { 'なし' })"

H '7. ローカルAI・他のAIツール'
Add "- Ollama: $(Run 'ollama' @('--version'))"
Add '- Ollama のモデル一覧:'
Add '```'
Add (Run 'ollama' @('list') 20)
Add '```'
Add "- LM Studio: $(if ($apps | Where-Object { $_.DisplayName -match '(?i)LM Studio' }) { 'インストール済み' } else { 'なし' })"
Add "- Codex CLI: $(Run 'codex' @('--version'))"
Add "- Gemini CLI: $(Run 'gemini' @('--version'))"
$ag = $apps | Where-Object { $_.DisplayName -match '(?i)antigravity' }
Add "- Google Antigravity: $(if ($ag) { ($ag | ForEach-Object { "$($_.DisplayName) $($_.DisplayVersion)" }) -join ' ; ' } else { 'なし' })"
Add "- その他のAI関連アプリ: $((($apps | Where-Object { $_.DisplayName -match '(?i)(claude|chatgpt|openai|cursor|copilot|gemini|ollama|docker)' }).DisplayName | Sort-Object -Unique) -join ' ; ')"
$npmg = Run 'npm' @('ls', '-g', '--depth=0') 30
Add '- npm グローバルパッケージ:'
Add '```'
Add $npmg
Add '```'

H '8. 次の手順'
Add '- このファイルの内容を確認し、問題なければ Claude Code（PC上のセッション）に「phase0_report.md を読んで PHASE 1 に進んで」と伝える。'

$path = Join-Path (Get-Location) 'phase0_report.md'
$out | Out-File -FilePath $path -Encoding utf8
Write-Host "完了: $path"
