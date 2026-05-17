# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

毎朝7時にRSSフィードからニュースを自動収集し、Gemini APIでAI要約を生成してGitHub Pagesに配信するボット。コスト¥0/月（Gemini API無料枠 + GitHub無料枠）。

## コマンド

```powershell
# ローカルでパイプライン全体を実行
.\run.ps1

# 結果をブラウザで確認
.\run.ps1 -OpenBrowser

# 特定ステップのみ実行（fetch / summarize / build）
.\run.ps1 -Step fetch

# 初回セットアップ（1回だけ）
.\setup.ps1 -GeminiApiKey "AIza..." -GitHubRepo "username/ramen-news-bot"

# GitHubへpush
.\deploy.ps1

# pushしてActionsも手動実行
.\deploy.ps1 -TriggerAction

# Actionsの完了まで監視
.\deploy.ps1 -WatchAction
```

## アーキテクチャ

### データフロー

```
config.yaml（監視フィード設定）
    ↓
scripts/fetch.py        → RSS収集
    ↓ articles.json（一時ファイル）
scripts/summarize.py    → Gemini API呼び出し、記事分析
    ↓ analysis付きJSON
scripts/build.py        → docs/index.html + docs/data/YYYY-MM-DD.json を生成
    ↓
GitHub Pages（自動配信）
```

### 実行環境

- **ローカル**: `run.ps1` が `.env` から `GEMINI_API_KEY` を読み込み、3スクリプトを順番に呼び出す
- **本番**: `.github/workflows/daily.yml` が毎朝7時にGitHub Actionsで同じパイプラインを実行。APIキーはGitHub Secretsから注入

### 出力フォーマット

`docs/data/YYYY-MM-DD.json` の構造：
```json
{
  "articles": [...],
  "analysis": {
    "alert_level": "low/medium/high",
    "summary": "..."
  }
}
```
`run.ps1` はこのJSONを読んでアラートレベル・サマリー・記事数をターミナルに表示する。

### config.yaml フィード設定

```yaml
- url: "https://news.google.com/rss/search?q=キーワード&hl=ja&gl=JP&ceid=JP:ja"
  categories: [revenue, cost, store]  # revenue / cost / store から選択
  label: "表示名"
```

## 未実装ファイル（スケルトン状態）

現在リポジトリには PowerShell スクリプトと README のみ存在する。以下はまだ作成が必要：

- `scripts/fetch.py` — RSS収集
- `scripts/summarize.py` — Gemini API要約
- `scripts/build.py` — HTML/JSON生成
- `config.yaml` — 監視フィード設定
- `requirements.txt` — Python依存パッケージ
- `.github/workflows/daily.yml` — GitHub Actions定義
- `docs/` — GitHub Pages配信ディレクトリ

## 環境変数

| 変数 | 用途 |
|---|---|
| `GEMINI_API_KEY` | Gemini API認証。ローカルは `.env`、本番はGitHub Secrets経由 |
