import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
TODAY = datetime.now().strftime("%Y-%m-%d")
JSON_PATH = ROOT / "docs" / "data" / f"{TODAY}.json"
HTML_OUTPUT = ROOT / "docs" / "index.html"

ALERT_CONFIG = {
    "high":   {"color": "#ff4757", "glow": "rgba(255,71,87,0.4)",   "bg": "#2d1b1b", "label": "HIGH",   "emoji": "🔴"},
    "medium": {"color": "#ffa502", "glow": "rgba(255,165,2,0.4)",   "bg": "#2d2410", "label": "MEDIUM", "emoji": "🟡"},
    "low":    {"color": "#2ed573", "glow": "rgba(46,213,115,0.4)",  "bg": "#0f2d1a", "label": "LOW",    "emoji": "🟢"},
}

def build():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    analysis = data["analysis"]
    articles = data["articles"]
    alert = analysis.get("alert_level", "low")
    cfg = ALERT_CONFIG.get(alert, ALERT_CONFIG["low"])

    key_topics_html = "".join(
        f'<span class="topic-tag" style="animation-delay:{i*0.1}s">{t}</span>'
        for i, t in enumerate(analysis.get("key_topics", []))
    )

    action_items_html = "".join(
        f'<li class="action-item" style="animation-delay:{i*0.15}s"><span class="action-num">{i+1:02d}</span>{a}</li>'
        for i, a in enumerate(analysis.get("action_items", []))
    )

    articles_html = "".join(
        f'''<a class="article-card" href="{a["link"]}" target="_blank" rel="noopener" style="animation-delay:{i*0.05}s">
          <div class="article-label">{a["label"]}</div>
          <div class="article-title">{a["title"]}</div>
          <div class="article-date">{a["published"][:16]}</div>
        </a>'''
        for i, a in enumerate(articles)
    )

    cost_trend = analysis.get("cost_trend", "横ばい")
    trend_icon = "↑" if "上昇" in cost_trend else ("↓" if "下降" in cost_trend else "→")
    trend_color = "#ff4757" if "上昇" in cost_trend else ("#2ed573" if "下降" in cost_trend else "#ffa502")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ラーメン経営情報ボード</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --alert-color: {cfg["color"]};
      --alert-glow: {cfg["glow"]};
      --alert-bg: {cfg["bg"]};
      --bg: #0a0a0f;
      --surface: #12121a;
      --surface2: #1a1a26;
      --border: rgba(255,255,255,0.07);
      --text: #e8e8f0;
      --muted: #6b6b80;
    }}

    body {{
      font-family: 'Inter', 'Hiragino Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }}

    /* Animated background */
    body::before {{
      content: '';
      position: fixed;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(ellipse at 20% 20%, {cfg["glow"]} 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 80%, rgba(99,102,241,0.08) 0%, transparent 50%);
      animation: bgPulse 8s ease-in-out infinite alternate;
      pointer-events: none;
      z-index: 0;
    }}

    @keyframes bgPulse {{
      0%   {{ transform: scale(1) rotate(0deg); opacity: 0.6; }}
      100% {{ transform: scale(1.1) rotate(3deg); opacity: 1; }}
    }}

    .container {{
      position: relative;
      z-index: 1;
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px 20px 60px;
    }}

    /* Header */
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 20px 0 32px;
      animation: fadeDown 0.6s ease both;
    }}

    .header-left h1 {{
      font-size: clamp(1.4rem, 3vw, 2rem);
      font-weight: 900;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #fff 0%, var(--alert-color) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .header-left p {{
      color: var(--muted);
      font-size: 0.8rem;
      margin-top: 4px;
    }}

    .header-right {{
      text-align: right;
    }}

    .live-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(46,213,115,0.1);
      border: 1px solid rgba(46,213,115,0.3);
      color: #2ed573;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 20px;
      letter-spacing: 0.05em;
    }}

    .live-dot {{
      width: 6px;
      height: 6px;
      background: #2ed573;
      border-radius: 50%;
      animation: livePulse 1.5s ease-in-out infinite;
    }}

    @keyframes livePulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.8); }}
    }}

    /* Alert Hero */
    .alert-hero {{
      background: var(--alert-bg);
      border: 1px solid var(--alert-color);
      border-radius: 20px;
      padding: 32px;
      margin-bottom: 24px;
      position: relative;
      overflow: hidden;
      animation: fadeUp 0.5s ease 0.1s both;
      box-shadow: 0 0 40px var(--alert-glow), inset 0 1px 0 rgba(255,255,255,0.05);
    }}

    .alert-hero::before {{
      content: '';
      position: absolute;
      top: 0; right: 0;
      width: 300px; height: 300px;
      background: radial-gradient(circle, var(--alert-glow) 0%, transparent 70%);
      transform: translate(30%, -30%);
      pointer-events: none;
    }}

    .alert-level-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }}

    .alert-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--alert-color);
      color: #000;
      font-size: 0.75rem;
      font-weight: 900;
      padding: 5px 14px;
      border-radius: 20px;
      letter-spacing: 0.1em;
      animation: badgePop 0.4s cubic-bezier(0.34,1.56,0.64,1) 0.3s both;
      box-shadow: 0 0 20px var(--alert-glow);
    }}

    @keyframes badgePop {{
      from {{ transform: scale(0); opacity: 0; }}
      to   {{ transform: scale(1); opacity: 1; }}
    }}

    .alert-label {{
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }}

    .alert-summary {{
      font-size: clamp(0.95rem, 2vw, 1.1rem);
      line-height: 1.75;
      color: var(--text);
      position: relative;
      z-index: 1;
    }}

    /* Stats row */
    .stats-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      animation: fadeUp 0.5s ease both;
      transition: transform 0.2s, border-color 0.2s;
    }}

    .stat-card:hover {{
      transform: translateY(-3px);
      border-color: rgba(255,255,255,0.15);
    }}

    .stat-label {{
      color: var(--muted);
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }}

    .stat-value {{
      font-size: 2rem;
      font-weight: 900;
      line-height: 1;
      color: var(--text);
    }}

    .stat-value.accent {{
      color: var(--alert-color);
    }}

    .stat-value.trend {{
      color: {trend_color};
    }}

    /* Grid layout */
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }}

    @media (max-width: 640px) {{
      .grid-2 {{ grid-template-columns: 1fr; }}
    }}

    /* Cards */
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      animation: fadeUp 0.5s ease both;
    }}

    .card-title {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .card-title::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }}

    /* Topics */
    .topics-wrap {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .topic-tag {{
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.82rem;
      animation: fadeUp 0.4s ease both;
      transition: border-color 0.2s, background 0.2s;
    }}

    .topic-tag:hover {{
      border-color: var(--alert-color);
      background: var(--alert-bg);
    }}

    /* Actions */
    .action-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .action-item {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      font-size: 0.88rem;
      line-height: 1.5;
      animation: fadeLeft 0.4s ease both;
    }}

    .action-num {{
      flex-shrink: 0;
      width: 24px;
      height: 24px;
      background: var(--alert-color);
      color: #000;
      font-size: 0.65rem;
      font-weight: 900;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    /* Articles */
    .articles-grid {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .article-card {{
      display: block;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      text-decoration: none;
      color: var(--text);
      animation: fadeUp 0.3s ease both;
      transition: border-color 0.2s, background 0.2s, transform 0.2s;
    }}

    .article-card:hover {{
      border-color: var(--alert-color);
      background: var(--surface2);
      transform: translateX(4px);
    }}

    .article-label {{
      display: inline-block;
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--alert-color);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
    }}

    .article-title {{
      font-size: 0.85rem;
      line-height: 1.5;
      margin-bottom: 4px;
    }}

    .article-date {{
      font-size: 0.7rem;
      color: var(--muted);
    }}

    /* Animations */
    @keyframes fadeDown {{
      from {{ opacity: 0; transform: translateY(-20px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(20px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes fadeLeft {{
      from {{ opacity: 0; transform: translateX(-20px); }}
      to   {{ opacity: 1; transform: translateX(0); }}
    }}

    /* Counter animation */
    .count-anim {{
      display: inline-block;
      animation: countUp 1s cubic-bezier(0.16,1,0.3,1) 0.5s both;
    }}

    @keyframes countUp {{
      from {{ opacity: 0; transform: translateY(20px); filter: blur(4px); }}
      to   {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
    }}

    footer {{
      text-align: center;
      color: var(--muted);
      font-size: 0.72rem;
      padding-top: 40px;
      animation: fadeUp 0.5s ease 0.8s both;
    }}
  </style>
</head>
<body>
<div class="container">

  <header>
    <div class="header-left">
      <h1>ラーメン経営情報ボード</h1>
      <p>{TODAY} 更新</p>
    </div>
    <div class="header-right">
      <span class="live-badge"><span class="live-dot"></span>AUTO UPDATE</span>
    </div>
  </header>

  <!-- Alert Hero -->
  <div class="alert-hero">
    <div class="alert-level-row">
      <span class="alert-badge">{cfg["emoji"]} {cfg["label"]}</span>
      <span class="alert-label">アラートレベル</span>
    </div>
    <p class="alert-summary">{analysis.get("summary", "")}</p>
  </div>

  <!-- Stats -->
  <div class="stats-row">
    <div class="stat-card" style="animation-delay:0.2s">
      <div class="stat-label">収集記事数</div>
      <div class="stat-value accent count-anim">{len(articles)}<span style="font-size:1rem;font-weight:400"> 件</span></div>
    </div>
    <div class="stat-card" style="animation-delay:0.25s">
      <div class="stat-label">食材コスト動向</div>
      <div class="stat-value trend count-anim">{trend_icon} {cost_trend}</div>
    </div>
    <div class="stat-card" style="animation-delay:0.3s">
      <div class="stat-label">更新時刻</div>
      <div class="stat-value count-anim" style="font-size:1.4rem">{data.get("generated_at","")[:16].replace("T"," ")}</div>
    </div>
  </div>

  <!-- Topics & Actions -->
  <div class="grid-2">
    <div class="card" style="animation-delay:0.35s">
      <div class="card-title">主要トピック</div>
      <div class="topics-wrap">
        {key_topics_html if key_topics_html else '<span style="color:var(--muted);font-size:.85rem">なし</span>'}
      </div>
    </div>
    <div class="card" style="animation-delay:0.4s">
      <div class="card-title">推奨アクション</div>
      <ul class="action-list">
        {action_items_html if action_items_html else '<li style="color:var(--muted);font-size:.85rem">なし</li>'}
      </ul>
    </div>
  </div>

  <!-- Articles -->
  <div class="card" style="animation-delay:0.45s">
    <div class="card-title">収集記事 ({len(articles)}件)</div>
    <div class="articles-grid">
      {articles_html if articles_html else '<p style="color:var(--muted);font-size:.85rem">記事なし</p>'}
    </div>
  </div>

  <footer>
    自動生成 by ramen-news-bot &nbsp;·&nbsp; Powered by Gemini 2.5 Flash &nbsp;·&nbsp; {data.get("generated_at","")[:19].replace("T"," ")}
  </footer>

</div>
</body>
</html>"""

    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  HTML生成完了 → {HTML_OUTPUT.name}")


if __name__ == "__main__":
    build()
