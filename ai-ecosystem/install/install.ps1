<#
  AI エコシステムのインストーラー（Windows PowerShell 5.1 互換）

  既定は「計画を表示するだけ」（何も変更しない）。-Apply を付けたときだけ実行する。
  - 追加するのは「まだ無いファイル」だけ。既存のファイルは上書きしない
  - 既存の CLAUDE.md / settings.json は変更しない（提案ファイルを別名で作る）
    -AddClaudeMdImport / -MergeSettings を付けたときだけ、バックアップを取ってから変更する
  - 例外：このキット専用の場所（~/.claude/hooks/ai-ecosystem/、~/.claude/ai-ecosystem.json）は、
    再インストール時にバックアップを取ってから更新する
  - バックアップ先：%USERPROFILE%\.claude\backups\ai-ecosystem-YYYYMMDD-HHMMSS\

  使い方（このファイルのあるフォルダで）：
    # 1) 計画を確認（変更なし）
    powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -VaultPath "C:\Users\me\Documents\MyVault"
    # 2) 実行
    powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -VaultPath "C:\Users\me\Documents\MyVault" -Apply
    # 3) 既存の CLAUDE.md / settings.json に統合する場合（内容を確認してから）
    ... -Apply -AddClaudeMdImport -MergeSettings
#>
param(
  [Parameter(Mandatory = $true)][string]$VaultPath,
  [switch]$Apply,
  [switch]$AddClaudeMdImport,
  [switch]$MergeSettings
)
$ErrorActionPreference = 'Stop'
$kit = Split-Path -Parent $PSScriptRoot
$src = Join-Path $kit 'claude-home'
$tpl = Join-Path $kit 'obsidian-template\AI_Hub'
$claudeDir = Join-Path $env:USERPROFILE '.claude'
$hooksDir = Join-Path $claudeDir 'hooks\ai-ecosystem'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = Join-Path $claudeDir "backups\ai-ecosystem-$stamp"
$today = Get-Date -Format 'yyyy-MM-dd'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$plan = New-Object System.Collections.Generic.List[object]

function Plan([string]$action, [string]$target, [string]$note = '') { $plan.Add([pscustomobject]@{ 操作 = $action; 対象 = $target; 補足 = $note }) }
function WriteText([string]$path, [string]$text) {
  $d = Split-Path -Parent $path
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
  [System.IO.File]::WriteAllText($path, $text, $utf8)
}
function Backup([string]$path) {
  $rel = $path.Substring($env:USERPROFILE.Length).TrimStart('\')
  $dst = Join-Path $backupDir $rel
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item -LiteralPath $path -Destination $dst -Force
}
function JsonPath([string]$p) { return $p.Replace('\', '\\') }

# ---------- 0. 前提チェック ----------
if (-not (Test-Path -LiteralPath $VaultPath)) { throw "Vault が見つからない: $VaultPath" }
if (-not (Test-Path -LiteralPath (Join-Path $VaultPath '.obsidian'))) { throw "Obsidian の Vault ではないようです（.obsidian フォルダがない）: $VaultPath" }
$VaultPath = (Resolve-Path -LiteralPath $VaultPath).Path
$hub = Join-Path $VaultPath 'AI_Hub'
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Warning 'claude コマンドが見つかりません。Claude Code の導入後に使えるようになります（インストール自体は続行できます）。' }

# ---------- 1. Obsidian AI_Hub（無いファイルだけ追加） ----------
foreach ($f in Get-ChildItem -LiteralPath $tpl -Recurse -File) {
  $rel = $f.FullName.Substring($tpl.Length).TrimStart('\')
  $dst = Join-Path $hub $rel
  if (Test-Path -LiteralPath $dst) { Plan 'そのまま' $dst '既存のノートを残す' }
  else { Plan '追加' $dst; if ($Apply) { WriteText $dst ((Get-Content -Raw -Encoding UTF8 $f.FullName).Replace('{{DATE}}', $today)) } }
}
foreach ($d in '03_Research', '04_Outputs', '05_Daily', '90_Archive', '02_Knowledge\Research_Methods', '02_Knowledge\Business_Models', '02_Knowledge\Technical') {
  $p = Join-Path $hub $d
  if (-not (Test-Path $p)) { Plan 'フォルダ作成' $p; if ($Apply) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }
}

# ---------- 2. サブエージェント・スキル（無いものだけ追加） ----------
foreach ($f in Get-ChildItem (Join-Path $src 'agents') -File) {
  $dst = Join-Path $claudeDir "agents\$($f.Name)"
  if (Test-Path $dst) { Plan '衝突（スキップ）' $dst '同名のエージェントが既にある。中身を確認して手動で統合' }
  else { Plan '追加' $dst; if ($Apply) { WriteText $dst (Get-Content -Raw -Encoding UTF8 $f.FullName) } }
}
foreach ($d in Get-ChildItem (Join-Path $src 'skills') -Directory) {
  $dst = Join-Path $claudeDir "skills\$($d.Name)\SKILL.md"
  if (Test-Path $dst) { Plan '衝突（スキップ）' $dst '同名のスキルが既にある。中身を確認して手動で統合' }
  else { Plan '追加' $dst; if ($Apply) { WriteText $dst (Get-Content -Raw -Encoding UTF8 (Join-Path $d.FullName 'SKILL.md')) } }
}

# ---------- 3. フック（キット専用フォルダ。更新時はバックアップ） ----------
foreach ($f in Get-ChildItem (Join-Path $src 'hooks') -File) {
  $dst = Join-Path $hooksDir $f.Name
  $new = Get-Content -Raw -Encoding UTF8 $f.FullName
  if (Test-Path $dst) {
    if ((Get-Content -Raw -Encoding UTF8 $dst) -eq $new) { Plan 'そのまま' $dst '同じ内容' }
    else { Plan '更新（バックアップあり）' $dst; if ($Apply) { Backup $dst; WriteText $dst $new } }
  } else { Plan '追加' $dst; if ($Apply) { WriteText $dst $new } }
}
$cfgPath = Join-Path $claudeDir 'ai-ecosystem.json'
$cfg = (@{ vault_path = $VaultPath; ai_hub = $hub; installed_at = $today; kit = $kit } | ConvertTo-Json)
if (Test-Path $cfgPath) { Plan '更新（バックアップあり）' $cfgPath; if ($Apply) { Backup $cfgPath; WriteText $cfgPath $cfg } }
else { Plan '追加' $cfgPath; if ($Apply) { WriteText $cfgPath $cfg } }

# ---------- 4. CLAUDE.md ----------
$claudeMd = (Get-Content -Raw -Encoding UTF8 (Join-Path $src 'CLAUDE.md')).Replace('{{AI_HUB}}', $hub)
$userMd = Join-Path $claudeDir 'CLAUDE.md'
if (-not (Test-Path $userMd)) { Plan '追加' $userMd; if ($Apply) { WriteText $userMd $claudeMd } }
else {
  $side = Join-Path $claudeDir 'ai-ecosystem.CLAUDE.md'
  Plan '追加（別名）' $side '既存の CLAUDE.md は変更しない'
  if ($Apply) { if (Test-Path $side) { Backup $side }; WriteText $side $claudeMd }
  $hasImport = (Get-Content -Raw -Encoding UTF8 $userMd) -match '@ai-ecosystem\.CLAUDE\.md'
  if ($hasImport) { Plan 'そのまま' $userMd '読み込み行は追加済み' }
  elseif ($AddClaudeMdImport) { Plan '1行追記（バックアップあり）' $userMd '@ai-ecosystem.CLAUDE.md'; if ($Apply) { Backup $userMd; Add-Content -Encoding UTF8 -Path $userMd -Value "`r`n@ai-ecosystem.CLAUDE.md" } }
  else { Plan '要判断' $userMd '-AddClaudeMdImport を付けると末尾に「@ai-ecosystem.CLAUDE.md」の1行を追記（バックアップあり）' }
}

# ---------- 5. settings.json ----------
$tplText = (Get-Content -Raw -Encoding UTF8 (Join-Path $src 'settings.template.json')).Replace('{{HOOKS_DIR}}', (JsonPath $hooksDir)).Replace('{{VAULT_PATH}}', (JsonPath $VaultPath))
$ours = $tplText | ConvertFrom-Json   # JSON として正しいかをここで確認
function Merge($base, $add) {
  # 既存の値は変えない。配列は和集合、オブジェクトは再帰的に、無いキーだけ追加
  foreach ($p in $add.PSObject.Properties) {
    $cur = $base.PSObject.Properties[$p.Name]
    if (-not $cur) { $base | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value; continue }
    if ($cur.Value -is [System.Array] -and $p.Value -is [System.Array]) {
      $merged = @($cur.Value)
      foreach ($v in $p.Value) {
        $vj = $v | ConvertTo-Json -Depth 20 -Compress
        if (-not ($merged | Where-Object { ($_ | ConvertTo-Json -Depth 20 -Compress) -eq $vj })) { $merged += $v }
      }
      $base.($p.Name) = $merged
    } elseif ($cur.Value -is [System.Management.Automation.PSCustomObject] -and $p.Value -is [System.Management.Automation.PSCustomObject]) { Merge $cur.Value $p.Value | Out-Null }
  }
  return $base
}
$userSettings = Join-Path $claudeDir 'settings.json'
if (-not (Test-Path $userSettings)) { Plan '追加' $userSettings; if ($Apply) { WriteText $userSettings $tplText } }
else {
  $merged = Merge ((Get-Content -Raw -Encoding UTF8 $userSettings) | ConvertFrom-Json) $ours
  $mergedText = $merged | ConvertTo-Json -Depth 30
  $proposal = Join-Path $claudeDir 'settings.ai-ecosystem.proposed.json'
  Plan '追加（提案）' $proposal '既存設定に本キットの設定を足した案。既存の値は変えていない'
  if ($Apply) { WriteText $proposal $mergedText }
  if ($MergeSettings) { Plan '統合（バックアップあり）' $userSettings; if ($Apply) { Backup $userSettings; WriteText $userSettings $mergedText } }
  else { Plan '要判断' $userSettings '提案ファイルを確認し、問題なければ -MergeSettings で統合' }
}

# ---------- 結果 ----------
$plan | Format-Table -AutoSize -Wrap
if ($Apply) {
  Write-Host "完了。バックアップ: $(if (Test-Path $backupDir) { $backupDir } else { 'なし（上書きしたファイルなし）' })" -ForegroundColor Green
  Write-Host "次に: powershell -NoProfile -ExecutionPolicy Bypass -File `"$hooksDir\test-hooks.ps1`" でフックを自己テスト"
} else {
  Write-Host '（計画のみ。何も変更していない。実行するには -Apply を付ける）' -ForegroundColor Yellow
}
