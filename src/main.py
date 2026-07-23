"""Entry point for the standalone AI & Cyber Daily Digest."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from config import DIGEST_FILE, MARKDOWN_OUTPUT, MAX_ARTICLES, RSS_FEEDS
from feeds import collect_articles
from ranker import deduplicate, rank_articles
from state import load_state, save_state
from summarizer import build_digest
from validator import validate_digest

LOG = logging.getLogger("digest")


def markdown_for(digest: dict) -> str:
    lines = [
        "# AI & Cyber Intelligence Digest", "",
        f"Generated: {digest['generated_at']}", "",
        "A prioritized briefing of recent cybersecurity and artificial intelligence developments.", "",
    ]
    sections = [
        ("Critical stories", {"Critical"}),
        ("High-priority stories", {"High"}),
        ("Other notable developments", {"Medium", "Low"}),
    ]
    for heading, severities in sections:
        matching = [story for story in digest["stories"] if story["severity"] in severities]
        if not matching:
            continue
        lines.extend([f"## {heading}", ""])
        for story in matching:
            lines.extend(
                [
                    f"### [{story['title']}]({story['source_url']})", "",
                    f"**{story['severity']} · {story['category']} · Score {story['importance_score']} · {story['source']}**", "",
                    story["summary"], "", f"**Why it matters:** {story['why_it_matters']}", "",
                ]
            )
            if story["cves"]:
                lines.extend([f"**CVEs:** {', '.join(story['cves'])}", ""])
    lines.extend(["## Sources", ""])
    for status in digest["source_status"]:
        lines.append(f"- {status['source']}: {status['status']} ({status['articles']} new)")
    lines.append("")
    return "\n".join(lines)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def run(allow_empty: bool = False) -> dict | None:
    state = load_state()
    articles, statuses = collect_articles(RSS_FEEDS, set(state.get("seen_links", [])))
    LOG.info("Collected %d new candidate articles", len(articles))
    if not articles and not allow_empty:
        LOG.info("No new articles; preserving the last known good digest")
        return None

    ranked = rank_articles(articles)
    unique = deduplicate(ranked)
    digest = build_digest(unique[:MAX_ARTICLES], statuses, len(articles), len(unique))
    validate_digest(digest, allow_empty=allow_empty)

    # Validation happens before either public artifact is replaced.
    atomic_write(DIGEST_FILE, json.dumps(digest, indent=2, ensure_ascii=False) + "\n")
    atomic_write(MARKDOWN_OUTPUT, markdown_for(digest))
    # Mark every successfully processed candidate, not only the final top stories,
    # so lower-ranked items do not reappear as "new" on every subsequent run.
    state["seen_links"] = state.get("seen_links", []) + [article["source_url"] for article in articles]
    save_state(state)
    LOG.info("Published %d validated stories", len(digest["stories"]))
    return digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true", help="validate the current JSON output")
    parser.add_argument("--allow-empty", action="store_true", help="permit empty output (intended for tests only)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.validate_only:
        validate_digest(json.loads(DIGEST_FILE.read_text(encoding="utf-8")), allow_empty=args.allow_empty)
        LOG.info("Digest validation passed")
        return
    run(allow_empty=args.allow_empty)


if __name__ == "__main__":
    main()
