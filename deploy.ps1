# deploy.ps1
# ローカルの変更をGitHubにpushしてActionsの実行状況を確認する
# 使い方: .\deploy.ps1
#         .\deploy.ps1 -TriggerAction  # pushに加えてActionsを手動トリガー
#         .\deploy.ps1 -WatchAction    # Actionsの完了までログを監視

param(
    [switch]$TriggerAction,
    [switch]$WatchAction
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) {
    Write-Host "`n>> $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "   [OK] $msg" -ForegroundColor Green
}

# ----------------------------------------
Write-Step "Git の状態確認"
Set-Location $RootDir
$status = git status --short
if ($status) {
    Write-Host "   変更ファイル:" -ForegroundColor Yellow
    $status | ForEach-Object { Write-Host "   $_" }
} else {
    Write-Host "   変更なし（最新状態）" -ForegroundColor Gray
}

# ----------------------------------------
Write-Step "GitHub へ push"
git add .
$hasChanges = git diff --staged --quiet; $staged = $LASTEXITCODE
if ($staged -ne 0) {
    $commitMsg = "update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git commit -m $commitMsg
    git push
    Write-OK "push 完了: $commitMsg"
} else {
    Write-Host "   コミットする変更がありません" -ForegroundColor Gray
}

# ----------------------------------------
# GitHub CLI があれば Actions を操作
try {
    gh --version | Out-Null
    $ghAvailable = $true
} catch {
    $ghAvailable = $false
}

if ($ghAvailable) {
    if ($TriggerAction) {
        Write-Step "GitHub Actions を手動トリガー"
        gh workflow run daily.yml
        Write-OK "ワークフロー起動"
        Start-Sleep -Seconds 3
    }

    if ($WatchAction) {
        Write-Step "Actions の実行を監視中（Ctrl+C で中断）"
        gh run watch
    } else {
        Write-Step "最新の Actions 実行状況"
        gh run list --limit 5
    }
} else {
    Write-Host "`n  GitHub CLI がないため Actions の確認はブラウザで行ってください" -ForegroundColor Yellow
    Write-Host "  https://github.com/$(git remote get-url origin | Split-Path -Leaf)/actions" -ForegroundColor Gray
}
