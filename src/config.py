"""Configuration for the standalone AI & Cyber Daily Digest."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RSS_FEEDS = [
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "kind": "cyber"},
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/", "kind": "cyber"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "kind": "cyber"},
    {"name": "SecurityWeek", "url": "https://www.securityweek.com/feed/", "kind": "cyber"},
    {"name": "CISA Cybersecurity Advisories", "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "kind": "government"},
    {"name": "MIT News AI", "url": "https://news.mit.edu/rss/topic/artificial-intelligence2", "kind": "ai"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "kind": "ai"},
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml", "kind": "ai"},
]

MAX_ARTICLES = 20
MAX_PER_FEED = 25
ARTICLE_MAX_AGE_DAYS = 4
REQUEST_TIMEOUT = 20
USER_AGENT = "AI-Cyber-Daily-Digest/2.0 (+https://github.com/SithOperation/ai-cyber-daily-digest)"

STATE_FILE = ROOT / "data" / "ai_cyber_digest_state.json"
DIGEST_FILE = ROOT / "data" / "ai_cyber_digest.json"
MARKDOWN_OUTPUT = ROOT / "output" / "latest_digest.md"
