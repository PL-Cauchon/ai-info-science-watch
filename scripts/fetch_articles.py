"""
fetch_articles.py
Fetches RSS feeds relevant to AI in information sciences,
categorizes articles by keyword, and appends new entries to data/articles.json.
Run daily via GitHub Actions.
"""

import feedparser
import json
import os
import re
import hashlib
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# RSS feed sources
# ---------------------------------------------------------------------------
FEEDS = [
    # Knowledge Management & AI
    {"url": "https://www.kmworld.com/rss/",                         "source": "KMWorld"},
    {"url": "https://www.aiim.org/feed/",                           "source": "AIIM"},
    {"url": "https://www.information-management.com/feed/",         "source": "Information Management"},

    # Libraries & Archives
    {"url": "https://americanlibrariesmagazine.org/feed/",          "source": "American Libraries"},
    {"url": "https://www.libraryjournal.com/?feed=rss2",            "source": "Library Journal"},
    {"url": "https://blogs.loc.gov/thesignal/feed/",                "source": "LOC Signal"},
    {"url": "https://hangingtogether.org/feed/",                    "source": "OCLC Research"},
    {"url": "https://www.cilip.org.uk/feed",                        "source": "CILIP"},

    # Information Retrieval (arXiv)
    {"url": "https://arxiv.org/rss/cs.IR",                          "source": "arXiv: Information Retrieval"},
    {"url": "https://arxiv.org/rss/cs.DL",                          "source": "arXiv: Digital Libraries"},

    # AI broader (filtered by keyword at categorization)
    {"url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "source": "MIT Tech Review"},
    {"url": "https://www.wired.com/feed/tag/ai/latest/rss",         "source": "Wired AI"},

    # Governance & policy
    {"url": "https://fpf.org/feed/",                                "source": "Future of Privacy Forum"},
    {"url": "https://www.nist.gov/blogs/cybersecurity-insights/rss.xml", "source": "NIST"},
]

# ---------------------------------------------------------------------------
# Category keyword mapping (first match wins; order = priority)
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("AI & Knowledge Management", [
        "knowledge management", " rag ", "retrieval-augmented", "retrieval augmented",
        "chatbot", "llm", "large language model", "generative ai", "gen ai",
        "copilot", "knowledge base", "knowledge graph", "conversational ai",
    ]),
    ("Records Management & AI", [
        "records management", "records retention", "document management",
        "ecm", "enterprise content management", "records lifecycle",
        "information lifecycle", "recordkeeping", "record keeping",
        "disposition", "vital records",
    ]),
    ("Information Retrieval & Search", [
        "information retrieval", "semantic search", "vector search",
        "taxonomy", "ontology", "metadata", "indexing", "index",
        "search engine", "embedding", "full-text search",
    ]),
    ("Libraries & Archives", [
        "library", "libraries", "archive", "archival", "cataloging", "cataloguing",
        "preservation", "digital library", "special library", "librarian",
        "digital preservation", "finding aid",
    ]),
    ("Information Behavior", [
        "information behavior", "information behaviour", "information seeking",
        "information literacy", "information need", "user behavior",
        "information practice",
    ]),
    ("AI Training & Literacy", [
        "ai training", "ai literacy", "ai education", "prompt engineering",
        "ai adoption", "ai tools for", "ai skills", "upskilling",
        "learning ai", "ai workshop", "ai tutorial",
    ]),
    ("Enterprise Information Management", [
        "enterprise information", "information management", "intranet",
        "enterprise ai", "enterprise search", "organizational knowledge",
        "corporate knowledge", "business intelligence", "sharepoint",
        "content strategy",
    ]),
    ("AI & Information Governance", [
        "ai governance", "information governance", "ai policy", "ai regulation",
        "ai ethics", "ai risk", "responsible ai", "data governance",
        "ai compliance", "ai act", "algorithmic accountability",
    ]),
]

DEFAULT_CATEGORY = "AI & Information Sciences"


def categorize(title: str, summary: str) -> str:
    text = (" " + title + " " + summary + " ").lower()
    for category, keywords in CATEGORIES:
        if any(kw in text for kw in keywords):
            return category
    return DEFAULT_CATEGORY


def parse_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def article_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500] + ("…" if len(text) > 500 else "")


def load_existing() -> dict:
    path = os.path.join("data", "articles.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {a["id"]: a for a in data}
    return {}


def save_articles(articles: dict):
    os.makedirs("data", exist_ok=True)
    sorted_list = sorted(articles.values(), key=lambda a: a["date"], reverse=True)
    with open(os.path.join("data", "articles.json"), "w", encoding="utf-8") as f:
        json.dump(sorted_list, f, ensure_ascii=False, indent=2)


def main():
    existing = load_existing()
    new_count = 0

    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:25]:
                url = entry.get("link", "").strip()
                if not url:
                    continue
                aid = article_id(url)
                if aid in existing:
                    continue

                title = strip_html(entry.get("title", "Untitled"))
                raw_summary = entry.get("summary", entry.get("description", ""))
                summary = strip_html(raw_summary)
                date = parse_date(entry)
                category = categorize(title, summary)

                existing[aid] = {
                    "id": aid,
                    "title": title,
                    "url": url,
                    "source": feed_info["source"],
                    "date": date,
                    "summary": summary,
                    "category": category,
                }
                new_count += 1
                print(f"  + [{category}] {title[:70]}")

        except Exception as e:
            print(f"ERROR fetching {feed_info['url']}: {e}")

    save_articles(existing)
    print(f"\nDone — {new_count} new articles added. Total: {len(existing)}")


if __name__ == "__main__":
    main()
