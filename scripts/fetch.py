import feedparser
import yaml
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG = ROOT / "config.yaml"
OUTPUT = ROOT / "docs" / "data" / "articles_raw.json"


def fetch():
    with open(CONFIG, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    articles = []
    for feed_conf in config.get("feeds", []):
        url = feed_conf["url"]
        label = feed_conf.get("label", "")
        categories = feed_conf.get("categories", [])

        print(f"  Fetching: {label}")
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "published": entry.get("published", ""),
                "label": label,
                "categories": categories,
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            {"fetched_at": datetime.now().isoformat(), "articles": articles},
            f, ensure_ascii=False, indent=2
        )

    print(f"  収集完了: {len(articles)}件 → {OUTPUT.name}")


if __name__ == "__main__":
    fetch()
