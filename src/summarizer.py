"""Evidence-constrained analyst copy and output document construction."""

from __future__ import annotations

from datetime import datetime, timezone


def _sentence(text: str) -> str:
    clean = " ".join((text or "").split())
    for delimiter in (". ", "! ", "? "):
        if delimiter in clean:
            clean = clean.split(delimiter, 1)[0] + delimiter.strip()
            break
    return clean[:420].rstrip()


def analyst_summary(article: dict) -> tuple[str, str]:
    factual = _sentence(article.get("raw_summary")) or article["title"].rstrip(".") + "."
    if article["active_exploitation"]:
        why = "Defenders should treat this as an immediate exposure-management priority, confirm whether affected systems are internet-facing, review available indicators, and apply verified vendor mitigations or updates."
    elif article["cves"]:
        patch = " and prioritize the available security update" if article["patch_available"] else ""
        why = f"Organizations should inventory potentially affected products, review the original advisory{patch}, and monitor for credible exploitation evidence."
    elif article["category"] in {"Artificial Intelligence", "AI Security"}:
        why = "Security and technology teams should assess the development for changes to model risk, data handling, access controls, and their existing AI governance."
    elif article["category"] == "Data Breaches":
        why = "Potentially affected organizations and individuals should follow confirmed notifications, review exposed-data risk, and strengthen monitoring for follow-on fraud or credential abuse."
    else:
        why = "Security teams should review the original reporting, determine whether the development affects their environment, and adjust monitoring or controls when supported by verified details."
    return factual, why


def build_digest(
    articles: list[dict], source_status: list[dict], collected_count: int, deduplicated_count: int | None = None
) -> dict:
    stories = []
    for article in articles:
        summary, why = analyst_summary(article)
        stories.append(
            {
                "id": article["id"],
                "title": article["title"],
                "source": article["source"],
                "source_url": article["source_url"],
                "published_at": article["published_at"],
                "collected_at": article["collected_at"],
                "category": article["category"],
                "severity": article["severity"],
                "summary": summary,
                "why_it_matters": why,
                "affected_products": article["affected_products"],
                "affected_vendors": article["affected_vendors"],
                "cves": article["cves"],
                "cvss_score": article["cvss_score"],
                "known_exploited": article["known_exploited"],
                "active_exploitation": article["active_exploitation"],
                "patch_available": article["patch_available"],
                "vendor_advisory_url": article["vendor_advisory_url"],
                "mitre_techniques": article["mitre_techniques"],
                "tags": article["tags"],
                "importance_score": article["importance_score"],
                "score_breakdown": article["score_breakdown"],
                "related_sources": article["related_sources"],
            }
        )
    counts = {level: sum(s["severity"] == level for s in stories) for level in ("Critical", "High", "Medium", "Low")}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(source_status),
        "sources_succeeded": sum(s["status"] == "success" for s in source_status),
        "articles_collected": collected_count,
        "articles_after_deduplication": deduplicated_count if deduplicated_count is not None else len(stories),
        "stories_published": len(stories),
        "critical_count": counts["Critical"],
        "high_count": counts["High"],
        "medium_count": counts["Medium"],
        "low_count": counts["Low"],
        "source_status": source_status,
        "stories": stories,
    }
