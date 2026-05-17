# run.ps1
# fetch → summarize → build を順番に実行して結果を確認する
# 使い方: .\run.ps1
#         .\run.ps1 -OpenBrowser  # 実行後にブラウザでプレビュー
#         .\run.ps1 -Step fetch   # 特定ステップだけ実行

param(
    [switch]$OpenBrowser,
    [ValidateSet("all", "fetch", "summarize", "build")]
    [string]$Step = "all"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptsDir = "$RootDir\scripts"
$EnvFile = "$RootDir\.env"

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

# .env から環境変数を読み込む
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
} else {
    Write-Host "   [WARN] .env が見つかりません。setup.ps1 を先に実行してください" -ForegroundColor Yellow
}

$StartTime = Get-Date

# ----------------------------------------
if ($Step -eq "all" -or $Step -eq "fetch") {
    Write-Step "STEP 1: RSS収集 (fetch.py)"
    $result = python "$ScriptsDir\fetch.py" 2>&1
    $result | ForEach-Object { Write-Host "   $_" }
    if ($LASTEXITCODE -ne 0) { Write-Fail "fetch.py でエラーが発生しました" }
    Write-OK "収集完了"
}

# ----------------------------------------
if ($Step -eq "all" -or $Step -eq "summarize") {
    Write-Step "STEP 2: AI要約生成 (summarize.py)"
    $result = python "$ScriptsDir\summarize.py" 2>&1
    $result | ForEach-Object { Write-Host "   $_" }
    if ($LASTEXITCODE -ne 0) { Write-Fail "summarize.py でエラーが発生しました" }
    Write-OK "要約完了"
}

# ----------------------------------------
if ($Step -eq "all" -or $Step -eq "build") {
    Write-Step "STEP 3: HTML生成 (build.py)"
    $result = python "$ScriptsDir\build.py" 2>&1
    $result | ForEach-Object { Write-Host "   $_" }
    if ($LASTEXITCODE -ne 0) { Write-Fail "build.py でエラーが発生しました" }
    Write-OK "HTML生成完了"
}

# ----------------------------------------
$Elapsed = ((Get-Date) - $StartTime).TotalSeconds
Write-Host "`n  完了 (${Elapsed}秒)" -ForegroundColor Cyan

# 生成されたJSONのサマリーを表示
$Today = (Get-Date).ToString("yyyy-MM-dd")
$JsonPath = "$RootDir\docs\data\$Today.json"
if (Test-Path $JsonPath) {
    $data = Get-Content $JsonPath -Raw | ConvertFrom-Json
    $analysis = $data.analysis
    Write-Host "`n  アラートレベル : $($analysis.alert_level.ToUpper())" -ForegroundColor Yellow
    Write-Host "  サマリー       : $($analysis.summary.Substring(0, [Math]::Min(80, $analysis.summary.Length)))..." -ForegroundColor White
    Write-Host "  収集記事数     : $($data.articles.Count)件" -ForegroundColor White
}

# ブラウザでプレビュー
if ($OpenBrowser) {
    $HtmlPath = "$RootDir\docs\index.html"
    if (Test-Path $HtmlPath) {
        Write-Host "`n  ブラウザでプレビューを開きます..." -ForegroundColor Cyan
        Start-Process $HtmlPath
    }
}
