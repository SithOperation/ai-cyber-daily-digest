import feedparser
import json
import os
import re
import requests
import time
from pathlib import Path
from datetime import datetime, timezone

STATE_FILE = Path("ai_cyber_digest_state.json")
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

MAX_PER_CATEGORY = 5
MAX_ENTRIES_PER_FEED = 8
DISCORD_LIMIT = 1900

AI_FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://ai.meta.com/blog/rss/",
    "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
    "https://mistral.ai/news/feed.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://www.marktechpost.com/feed/",
    "https://www.unite.ai/feed/",
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.LG",
    "https://machinelearningmastery.com/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.analyticsvidhya.com/blog/feed/",
]

CYBER_FEEDS = [
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://krebsonsecurity.com/feed/",
    "https://www.bleepingcomputer.com/feed/",
    "https://www.darkreading.com/rss/all.xml",
    "https://isc.sans.edu/rssfeed.xml",
    "https://unit42.paloaltonetworks.com/feed/",
    "https://cloud.google.com/blog/topics/threat-intelligence/rss/",
    "https://www.crowdstrike.com/blog/feed/",
    "https://www.mandiant.com/resources/blog/rss.xml",
    "https://securelist.com/feed/",
    "https://googleprojectzero.blogspot.com/feeds/posts/default",
    "https://blog.talosintelligence.com/rss/",
    "https://www.rapid7.com/blog/rss/",
    "https://www.tenable.com/blog/cybersecurity-guide/rss.xml",
    "https://www.sentinelone.com/blog/rss/",
    "https://redcanary.com/feed/",
    "https://therecord.media/feed",
]

AI_KEYWORDS = {
    "model": 5,
    "new model": 8,
    "release": 5,
    "released": 5,
    "breakthrough": 8,
    "reasoning": 7,
    "agent": 6,
    "agents": 6,
    "open source": 7,
    "benchmark": 5,
    "multimodal": 6,
    "robotics": 6,
    "inference": 5,
    "training": 4,
    "llm": 5,
    "agi": 6,
    "alignment": 5,
    "safety": 4,
    "chip": 4,
    "gpu": 4,
}

CYBER_KEYWORDS = {
    "zero-day": 10,
    "zero day": 10,
    "actively exploited": 10,
    "exploited": 8,
    "ransomware": 9,
    "breach": 8,
    "data leak": 8,
    "cve": 7,
    "kev": 7,
    "malware": 7,
    "apt": 7,
    "nation-state": 8,
    "phishing": 5,
    "backdoor": 7,
    "botnet": 6,
    "critical": 6,
    "vulnerability": 6,
    "patch": 5,
    "microsoft": 4,
    "windows": 4,
    "linux": 4,
}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_links": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def trim(text, max_len=240):
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."

def send_discord_alert(message):
    message = message[:DISCORD_LIMIT]

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=20
    )

    if response.status_code == 429:
        retry_after = response.json().get("retry_after", 5)
        time.sleep(retry_after + 1)

        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=20
        )

    response.raise_for_status()
    time.sleep(2)

def score_story(title, summary, keywords):
    text = f"{title} {summary}".lower()
    score = 0
    matched = []

    for keyword, points in keywords.items():
        if keyword in text:
            score += points
            matched.append(keyword)

    if any(word in text for word in ["today", "new", "launch", "announced", "warning", "alert"]):
        score += 3

    if title:
        score += 2

    return score, matched[:5]

def parse_rss_feed(feed_url, category, keywords):
    stories = []

    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
        title = trim(getattr(entry, "title", ""), 180)
        link = getattr(entry, "link", "")
        summary = trim(getattr(entry, "summary", ""), 200)

        if not title or not link:
            continue

        score, matched = score_story(title, summary, keywords)

        if score <= 0:
            continue

        stories.append({
            "category": category,
            "title": title,
            "link": link,
            "score": score,
            "matched": matched,
            "source": trim(feed.feed.get("title", "Unknown source"), 80),
        })

    return stories

def parse_cisa_kev_json():
    stories = []

    try:
        response = requests.get(
            "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
            headers={"User-Agent": "AI-Cyber-Daily-Digest/1.0"},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        for vuln in data.get("vulnerabilities", [])[:25]:
            cve_id = vuln.get("cveID", "")
            vendor = vuln.get("vendorProject", "")
            product = vuln.get("product", "")
            name = vuln.get("vulnerabilityName", "")
            link = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"

            title = f"{cve_id}: {vendor} {product} - {name}"

            score, matched = score_story(title, "known exploited vulnerability", CYBER_KEYWORDS)

            stories.append({
                "category": "Cybersecurity",
                "title": trim(title, 180),
                "link": link,
                "score": score + 10,
                "matched": matched + ["known exploited"],
                "source": "CISA KEV Catalog",
            })

    except Exception as e:
        print(f"CISA KEV error: {e}")

    return stories

def collect_stories(feeds, category, keywords):
    all_stories = []

    for feed_url in feeds:
        try:
            all_stories.extend(parse_rss_feed(feed_url, category, keywords))
        except Exception as e:
            print(f"Feed error: {feed_url} — {e}")

    return all_stories

def dedupe_and_rank(stories, seen_links, limit):
    unique = {}

    for story in stories:
        link = story["link"]

        if link in seen_links:
            continue

        key = re.sub(r"[^a-z0-9]+", " ", story["title"].lower()).strip()

        if key not in unique or story["score"] > unique[key]["score"]:
            unique[key] = story

    ranked = sorted(unique.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:limit]

def format_category_digest(title, stories):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"{title} — {today}",
        ""
    ]

    if not stories:
        lines.append("No strong stories found today.")
    else:
        for index, story in enumerate(stories, 1):
            tags = ", ".join(story["matched"]) if story["matched"] else "general"

            lines.append(
                f"{index}. **{story['title']}**\n"
                f"Source: {story['source']} | Tags: {tags}\n"
                f"{story['link']}"
            )

    return "\n\n".join(lines)[:DISCORD_LIMIT]

def main():
    state = load_state()
    seen_links = set(state.get("seen_links", []))

    ai_stories = collect_stories(AI_FEEDS, "AI", AI_KEYWORDS)
    cyber_stories = collect_stories(CYBER_FEEDS, "Cybersecurity", CYBER_KEYWORDS)
    cyber_stories.extend(parse_cisa_kev_json())

    top_ai = dedupe_and_rank(ai_stories, seen_links, MAX_PER_CATEGORY)
    top_cyber = dedupe_and_rank(cyber_stories, seen_links, MAX_PER_CATEGORY)

    ai_message = format_category_digest("🧠 **Top 5 AI Stories**", top_ai)
    cyber_message = format_category_digest("🔐 **Top 5 Cybersecurity Stories**", top_cyber)

    send_discord_alert(ai_message)
    send_discord_alert(cyber_message)

    for story in top_ai + top_cyber:
        seen_links.add(story["link"])

    state["seen_links"] = list(seen_links)[-5000:]
    state["last_digest"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

if __name__ == "__main__":
    main()
