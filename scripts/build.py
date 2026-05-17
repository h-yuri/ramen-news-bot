import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
TODAY = datetime.now().strftime("%Y-%m-%d")
JSON_PATH = ROOT / "docs" / "data" / f"{TODAY}.json"
HTML_OUTPUT = ROOT / "docs" / "index.html"

ALERT_CONFIG = {
    "high":   {"color": "#ff4757", "glow": "rgba(255,71,87,0.35)",  "bg": "#2d1b1b", "label": "HIGH",   "emoji": "🔴"},
    "medium": {"color": "#ffa502", "glow": "rgba(255,165,2,0.35)",  "bg": "#2d2410", "label": "MEDIUM", "emoji": "🟡"},
    "low":    {"color": "#2ed573", "glow": "rgba(46,213,115,0.35)", "bg": "#0f2d1a", "label": "LOW",    "emoji": "🟢"},
}

TAG_COLORS = {
    "【コスト】":  "#ff6b6b",
    "【競合】":   "#ffa502",
    "【客数】":   "#54a0ff",
    "【採用】":   "#a29bfe",
    "【規制】":   "#fd79a8",
    "【機会】":   "#00cec9",
}

WHEN_COLORS = {
    "今日":   "#ff4757",
    "今週中": "#ffa502",
    "今月中": "#2ed573",
}

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()

def build():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    analysis = data["analysis"]
    articles = data["articles"]
    alert = analysis.get("alert_level", "low")
    cfg = ALERT_CONFIG.get(alert, ALERT_CONFIG["low"])

    # --- Highlights ---
    highlights_html = ""
    for h in analysis.get("highlights", []):
        tag = h.get("tag", "")
        tag_color = TAG_COLORS.get(tag, "#a0a0b0")
        highlights_html += f"""
        <div class="highlight-card" >
          <span class="highlight-tag" style="color:{tag_color};border-color:{tag_color}20;background:{tag_color}12">{tag}</span>
          <p class="highlight-text">{h.get("text","")}</p>
        </div>"""

    # --- Actions ---
    actions_html = ""
    for i, ac in enumerate(analysis.get("actions", [])):
        when = ac.get("when", "")
        when_color = next((v for k, v in WHEN_COLORS.items() if k in when), "#a0a0b0")
        actions_html += f"""
        <div class="action-card" style="animation-delay:{i*0.1}s">
          <div class="action-top">
            <span class="action-when" style="color:{when_color};border-color:{when_color}40;background:{when_color}15">{when}</span>
          </div>
          <p class="action-what">{ac.get("what","")}</p>
          <p class="action-why">▶ {ac.get("why","")}</p>
        </div>"""

    # --- Cost items ---
    cost_html = ""
    for c in analysis.get("cost_items", []):
        direction = c.get("direction", "横ばい")
        if "上昇" in direction:
            d_color, d_icon = "#ff4757", "↑"
        elif "下降" in direction:
            d_color, d_icon = "#2ed573", "↓"
        else:
            d_color, d_icon = "#ffa502", "→"
        cost_html += f"""
        <div class="cost-item">
          <span class="cost-name">{c.get("name","")}</span>
          <span class="cost-dir" style="color:{d_color}">{d_icon} {direction}</span>
          <span class="cost-detail">{c.get("detail","")}</span>
        </div>"""

    # --- Articles ---
    articles_html = ""
    for i, a in enumerate(articles):
        summary = strip_html(a.get("summary", ""))[:180]
        if summary:
            summary += "…"
        articles_html += f"""
        <a class="article-card" href="{a["link"]}" target="_blank" rel="noopener" style="animation-delay:{i*0.04}s">
          <div class="article-meta">
            <span class="article-label">{a["label"]}</span>
            <span class="article-date">{a["published"][:16]}</span>
          </div>
          <div class="article-title">{a["title"]}</div>
          {"<div class='article-summary'>" + summary + "</div>" if summary else ""}
        </a>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ラーメン経営情報ボード — {TODAY}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --alert: {cfg["color"]};
      --alert-glow: {cfg["glow"]};
      --alert-bg: {cfg["bg"]};
      --bg: #0a0a0f;
      --surface: #111118;
      --surface2: #18181f;
      --border: rgba(255,255,255,0.07);
      --text: #e4e4f0;
      --muted: #5a5a70;
      --radius: 14px;
    }}
    body {{
      font-family: 'Inter','Hiragino Sans',sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}
    body::before {{
      content:'';
      position:fixed;
      inset:0;
      background: radial-gradient(ellipse 60% 40% at 15% 10%, {cfg["glow"]} 0%, transparent 60%),
                  radial-gradient(ellipse 50% 40% at 85% 85%, rgba(99,102,241,0.06) 0%, transparent 60%);
      animation: bgBreath 10s ease-in-out infinite alternate;
      pointer-events:none;
      z-index:0;
    }}
    @keyframes bgBreath {{
      from {{ opacity:.5; transform:scale(1); }}
      to   {{ opacity:1;  transform:scale(1.05); }}
    }}
    .wrap {{ position:relative; z-index:1; max-width:1060px; margin:0 auto; padding:28px 20px 80px; }}

    /* ── Header ── */
    header {{
      display:flex; align-items:center; justify-content:space-between;
      padding-bottom:28px; animation: fadeDown .5s ease both;
    }}
    .h-title {{ font-size:clamp(1.2rem,2.5vw,1.6rem); font-weight:900; letter-spacing:-.02em;
      background:linear-gradient(120deg,#fff 30%,{cfg["color"]});
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }}
    .h-sub {{ color:var(--muted); font-size:.78rem; margin-top:3px; }}
    .live-badge {{
      display:inline-flex; align-items:center; gap:6px;
      background:rgba(46,213,115,.08); border:1px solid rgba(46,213,115,.25);
      color:#2ed573; font-size:.7rem; font-weight:700; padding:4px 11px;
      border-radius:20px; letter-spacing:.06em;
    }}
    .live-dot {{ width:6px;height:6px;background:#2ed573;border-radius:50%;
      animation:livePulse 1.4s ease-in-out infinite; }}
    @keyframes livePulse {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.3;transform:scale(.7)}} }}

    /* ── Alert hero ── */
    .alert-hero {{
      background:var(--alert-bg); border:1px solid {cfg["color"]}60;
      border-radius:20px; padding:28px 32px; margin-bottom:20px;
      position:relative; overflow:hidden;
      animation:fadeUp .45s ease .05s both;
      box-shadow:0 0 50px var(--alert-glow), inset 0 1px 0 rgba(255,255,255,.04);
    }}
    .alert-hero::after {{
      content:''; position:absolute; top:-60px; right:-60px;
      width:260px; height:260px;
      background:radial-gradient(circle,var(--alert-glow) 0%,transparent 70%);
      pointer-events:none;
    }}
    .alert-row {{ display:flex; align-items:center; gap:10px; margin-bottom:14px; }}
    .alert-badge {{
      background:var(--alert); color:#000; font-size:.7rem; font-weight:900;
      padding:4px 12px; border-radius:20px; letter-spacing:.1em;
      animation:badgePop .4s cubic-bezier(.34,1.56,.64,1) .3s both;
      box-shadow:0 0 18px var(--alert-glow);
    }}
    @keyframes badgePop {{ from{{transform:scale(0);opacity:0}} to{{transform:scale(1);opacity:1}} }}
    .alert-label-txt {{ color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; }}
    .headline {{
      font-size:clamp(1.1rem,2.5vw,1.4rem); font-weight:800; line-height:1.4;
      color:#fff; letter-spacing:-.01em;
    }}

    /* ── Grid ── */
    .grid-main {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}
    @media(max-width:640px){{ .grid-main{{grid-template-columns:1fr}} }}

    /* ── Card base ── */
    .card {{
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:22px;
      animation:fadeUp .45s ease both;
    }}
    .card-title {{
      font-size:.68rem; text-transform:uppercase; letter-spacing:.1em;
      color:var(--muted); margin-bottom:16px;
      display:flex; align-items:center; gap:8px;
    }}
    .card-title::after {{ content:''; flex:1; height:1px; background:var(--border); }}

    /* ── Highlights ── */
    .highlights-list {{ display:flex; flex-direction:column; gap:12px; }}
    .highlight-card {{
      background:var(--surface2); border:1px solid var(--border);
      border-radius:10px; padding:14px;
      transition:border-color .2s;
    }}
    .highlight-card:hover {{ border-color:rgba(255,255,255,.15); }}
    .highlight-tag {{
      display:inline-block; font-size:.68rem; font-weight:700;
      padding:2px 8px; border-radius:6px; border:1px solid;
      margin-bottom:8px; letter-spacing:.04em;
    }}
    .highlight-text {{ font-size:.85rem; line-height:1.65; color:var(--text); }}

    /* ── Actions ── */
    .actions-list {{ display:flex; flex-direction:column; gap:10px; }}
    .action-card {{
      background:var(--surface2); border:1px solid var(--border);
      border-radius:10px; padding:14px;
      animation:fadeLeft .4s ease both;
      transition:border-color .2s, transform .2s;
    }}
    .action-card:hover {{ border-color:rgba(255,255,255,.15); transform:translateX(3px); }}
    .action-top {{ margin-bottom:8px; }}
    .action-when {{
      display:inline-block; font-size:.68rem; font-weight:700;
      padding:2px 10px; border-radius:20px; border:1px solid; letter-spacing:.06em;
    }}
    .action-what {{ font-size:.88rem; font-weight:600; line-height:1.5; margin-bottom:6px; }}
    .action-why {{ font-size:.78rem; color:var(--muted); line-height:1.5; }}

    /* ── Cost items ── */
    .cost-list {{ display:flex; flex-direction:column; gap:8px; }}
    .cost-item {{
      display:grid; grid-template-columns:auto auto 1fr;
      align-items:center; gap:10px;
      padding:10px 12px;
      background:var(--surface2); border-radius:8px;
      font-size:.84rem;
    }}
    .cost-name {{ font-weight:600; white-space:nowrap; }}
    .cost-dir  {{ font-weight:700; font-size:.9rem; white-space:nowrap; }}
    .cost-detail {{ color:var(--muted); font-size:.78rem; }}

    /* ── Articles ── */
    .articles-list {{ display:flex; flex-direction:column; gap:8px; }}
    .article-card {{
      display:block; text-decoration:none; color:var(--text);
      background:var(--surface); border:1px solid var(--border);
      border-radius:10px; padding:14px 16px;
      animation:fadeUp .3s ease both;
      transition:border-color .2s, background .2s, transform .2s;
    }}
    .article-card:hover {{
      border-color:var(--alert); background:var(--surface2);
      transform:translateX(4px);
    }}
    .article-meta {{ display:flex; align-items:center; gap:8px; margin-bottom:5px; }}
    .article-label {{
      font-size:.65rem; font-weight:700; color:var(--alert);
      text-transform:uppercase; letter-spacing:.06em;
    }}
    .article-date {{ font-size:.68rem; color:var(--muted); }}
    .article-title {{ font-size:.86rem; font-weight:600; line-height:1.5; margin-bottom:4px; }}
    .article-summary {{ font-size:.78rem; color:#8888a0; line-height:1.6; }}

    /* ── Stats row ── */
    .stats-row {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:16px; }}
    @media(max-width:500px){{ .stats-row{{grid-template-columns:1fr 1fr}} }}
    .stat-card {{
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:18px;
      animation:fadeUp .45s ease both;
      transition:transform .2s, border-color .2s;
    }}
    .stat-card:hover {{ transform:translateY(-2px); border-color:rgba(255,255,255,.14); }}
    .stat-label {{ color:var(--muted); font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }}
    .stat-value {{ font-size:1.8rem; font-weight:900; line-height:1; color:var(--text); }}
    .stat-value.accent {{ color:var(--alert); }}

    /* ── Animations ── */
    @keyframes fadeDown {{ from{{opacity:0;transform:translateY(-16px)}} to{{opacity:1;transform:none}} }}
    @keyframes fadeUp   {{ from{{opacity:0;transform:translateY(16px)}}  to{{opacity:1;transform:none}} }}
    @keyframes fadeLeft {{ from{{opacity:0;transform:translateX(-16px)}} to{{opacity:1;transform:none}} }}

    footer {{ text-align:center; color:var(--muted); font-size:.7rem; padding-top:48px; animation:fadeUp .5s ease .9s both; }}
  </style>
</head>
<body>
<div class="wrap">

  <header>
    <div>
      <div class="h-title">ラーメン経営情報ボード</div>
      <div class="h-sub">{TODAY} 更新 · 毎朝7時自動収集</div>
    </div>
    <span class="live-badge"><span class="live-dot"></span>AUTO</span>
  </header>

  <!-- Alert Hero -->
  <div class="alert-hero">
    <div class="alert-row">
      <span class="alert-badge">{cfg["emoji"]} {cfg["label"]}</span>
      <span class="alert-label-txt">アラートレベル</span>
    </div>
    <div class="headline">{analysis.get("headline","")}</div>
  </div>

  <!-- Stats -->
  <div class="stats-row">
    <div class="stat-card" style="animation-delay:.15s">
      <div class="stat-label">収集記事数</div>
      <div class="stat-value accent">{len(articles)}<span style="font-size:.9rem;font-weight:400"> 件</span></div>
    </div>
    <div class="stat-card" style="animation-delay:.2s">
      <div class="stat-label">アクション数</div>
      <div class="stat-value accent">{len(analysis.get("actions",[]))}<span style="font-size:.9rem;font-weight:400"> 件</span></div>
    </div>
    <div class="stat-card" style="animation-delay:.25s">
      <div class="stat-label">更新時刻</div>
      <div class="stat-value" style="font-size:1.1rem">{data.get("generated_at","")[:16].replace("T"," ")}</div>
    </div>
  </div>

  <!-- Highlights + Actions -->
  <div class="grid-main">
    <div class="card" style="animation-delay:.3s">
      <div class="card-title">今日のハイライト</div>
      <div class="highlights-list">
        {highlights_html if highlights_html else '<p style="color:var(--muted);font-size:.85rem">情報なし</p>'}
      </div>
    </div>
    <div class="card" style="animation-delay:.35s">
      <div class="card-title">今日・今週のアクション</div>
      <div class="actions-list">
        {actions_html if actions_html else '<p style="color:var(--muted);font-size:.85rem">なし</p>'}
      </div>
    </div>
  </div>

  <!-- Cost items -->
  {"" if not analysis.get("cost_items") else f'''
  <div class="card" style="animation-delay:.4s;margin-bottom:16px">
    <div class="card-title">食材コスト動向</div>
    <div class="cost-list">{cost_html}</div>
  </div>'''}

  <!-- Articles -->
  <div class="card" style="animation-delay:.45s">
    <div class="card-title">収集記事 ({len(articles)}件) — タップで全文</div>
    <div class="articles-list">
      {articles_html if articles_html else '<p style="color:var(--muted);font-size:.85rem">記事なし</p>'}
    </div>
  </div>

  <footer>ramen-news-bot · Gemini 2.5 Flash · {data.get("generated_at","")[:19].replace("T"," ")}</footer>
</div>
</body>
</html>"""

    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  HTML生成完了 → {HTML_OUTPUT.name}")


if __name__ == "__main__":
    build()
