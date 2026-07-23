"""Fault-tolerant collection and normalization of untrusted RSS metadata."""

from __future__ import annotations

import hashlib
import html
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

import feedparser
import requests
from dateutil import parser as date_parser

from config import ARTICLE_MAX_AGE_DAYS, MAX_PER_FEED, REQUEST_TIMEOUT, USER_AGENT

LOG = logging.getLogger(__name__)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_text(value: object, limit: int = 4000) -> str:
    """Turn feed HTML into bounded plain text suitable for later display."""
    text = html.unescape(str(value or ""))
    text = TAG_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()
    return text[:limit]


def canonical_url(value: str) -> str:
    try:
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", parsed.query, ""))
    except (AttributeError, ValueError):
        return ""


def parse_date(item: dict) -> str | None:
    for field in ("published", "updated", "created"):
        value = item.get(field)
        if not value:
            continue
        try:
            parsed = date_parser.parse(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            continue
    return None


def collect_articles(feeds: list[dict], seen: set[str]) -> tuple[list[dict], list[dict]]:
    articles: list[dict] = []
    statuses: list[dict] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=ARTICLE_MAX_AGE_DAYS)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for source in feeds:
        status = {"source": source["name"], "url": source["url"], "status": "failed", "articles": 0}
        try:
            response = session.get(source["url"], timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if parsed.bozo and not parsed.entries:
                raise ValueError(f"invalid feed: {parsed.bozo_exception}")

            for item in parsed.entries[:MAX_PER_FEED]:
                url = canonical_url(item.get("link", ""))
                title = clean_text(item.get("title"), 300)
                if not url or not title or url in seen:
                    continue
                published_at = parse_date(item)
                if published_at and date_parser.isoparse(published_at) < cutoff:
                    continue
                summary = clean_text(
                    item.get("summary") or item.get("description") or item.get("content", [{}])[0].get("value"),
                    2000,
                )
                articles.append(
                    {
                        "id": hashlib.sha256(url.encode()).hexdigest()[:16],
                        "title": title,
                        "source": source["name"],
                        "source_url": url,
                        "published_at": published_at,
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                        "raw_summary": summary,
                        "source_kind": source["kind"],
                    }
                )
                status["articles"] += 1
            status["status"] = "success" if status["articles"] else "no_new_articles"
        except (requests.RequestException, ValueError, AttributeError) as exc:
            status["error"] = clean_text(exc, 300)
            LOG.warning("Source failed: %s (%s)", source["name"], exc)
        statuses.append(status)
        LOG.info("Source %-30s %s (%d)", source["name"], status["status"], status["articles"])
    return articles, statuses
