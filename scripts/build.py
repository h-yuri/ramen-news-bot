import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
TODAY = datetime.now().strftime("%Y-%m-%d")
JSON_PATH = ROOT / "docs" / "data" / f"{TODAY}.json"
HTML_OUTPUT = ROOT / "docs" / "index.html"


ALERT_COLORS = {
    "high": ("#c0392b", "#fadbd8", "⚠ 高"),
    "medium": ("#e67e22", "#fdebd0", "▲ 中"),
    "low": ("#27ae60", "#d5f5e3", "● 低"),
}


def build():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    analysis = data["analysis"]
    articles = data["articles"]
    alert = analysis.get("alert_level", "low")
    color, bg, label = ALERT_COLORS.get(alert, ALERT_COLORS["low"])

    key_topics_html = "".join(
        f'<span class="tag">{t}</span>' for t in analysis.get("key_topics", [])
    )
    action_items_html = "".join(
        f"<li>{a}</li>" for a in analysis.get("action_items", [])
    )
    articles_html = "".join(
        f'''<div class="article">
          <a href="{a['link']}" target="_blank" rel="noopener">{a['title']}</a>
          <span class="meta">{a['label']} | {a['published'][:16]}</span>
        </div>'''
        for a in articles
    )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ラーメン経営情報ボード — {TODAY}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; background: #f5f5f5; color: #333; }}
    header {{ background: #c0392b; color: #fff; padding: 16px 24px; }}
    header h1 {{ font-size: 1.4rem; }}
    header small {{ font-size: 0.8rem; opacity: 0.8; }}
    .container {{ max-width: 860px; margin: 0 auto; padding: 16px; }}
    .alert-box {{ background: {bg}; border-left: 6px solid {color}; padding: 16px; margin: 16px 0; border-radius: 4px; }}
    .alert-box .level {{ font-size: 1.1rem; font-weight: bold; color: {color}; margin-bottom: 8px; }}
    .summary {{ font-size: 0.95rem; line-height: 1.6; }}
    .section {{ background: #fff; border-radius: 6px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    .section h2 {{ font-size: 1rem; color: #555; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
    .tag {{ display: inline-block; background: #eaf0fb; color: #2471a3; border-radius: 12px; padding: 3px 10px; font-size: 0.82rem; margin: 3px; }}
    .section ul {{ padding-left: 18px; }}
    .section li {{ margin: 6px 0; font-size: 0.9rem; line-height: 1.5; }}
    .article {{ padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
    .article:last-child {{ border-bottom: none; }}
    .article a {{ color: #2471a3; text-decoration: none; font-size: 0.9rem; display: block; }}
    .article a:hover {{ text-decoration: underline; }}
    .meta {{ font-size: 0.75rem; color: #999; display: block; margin-top: 2px; }}
    .cost-badge {{ display: inline-block; background: #f0f0f0; border-radius: 4px; padding: 4px 10px; font-size: 0.85rem; }}
    footer {{ text-align: center; color: #aaa; font-size: 0.75rem; padding: 24px; }}
  </style>
</head>
<body>
  <header>
    <h1>ラーメン経営情報ボード</h1>
    <small>{TODAY} 更新 | 収集記事数: {len(articles)}件</small>
  </header>
  <div class="container">
    <div class="alert-box">
      <div class="level">アラートレベル: {label}</div>
      <div class="summary">{analysis.get('summary', '')}</div>
    </div>

    <div class="section">
      <h2>主要トピック</h2>
      {key_topics_html if key_topics_html else '<span class="meta">なし</span>'}
    </div>

    <div class="section">
      <h2>食材コスト動向</h2>
      <span class="cost-badge">{analysis.get('cost_trend', '不明')}</span>
    </div>

    <div class="section">
      <h2>推奨アクション</h2>
      <ul>{action_items_html if action_items_html else '<li>なし</li>'}</ul>
    </div>

    <div class="section">
      <h2>収集記事一覧 ({len(articles)}件)</h2>
      {articles_html if articles_html else '<p class="meta">記事なし</p>'}
    </div>
  </div>
  <footer>自動生成 by ramen-news-bot | {data.get('generated_at', '')[:19]}</footer>
</body>
</html>"""

    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  HTML生成完了 → {HTML_OUTPUT.name}")


if __name__ == "__main__":
    build()
