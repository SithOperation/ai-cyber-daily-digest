import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from feeds import canonical_url, clean_text
from ranker import deduplicate, enrich, rank_articles
from summarizer import build_digest
from validator import validate_digest


def article(title, url, summary, source="Test Security", kind="cyber"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": url.rsplit("/", 1)[-1],
        "title": title,
        "source": source,
        "source_url": url,
        "published_at": now,
        "collected_at": now,
        "raw_summary": summary,
        "source_kind": kind,
    }


class PipelineTests(unittest.TestCase):
    def test_untrusted_html_is_removed(self):
        self.assertEqual(clean_text("<script>alert(1)</script><b>Safe</b>"), "alert(1) Safe")
        self.assertEqual(canonical_url("javascript:alert(1)"), "")

    def test_extracts_only_explicit_cve_evidence(self):
        result = enrich(article(
            "CVE-2026-12345 is exploited in the wild",
            "https://example.com/a",
            "CVSS score: 9.8. A security update is available.",
        ))
        self.assertEqual(result["cves"], ["CVE-2026-12345"])
        self.assertEqual(result["cvss_score"], 9.8)
        self.assertTrue(result["active_exploitation"])
        self.assertTrue(result["patch_available"])
        self.assertEqual(result["mitre_techniques"], [])

    def test_deduplicates_matching_cves(self):
        items = rank_articles([
            article("Vendor fixes critical issue", "https://example.com/a", "CVE-2026-12345"),
            article("CVE exploited in a popular product", "https://other.example/b", "CVE-2026-12345"),
        ])
        unique = deduplicate(items)
        self.assertEqual(len(unique), 1)
        self.assertEqual(len(unique[0]["related_sources"]), 1)

    def test_complete_digest_validates(self):
        raw = [article("Important AI model release", "https://example.com/ai", "A major artificial intelligence model was released.", kind="ai")]
        stories = deduplicate(rank_articles(raw))
        status = [{"source": "Test", "url": "https://example.com/feed", "status": "success", "articles": 1}]
        digest = build_digest(stories, status, 1)
        validate_digest(digest)


if __name__ == "__main__":
    unittest.main()
