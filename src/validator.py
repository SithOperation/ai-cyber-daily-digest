"""Strict validation before publishing a digest."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

SEVERITIES = {"Critical", "High", "Medium", "Low"}
REQUIRED = {
    "id", "title", "source", "source_url", "published_at", "collected_at", "category",
    "severity", "summary", "why_it_matters", "affected_products", "affected_vendors",
    "cves", "cvss_score", "known_exploited", "active_exploitation", "patch_available",
    "mitre_techniques", "tags", "importance_score",
}


def _valid_url(value: object) -> bool:
    parsed = urlparse(value) if isinstance(value, str) else None
    return bool(parsed and parsed.scheme in {"http", "https"} and parsed.netloc)


def _valid_date(value: object, nullable: bool = False) -> bool:
    if value is None:
        return nullable
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return "T" in str(value)
    except ValueError:
        return False


def validate_digest(digest: dict, allow_empty: bool = False) -> None:
    stories = digest.get("stories")
    if not isinstance(stories, list):
        raise ValueError("stories must be a list")
    if not stories and not allow_empty:
        raise ValueError("digest is unexpectedly empty")
    ids = set()
    for index, story in enumerate(stories):
        missing = REQUIRED - story.keys()
        if missing:
            raise ValueError(f"story {index} missing fields: {sorted(missing)}")
        if story["id"] in ids:
            raise ValueError(f"duplicate story id: {story['id']}")
        ids.add(story["id"])
        if story["severity"] not in SEVERITIES:
            raise ValueError(f"invalid severity: {story['severity']}")
        if not _valid_url(story["source_url"]):
            raise ValueError(f"invalid URL: {story['source_url']}")
        if not _valid_date(story["published_at"], nullable=True) or not _valid_date(story["collected_at"]):
            raise ValueError(f"invalid date in story {story['id']}")
    if not _valid_date(digest.get("generated_at")):
        raise ValueError("invalid generated_at")
