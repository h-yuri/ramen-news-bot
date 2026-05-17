import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

ROOT = Path(__file__).parent.parent
RAW = ROOT / "docs" / "data" / "articles_raw.json"
TODAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT = ROOT / "docs" / "data" / f"{TODAY}.json"

# Gemini 2.5 Flash free tier: input ~1M tokens/min, 500 req/day
# 80 articles × 400 chars ≈ 32,000 chars ≈ 10,000 tokens → 余裕あり
MAX_ARTICLES = 80


def summarize():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。.env を確認してください。")

    client = genai.Client(api_key=api_key)

    with open(RAW, encoding="utf-8") as f:
        data = json.load(f)

    articles = data["articles"]
    if not articles:
        print("  記事が0件のため要約をスキップします")
        _write_empty(articles)
        return

    # カテゴリ別に整理して文脈を作る
    used = articles[:MAX_ARTICLES]
    article_texts = "\n\n".join([
        f"[{i+1}/{len(used)}|{a['label']}] {a['title']}\n{a['summary'][:350]}"
        for i, a in enumerate(used)
    ])

    prompt = f"""あなたはラーメン店オーナーの経営アドバイザーです。
以下は今日の日本・世界のニュース（{len(used)}件）です。
記事の中にラーメン店に直接関係しないものも多くありますが、**すべての記事をラーメン店経営者の視点で解釈**してください。

例：
- 「円安進行」→ 輸入小麦・豚骨・醤油の仕入れコスト上昇リスク
- 「最低賃金引き上げ議論」→ アルバイト時給の先読みと採用戦略
- 「猛暑予報」→ ラーメン離れの季節リスク、冷やし系メニュー検討
- 「大手チェーン値上げ」→ 自店の値上げタイミングの参考
- 「消費者物価指数上昇」→ 客単価維持の難しさと来店頻度低下リスク

【絶対ルール】
1. 「コストが上がっている」「競争が激しい」のような一般論は書かない
2. 必ず具体的な数字・企業名・品目・割合・時期を入れる（記事に数字がなければ「数値不明」と記載）
3. アクションは「今週中に◯◯する、なぜなら◯◯という記事があったから」レベルまで具体化する
4. ラーメン店に直接関係なさそうなニュースでも、経営への影響を必ず考察する

【記事一覧】
{article_texts}

以下のJSONのみで回答（前後に余計なテキスト不要）:
{{
  "alert_level": "high または medium または low",
  "headline": "今日最も重要な経営インパクト（25字以内）",
  "highlights": [
    {{"tag": "【コスト】",  "text": "具体的な変化（数字・企業名・品目入り）"}},
    {{"tag": "【人件費】",  "text": ""}},
    {{"tag": "【客数・消費】", "text": ""}},
    {{"tag": "【競合・業界】", "text": ""}},
    {{"tag": "【世界情勢→経営】", "text": "一見無関係なニュースのラーメン経営への影響"}}
  ],
  "actions": [
    {{"what": "今週やること（動詞で始める）", "why": "◯◯という記事があったため", "when": "今日/今週中/今月中"}},
    {{"what": "", "why": "", "when": ""}},
    {{"what": "", "why": "", "when": ""}}
  ],
  "cost_items": [
    {{"name": "食材・コスト項目名", "direction": "上昇/横ばい/下降", "detail": "根拠となる数字や記事内容"}}
  ]
}}"""

    print(f"  Gemini API 呼び出し中（{len(used)}件の記事を分析）...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text.strip()

    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        text = match.group(1).strip()

    analysis = json.loads(text)

    # highlights の空エントリを除去
    analysis["highlights"] = [h for h in analysis.get("highlights", []) if h.get("text")]
    analysis["actions"] = [a for a in analysis.get("actions", []) if a.get("what")]

    result = {
        "date": TODAY,
        "generated_at": datetime.now().isoformat(),
        "articles": articles,
        "analysis": analysis,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  要約完了 → {OUTPUT.name}")
    print(f"  ヘッドライン: {analysis.get('headline', '')}")
    print(f"  アラートレベル: {analysis['alert_level']}")
    print(f"  アクション数: {len(analysis.get('actions', []))}件")


def _write_empty(articles):
    result = {
        "date": TODAY,
        "generated_at": datetime.now().isoformat(),
        "articles": articles,
        "analysis": {
            "alert_level": "low",
            "headline": "収集記事なし",
            "highlights": [],
            "actions": [],
            "cost_items": [],
        },
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    summarize()
