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
        result = {
            "date": TODAY,
            "generated_at": datetime.now().isoformat(),
            "articles": [],
            "analysis": {
                "alert_level": "low",
                "summary": "収集記事なし",
                "key_topics": [],
                "cost_trend": "横ばい",
                "action_items": [],
            },
        }
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return

    article_texts = "\n\n".join([
        f"[{i+1}] {a['title']}\n{a['summary'][:200]}"
        for i, a in enumerate(articles[:30])
    ])

    prompt = f"""以下はラーメン業界・飲食業界に関するニュース記事です。
ラーメン店経営者の視点で分析してください。

{article_texts}

必ず以下のJSON形式のみで回答してください（前後に余計なテキスト不要）:
{{
  "alert_level": "low または medium または high",
  "summary": "経営者向けの全体サマリー（200文字以内）",
  "key_topics": ["トピック1", "トピック2", "トピック3"],
  "cost_trend": "上昇 または 横ばい または 下降",
  "action_items": ["推奨アクション1", "推奨アクション2"]
}}"""

    print("  Gemini API 呼び出し中...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text.strip()

    # Extract JSON block if wrapped in markdown
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
    print(f"  アラートレベル: {analysis['alert_level']}")


if __name__ == "__main__":
    summarize()
