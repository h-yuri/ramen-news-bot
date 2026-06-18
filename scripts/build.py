import json
import re
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
TODAY = datetime.now().strftime("%Y-%m-%d")
JSON_PATH = ROOT / "docs" / "data" / f"{TODAY}.json"
HTML_OUTPUT = ROOT / "docs" / "index.html"
CONFIG_PATH = ROOT / "config.yaml"


def load_access_hash():
    """config.yaml の access.hash（SHA-256 の "ユーザーID:パスワード"）を読む。
    未設定なら空文字を返し、その場合ゲートは無効（公開）になる。"""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return ((cfg.get("access") or {}).get("hash") or "").strip()
    except Exception:
        return ""


# クライアントサイドの簡易パスワードゲート。
# 注意: 本格的な暗号防御ではなく「URL を知っている人＋鍵を知っている人」向けの
# 抑止レベルの保護。ページHTMLはソース上には存在するため、機密度の高い情報には使わない。
GATE_TEMPLATE = """
<div id="gate">
  <form id="gate-form" autocomplete="on">
    <div class="gate-lock">🔒</div>
    <div class="gate-title">ラーメン経営情報ボード</div>
    <div class="gate-sub">このページは保護されています</div>
    <input id="gate-user" name="username" placeholder="ユーザーID" autocomplete="username" autocapitalize="none" spellcheck="false">
    <input id="gate-pass" name="password" type="password" placeholder="パスワード" autocomplete="current-password">
    <button type="submit">ログイン</button>
    <div id="gate-err"></div>
  </form>
</div>
<style>
  body.gate-locked { overflow: hidden; height: 100vh; }
  #gate {
    position: fixed; inset: 0; z-index: 99999;
    display: flex; align-items: center; justify-content: center;
    background: #0a0a0f;
    background-image: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(99,102,241,0.12) 0%, transparent 60%);
    padding: 24px;
  }
  #gate-form {
    display: flex; flex-direction: column; gap: 12px;
    width: 100%; max-width: 320px;
    background: #111118; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 28px 24px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    font-family: 'Hiragino Sans','Noto Sans JP',sans-serif; color: #e4e4f0;
  }
  .gate-lock { font-size: 2rem; text-align: center; }
  .gate-title { font-size: 1.05rem; font-weight: 800; text-align: center; }
  .gate-sub { font-size: .75rem; color: #5a5a70; text-align: center; margin-bottom: 6px; }
  #gate-form input {
    background: #18181f; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 12px 14px; color: #e4e4f0; font-size: 1rem;
    outline: none;
  }
  #gate-form input:focus { border-color: #6366f1; }
  #gate-form button {
    background: #6366f1; color: #fff; border: none; border-radius: 10px;
    padding: 12px; font-size: .95rem; font-weight: 700; cursor: pointer; margin-top: 4px;
  }
  #gate-form button:active { opacity: .85; }
  #gate-err { color: #ff4757; font-size: .78rem; text-align: center; min-height: 1em; }
</style>
<script>
(function(){
  var HASH = "__HASH__";
  var KEY = "ramen-board-auth";
  async function sha256(s){
    var buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return Array.from(new Uint8Array(buf)).map(function(b){return b.toString(16).padStart(2,"0");}).join("");
  }
  function unlock(){
    var g = document.getElementById("gate");
    if (g) g.remove();
    document.body.classList.remove("gate-locked");
  }
  if (localStorage.getItem(KEY) === HASH) { unlock(); return; }
  document.body.classList.add("gate-locked");
  document.addEventListener("DOMContentLoaded", function(){
    var form = document.getElementById("gate-form");
    if (!form) return;
    form.addEventListener("submit", async function(e){
      e.preventDefault();
      var u = document.getElementById("gate-user").value.trim();
      var p = document.getElementById("gate-pass").value;
      var h = await sha256(u + ":" + p);
      if (h === HASH) { localStorage.setItem(KEY, HASH); unlock(); }
      else { document.getElementById("gate-err").textContent = "IDまたはパスワードが違います"; }
    });
  });
})();
</script>
"""


def build_gate_html():
    h = load_access_hash()
    if not h:
        return ""
    return GATE_TEMPLATE.replace("__HASH__", h)

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

    # --- Articles (filter to relevant only) ---
    gate_html = build_gate_html()

    relevant_indices = set(analysis.get("relevant_indices", []))
    # 1-indexed: index i in articles corresponds to article number i+1
    if relevant_indices:
        display_articles = [a for i, a in enumerate(articles) if (i + 1) in relevant_indices]
    else:
        display_articles = articles  # fallback: show all

    articles_html = ""
    for i, a in enumerate(display_articles):
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
  <meta name="theme-color" content="#0a0a0f">
  <title>ラーメン経営情報ボード — {TODAY}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
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
      /* モバイルベースのスペーシング */
      --pad-x: 16px;
      --pad-card: 16px;
      --gap: 12px;
    }}
    /* タブレット以上 */
    @media(min-width:640px) {{
      :root {{ --pad-x:24px; --pad-card:22px; --gap:16px; }}
    }}
    @media(min-width:1024px) {{
      :root {{ --pad-x:32px; --pad-card:24px; }}
    }}

    html {{ -webkit-text-size-adjust:100%; }} /* iOS自動拡大防止 */
    body {{
      font-family: 'Inter','Hiragino Sans','Noto Sans JP',sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      /* iOSのバウンススクロール時に背景が白くならないよう */
      overscroll-behavior: none;
    }}
    body::before {{
      content:'';
      position:fixed;
      inset:0;
      background: radial-gradient(ellipse 80% 50% at 15% 10%, {cfg["glow"]} 0%, transparent 60%),
                  radial-gradient(ellipse 60% 50% at 85% 85%, rgba(99,102,241,0.06) 0%, transparent 60%);
      animation: bgBreath 10s ease-in-out infinite alternate;
      pointer-events:none;
      z-index:0;
    }}
    @keyframes bgBreath {{
      from {{ opacity:.4; transform:scale(1); }}
      to   {{ opacity:.9; transform:scale(1.04); }}
    }}
    /* アニメーション省エネ設定 */
    @media(prefers-reduced-motion:reduce) {{
      *, *::before, *::after {{ animation-duration:.01ms !important; transition-duration:.01ms !important; }}
    }}

    .wrap {{ position:relative; z-index:1; max-width:1060px; margin:0 auto; padding:20px var(--pad-x) 60px; }}

    /* ── Header ── */
    header {{
      display:flex; align-items:center; justify-content:space-between;
      padding-bottom:20px; animation: fadeDown .5s ease both;
      gap:12px;
    }}
    .h-title {{
      font-size:clamp(1.05rem,4vw,1.5rem); font-weight:900; letter-spacing:-.02em;
      background:linear-gradient(120deg,#fff 30%,{cfg["color"]});
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
      line-height:1.2;
    }}
    .h-sub {{ color:var(--muted); font-size:.72rem; margin-top:3px; }}
    .live-badge {{
      flex-shrink:0;
      display:inline-flex; align-items:center; gap:5px;
      background:rgba(46,213,115,.08); border:1px solid rgba(46,213,115,.25);
      color:#2ed573; font-size:.65rem; font-weight:700; padding:5px 10px;
      border-radius:20px; letter-spacing:.06em; white-space:nowrap;
    }}
    .live-dot {{ width:6px;height:6px;background:#2ed573;border-radius:50%;
      animation:livePulse 1.4s ease-in-out infinite; }}
    @keyframes livePulse {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.3;transform:scale(.7)}} }}

    /* ── Alert hero ── */
    .alert-hero {{
      background:var(--alert-bg); border:1px solid {cfg["color"]}60;
      border-radius:18px; padding:20px var(--pad-card); margin-bottom:var(--gap);
      position:relative; overflow:hidden;
      animation:fadeUp .45s ease .05s both;
      box-shadow:0 0 40px var(--alert-glow), inset 0 1px 0 rgba(255,255,255,.04);
    }}
    .alert-hero::after {{
      content:''; position:absolute; top:-40px; right:-40px;
      width:200px; height:200px;
      background:radial-gradient(circle,var(--alert-glow) 0%,transparent 70%);
      pointer-events:none;
    }}
    .alert-row {{ display:flex; align-items:center; gap:8px; margin-bottom:12px; flex-wrap:wrap; }}
    .alert-badge {{
      background:var(--alert); color:#000; font-size:.7rem; font-weight:900;
      padding:5px 12px; border-radius:20px; letter-spacing:.1em;
      animation:badgePop .4s cubic-bezier(.34,1.56,.64,1) .3s both;
      box-shadow:0 0 16px var(--alert-glow);
    }}
    @keyframes badgePop {{ from{{transform:scale(0);opacity:0}} to{{transform:scale(1);opacity:1}} }}
    .alert-label-txt {{ color:var(--muted); font-size:.7rem; text-transform:uppercase; letter-spacing:.1em; }}
    .headline {{
      font-size:clamp(1rem,3.5vw,1.35rem); font-weight:800; line-height:1.5;
      color:#fff; letter-spacing:-.01em;
    }}

    /* ── Stats row ── */
    .stats-row {{
      display:grid;
      grid-template-columns: repeat(3,1fr);
      gap:var(--gap); margin-bottom:var(--gap);
    }}
    /* スマホでは2列→3列はきつい場合があるが数字が大きいので2列にする */
    @media(max-width:400px) {{ .stats-row {{ grid-template-columns:1fr 1fr; }} }}
    .stat-card {{
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:14px var(--pad-card);
      animation:fadeUp .45s ease both;
    }}
    /* ホバーはマウスがある端末のみ */
    @media(hover:hover) {{
      .stat-card:hover {{ transform:translateY(-2px); border-color:rgba(255,255,255,.14); transition:transform .2s,border-color .2s; }}
    }}
    .stat-label {{ color:var(--muted); font-size:.62rem; text-transform:uppercase; letter-spacing:.07em; margin-bottom:5px; }}
    .stat-value {{ font-size:clamp(1.4rem,4vw,1.8rem); font-weight:900; line-height:1; color:var(--text); }}
    .stat-value.accent {{ color:var(--alert); }}

    /* ── Grid ── */
    .grid-main {{ display:grid; grid-template-columns:1fr; gap:var(--gap); margin-bottom:var(--gap); }}
    @media(min-width:700px) {{ .grid-main {{ grid-template-columns:1fr 1fr; }} }}

    /* ── Card base ── */
    .card {{
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:var(--pad-card);
      animation:fadeUp .45s ease both;
    }}
    .card-title {{
      font-size:.65rem; text-transform:uppercase; letter-spacing:.1em;
      color:var(--muted); margin-bottom:14px;
      display:flex; align-items:center; gap:8px;
    }}
    .card-title::after {{ content:''; flex:1; height:1px; background:var(--border); }}

    /* ── Highlights ── */
    .highlights-list {{ display:flex; flex-direction:column; gap:10px; }}
    .highlight-card {{
      background:var(--surface2); border:1px solid var(--border);
      border-radius:10px; padding:12px;
    }}
    .highlight-tag {{
      display:inline-block; font-size:.66rem; font-weight:700;
      padding:2px 8px; border-radius:6px; border:1px solid;
      margin-bottom:7px; letter-spacing:.04em;
    }}
    .highlight-text {{ font-size:.84rem; line-height:1.7; color:var(--text); }}

    /* ── Actions ── */
    .actions-list {{ display:flex; flex-direction:column; gap:10px; }}
    .action-card {{
      background:var(--surface2); border:1px solid var(--border);
      border-radius:10px; padding:12px;
      animation:fadeLeft .4s ease both;
    }}
    /* タッチ端末でのフィードバック */
    .action-card:active {{ background: #1e1e2a; }}
    @media(hover:hover) {{
      .action-card:hover {{ border-color:rgba(255,255,255,.15); transform:translateX(3px); transition:border-color .2s,transform .2s; }}
    }}
    .action-top {{ margin-bottom:7px; }}
    .action-when {{
      display:inline-block; font-size:.66rem; font-weight:700;
      padding:3px 10px; border-radius:20px; border:1px solid; letter-spacing:.06em;
    }}
    .action-what {{ font-size:.87rem; font-weight:600; line-height:1.55; margin-bottom:5px; }}
    .action-why {{ font-size:.77rem; color:var(--muted); line-height:1.55; }}

    /* ── Cost items ── */
    .cost-list {{ display:flex; flex-direction:column; gap:8px; }}
    .cost-item {{
      display:grid; grid-template-columns:auto auto 1fr;
      align-items:start; gap:8px 10px;
      padding:10px 12px;
      background:var(--surface2); border-radius:8px;
      font-size:.83rem;
    }}
    /* スマホでは3列が窮屈なら2行に */
    @media(max-width:380px) {{
      .cost-item {{ grid-template-columns:auto auto; }}
      .cost-detail {{ grid-column:1/-1; }}
    }}
    .cost-name {{ font-weight:600; white-space:nowrap; }}
    .cost-dir  {{ font-weight:700; white-space:nowrap; }}
    .cost-detail {{ color:var(--muted); font-size:.76rem; line-height:1.5; }}

    /* ── Articles ── */
    .articles-list {{ display:flex; flex-direction:column; gap:8px; }}
    .article-card {{
      display:block; text-decoration:none; color:var(--text);
      background:var(--surface); border:1px solid var(--border);
      border-radius:10px; padding:14px;
      animation:fadeUp .3s ease both;
      /* タップ領域を確保 */
      min-height:44px;
    }}
    .article-card:active {{ background:var(--surface2); border-color:var(--alert); }}
    @media(hover:hover) {{
      .article-card:hover {{ border-color:var(--alert); background:var(--surface2); transform:translateX(4px); transition:border-color .2s,background .2s,transform .2s; }}
    }}
    .article-meta {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; flex-wrap:wrap; }}
    .article-label {{
      font-size:.64rem; font-weight:700; color:var(--alert);
      text-transform:uppercase; letter-spacing:.06em;
    }}
    .article-date {{ font-size:.66rem; color:var(--muted); }}
    .article-title {{ font-size:.87rem; font-weight:600; line-height:1.55; margin-bottom:4px; }}
    .article-summary {{ font-size:.78rem; color:#8888a0; line-height:1.6; }}

    /* ── Animations ── */
    @keyframes fadeDown {{ from{{opacity:0;transform:translateY(-14px)}} to{{opacity:1;transform:none}} }}
    @keyframes fadeUp   {{ from{{opacity:0;transform:translateY(14px)}}  to{{opacity:1;transform:none}} }}
    @keyframes fadeLeft {{ from{{opacity:0;transform:translateX(-14px)}} to{{opacity:1;transform:none}} }}

    footer {{ text-align:center; color:var(--muted); font-size:.7rem; padding-top:40px; animation:fadeUp .5s ease .9s both; }}
  </style>
</head>
<body>
{gate_html}
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
    <div class="card-title">関連記事 ({len(display_articles)}件 / 収集{len(articles)}件中) — タップで全文</div>
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
