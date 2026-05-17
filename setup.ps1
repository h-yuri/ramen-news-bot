# setup.ps1
# 初回セットアップを全自動で実行する
# 使い方: .\setup.ps1 -GeminiApiKey "YOUR_KEY" -GitHubRepo "username/ramen-news-bot"

param(
    [Parameter(Mandatory=$true)]
    [string]$GeminiApiKey,

    [Parameter(Mandatory=$true)]
    [string]$GitHubRepo  # 例: "yourname/ramen-news-bot"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) {
    Write-Host "`n>> $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "   [OK] $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "   [ERROR] $msg" -ForegroundColor Red
    exit 1
}

# ----------------------------------------
Write-Step "Python の確認"
try {
    $pyVersion = python --version 2>&1
    Write-OK $pyVersion
} catch {
    Write-Fail "Python が見つかりません。https://python.org からインストールしてください"
}

# ----------------------------------------
Write-Step "依存パッケージのインストール"
python -m pip install -r "$RootDir\requirements.txt" --quiet
Write-OK "パッケージインストール完了"

# ----------------------------------------
Write-Step ".env ファイルの生成（ローカル実行用）"
$envPath = "$RootDir\.env"
@"
GEMINI_API_KEY=$GeminiApiKey
"@ | Set-Content -Path $envPath -Encoding UTF8
Write-OK ".env 生成 → $envPath"

# ----------------------------------------
Write-Step "GitHub CLI の確認"
try {
    gh --version | Out-Null
    Write-OK "GitHub CLI あり"

    Write-Step "GitHub Secrets に GEMINI_API_KEY を登録"
    $GeminiApiKey | gh secret set GEMINI_API_KEY --repo $GitHubRepo
    Write-OK "Secrets 登録完了"
} catch {
    Write-Host "   [SKIP] GitHub CLI がありません。手動でSecretsを登録してください" -ForegroundColor Yellow
    Write-Host "          Settings > Secrets > GEMINI_API_KEY = $GeminiApiKey" -ForegroundColor Yellow
}

# ----------------------------------------
Write-Step "docs/data ディレクトリの確認"
$dataDir = "$RootDir\docs\data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}
Write-OK "ディレクトリ確認済み"

# ----------------------------------------
Write-Step "動作確認（fetch → summarize → build）"
& "$RootDir\run.ps1"

Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "  セットアップ完了！" -ForegroundColor Cyan
Write-Host "  サイトプレビュー: docs\index.html" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
