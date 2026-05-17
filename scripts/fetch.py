import feedparser
import yaml
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG = ROOT / "config.yaml"
OUTPUT = ROOT / "docs" / "data" / "articles_raw.json"


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").replace("&nbsp;", " ").strip()


def fetch():
    with open(CONFIG, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    articles = []
    seen_titles = set()

    for feed_conf in config.get("feeds", []):
        url = feed_conf["url"]
        label = feed_conf.get("label", "")
        categories = feed_conf.get("categories", [])
        limit = feed_conf.get("limit", 10)

        print(f"  Fetching: {label} (最大{limit}件)")
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"    [WARN] {label} の取得に失敗: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= limit:
                break

            title = strip_html(entry.get("title", "")).strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            summary = strip_html(entry.get("summary", entry.get("description", "")))[:400]

            articles.append({
                "title": title,
                "link": entry.get("link", ""),
                "summary": summary,
                "published": entry.get("published", ""),
                "label": label,
                "categories": categories,
            })
            count += 1

        print(f"    → {count}件取得")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            {"fetched_at": datetime.now().isoformat(), "articles": articles},
            f, ensure_ascii=False, indent=2
        )

    print(f"\n  収集完了: 合計{len(articles)}件 → {OUTPUT.name}")


if __name__ == "__main__":
    fetch()
