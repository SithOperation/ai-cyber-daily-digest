"""Content classification, evidence extraction, deduplication, and ranking."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)
CVSS_RE = re.compile(r"\bCVSS(?:\s+(?:v\d(?:\.\d)?|score))?\s*[:\-]?\s*(10(?:\.0)?|[0-9](?:\.\d)?)\b", re.I)
TOKEN_RE = re.compile(r"[a-z0-9]+")

CATEGORIES = [
    ("Active Exploitation", ("actively exploited", "active exploitation", "exploited in the wild", "zero-day", "0-day")),
    ("Ransomware", ("ransomware", "extortion")),
    ("Nation-State Activity", ("nation-state", "state-sponsored", "apt ", "china-linked", "russia-linked", "iran-linked", "north korea")),
    ("Data Breaches", ("data breach", "data leak", "stolen data", "records exposed")),
    ("Supply Chain", ("supply chain", "dependency confusion", "malicious package")),
    ("Cloud Security", ("cloud security", "aws ", "azure ", "google cloud", "kubernetes", "container")),
    ("AI Security", ("prompt injection", "model poisoning", "jailbreak", "ai security", "llm security", "adversarial ai")),
    ("Malware", ("malware", "trojan", "backdoor", "botnet", "infostealer", "spyware")),
    ("Privacy", ("privacy", "data protection", "surveillance")),
    ("Government Advisories", ("cisa", "fbi warning", "government advisory", "cybersecurity advisory")),
    ("Critical Vulnerabilities", ("critical vulnerability", "critical flaw", "remote code execution", "rce", "cve-")),
    ("Artificial Intelligence", ("artificial intelligence", "generative ai", "large language model", "machine learning", " llm", "ai model", "ai agent")),
]

LOW_VALUE = ("sponsored", "webinar", "podcast", "deal", "giveaway", "how to watch", "best laptop")


def article_text(article: dict) -> str:
    return f"{article.get('title', '')} {article.get('raw_summary', '')}".lower()


def categorize(article: dict) -> str:
    text = article_text(article)
    for category, terms in CATEGORIES:
        if any(term in text for term in terms):
            return category
    return "General Cybersecurity" if article.get("source_kind") != "ai" else "Artificial Intelligence"


def enrich(article: dict) -> dict:
    text = article_text(article)
    article["cves"] = sorted({match.upper() for match in CVE_RE.findall(text)})
    match = CVSS_RE.search(text)
    article["cvss_score"] = float(match.group(1)) if match else None
    article["known_exploited"] = any(term in text for term in ("known exploited vulnerabilities", "cisa kev", "kev catalog"))
    article["active_exploitation"] = article["known_exploited"] or any(
        term in text for term in ("actively exploited", "active exploitation", "exploited in the wild", "attacks in the wild")
    )
    article["patch_available"] = any(
        term in text for term in ("patch available", "security update", "fixed in", "apply the update", "released patches")
    )
    article["zero_day"] = any(term in text for term in ("zero-day", "zero day", "0-day"))
    article["affected_products"] = []
    article["affected_vendors"] = []
    article["mitre_techniques"] = []
    article["vendor_advisory_url"] = None
    article["category"] = categorize(article)
    article["tags"] = sorted(
        {
            tag
            for tag, terms in {
                "CVE": ("cve-",),
                "Zero-Day": ("zero-day", "zero day", "0-day"),
                "Ransomware": ("ransomware",),
                "Malware": ("malware", "trojan", "backdoor"),
                "Data Breach": ("data breach", "data leak"),
                "AI": ("artificial intelligence", "generative ai", "llm", "ai model"),
            }.items()
            if any(term in text for term in terms)
        }
    )
    return article


def _title_tokens(title: str) -> set[str]:
    stop = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
    return {token for token in TOKEN_RE.findall(title.lower()) if token not in stop}


def _same_event(left: dict, right: dict) -> bool:
    if set(left["cves"]) & set(right["cves"]):
        return True
    lt, rt = _title_tokens(left["title"]), _title_tokens(right["title"])
    overlap = len(lt & rt) / max(1, len(lt | rt))
    title_ratio = SequenceMatcher(None, left["title"].lower(), right["title"].lower()).ratio()
    return overlap >= 0.58 or title_ratio >= 0.82


def _source_strength(article: dict) -> tuple:
    priority = {"government": 3, "cyber": 2, "ai": 1}.get(article.get("source_kind"), 0)
    return priority, len(article.get("raw_summary", ""))


def deduplicate(articles: list[dict]) -> list[dict]:
    unique: list[dict] = []
    for candidate in articles:
        duplicate = next((existing for existing in unique if _same_event(existing, candidate)), None)
        if not duplicate:
            candidate["related_sources"] = []
            unique.append(candidate)
            continue
        primary, secondary = (candidate, duplicate) if _source_strength(candidate) > _source_strength(duplicate) else (duplicate, candidate)
        related = primary.setdefault("related_sources", [])
        reference = {"source": secondary["source"], "source_url": secondary["source_url"]}
        if reference not in related:
            related.append(reference)
        if primary is candidate:
            unique[unique.index(duplicate)] = candidate
    return unique


def score_article(article: dict) -> tuple[int, list[dict]]:
    text = article_text(article)
    signals: list[tuple[str, int, bool]] = [
        ("Active exploitation", 25, article["active_exploitation"]),
        ("CISA KEV", 20, article["known_exploited"]),
        ("Zero-day", 18, article["zero_day"]),
        ("Critical CVSS", 18, article["cvss_score"] is not None and article["cvss_score"] >= 9),
        ("High CVSS", 10, article["cvss_score"] is not None and 7 <= article["cvss_score"] < 9),
        ("Critical infrastructure", 12, any(x in text for x in ("critical infrastructure", "hospital", "energy sector", "water utility"))),
        ("Nation-state activity", 12, article["category"] == "Nation-State Activity"),
        ("Ransomware", 12, article["category"] == "Ransomware"),
        ("Major data exposure", 10, article["category"] == "Data Breaches"),
        ("Government advisory", 8, article["source_kind"] == "government" or article["category"] == "Government Advisories"),
        ("AI security relevance", 8, article["category"] == "AI Security"),
        ("Patch available", 4, article["patch_available"]),
        ("CVE cited", 4, bool(article["cves"])),
    ]
    evidence = [{"signal": name, "points": points} for name, points, applies in signals if applies]
    return min(100, sum(item["points"] for item in evidence)), evidence


def rank_articles(articles: list[dict]) -> list[dict]:
    ranked = []
    for article in articles:
        if any(term in article_text(article) for term in LOW_VALUE):
            continue
        article = enrich(article)
        article["importance_score"], article["score_breakdown"] = score_article(article)
        score = article["importance_score"]
        article["severity"] = "Critical" if score >= 55 else "High" if score >= 32 else "Medium" if score >= 14 else "Low"
        ranked.append(article)
    return sorted(ranked, key=lambda item: (item["importance_score"], item.get("published_at") or ""), reverse=True)
