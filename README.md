# ラーメン経営情報ボード

毎朝7時にニュースを自動収集・AI要約してGitHub Pagesで配信する。  
コスト：**¥0 / 月**（Gemini API 無料枠 + GitHub 無料枠）

## ファイル構成

```
ramen-news-bot/
├── .github/workflows/daily.yml   # GitHub Actions（本番自動実行）
├── scripts/
│   ├── fetch.py                  # RSS収集
│   ├── summarize.py              # Gemini API 要約生成
│   └── build.py                  # HTML生成
├── docs/                         # GitHub Pages 配信ルート
│   ├── index.html                # 閲覧サイト（自動更新）
│   └── data/                     # 日付別JSON蓄積
├── config.yaml                   # 監視フィード設定
├── requirements.txt              # Python依存パッケージ
├── setup.ps1                     # 初回セットアップ（1回だけ実行）
├── run.ps1                       # ローカル動作確認
└── deploy.ps1                    # GitHubへのデプロイ・確認
```

## セットアップ（初回のみ）

### 事前に必要なもの
- Python 3.11 以上
- Git
- Gemini API キー（[Google AI Studio](https://aistudio.google.com) で無料取得）
- （任意）[GitHub CLI](https://cli.github.com/) ← あると自動化が楽

### 手順

**1. リポジトリをGitHubに作って clone**
```
git clone https://github.com/あなたのID/ramen-news-bot.git
cd ramen-news-bot
```

**2. PowerShellでセットアップを実行**
```powershell
.\setup.ps1 -GeminiApiKey "AIza..." -GitHubRepo "あなたのID/ramen-news-bot"
```
これだけで以下が全部完了する：
- Pythonパッケージインストール
- .env ファイル生成
- GitHub Secrets 登録（GitHub CLI がある場合）
- 動作確認（fetch → summarize → build）

**3. GitHub Pages を有効化**  
リポジトリの Settings → Pages → Source: `docs/` フォルダ

## 日常の使い方

| やること | コマンド |
|---|---|
| ローカルで動作確認 | `.\run.ps1` |
| 確認してブラウザで見る | `.\run.ps1 -OpenBrowser` |
| fetchだけ再実行 | `.\run.ps1 -Step fetch` |
| GitHubにpush | `.\deploy.ps1` |
| pushしてActionsも即実行 | `.\deploy.ps1 -TriggerAction` |
| Actionsの完了を監視 | `.\deploy.ps1 -WatchAction` |

## フィードの追加・変更

`config.yaml` を編集するだけ。

```yaml
- url: "https://news.google.com/rss/search?q=監視したいキーワード&hl=ja&gl=JP&ceid=JP:ja"
  categories: [revenue]  # revenue / cost / store から選ぶ
  label: "表示名"
```

編集後は `.\run.ps1` で確認 → `.\deploy.ps1` でpush。
