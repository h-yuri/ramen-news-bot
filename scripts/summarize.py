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

    article_texts = "\n\n".join([
        f"[{i+1}] {a['title']}\n{a['summary'][:300]}"
        for i, a in enumerate(articles[:30])
    ])

    prompt = f"""あなたはラーメン店オーナーのビジネスアドバイザーです。
以下のニュース記事を読んで、今日の経営判断に直結する情報だけを抽出してください。

【絶対に守るルール】
- 「原材料費が高騰している」「競争が激化している」のような誰でも知っている一般論は書かない
- 必ず具体的な数字・企業名・商品名・割合・金額を含める
- 記事に数字がなければ「数字なし」と正直に書く
- アクションは「仕入れ先に連絡する」ではなく「◯◯の価格が◯月から上がるので今週中に◯◯と価格固定交渉」レベルまで具体化
- 一般論ではなく「このニュースを読んだから今週これをする」と言える内容にする

【記事一覧】
{article_texts}

【出力形式】必ずこのJSONのみで答えること（説明文不要）:
{{
  "alert_level": "high または medium または low",
  "headline": "今日最も重要な変化を25字以内で（例:豚骨が8月から15%値上げ確定）",
  "highlights": [
    {{"tag": "【コスト】", "text": "具体的な変化（数字・企業名入り）。例:製粉大手3社が7月から小麦粉を8〜12%値上げ通知。"}},
    {{"tag": "【競合】", "text": "競合の具体的な動き。"}},
    {{"tag": "【客数】", "text": "客足・消費行動の具体的なデータ。"}}
  ],
  "actions": [
    {{"what": "今週やること（動詞から始める）", "why": "◯◯というニュースがあったため", "when": "今週中/今月中/今日 など"}},
    {{"what": "...", "why": "...", "when": "..."}}
  ],
  "cost_items": [
    {{"name": "食材名", "direction": "上昇", "detail": "前月比+◯%など具体的な根拠"}},
    {{"name": "食材名", "direction": "横ばい", "detail": "根拠"}}
  ]
}}"""

    print("  Gemini API 呼び出し中...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text.strip()

    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        text = match.group(1).strip()

    analysis = json.loads(text)

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
