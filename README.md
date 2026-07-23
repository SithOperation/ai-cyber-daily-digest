# AI & Cyber Intelligence Digest

A standalone, automated cybersecurity and artificial-intelligence news briefing for a portfolio website. It collects trusted RSS feeds, rejects stale and low-value items, normalizes and deduplicates reporting, extracts verifiable security evidence, applies a transparent importance score, and publishes validated JSON and Markdown.

This repository is independent. It does not read, write, import, link to, or share state and scoring with Sentinel Grid Intelligence.

## What it produces

- `data/ai_cyber_digest.json` — validated website data, ranked by importance
- `data/ai_cyber_digest_state.json` — bounded history of previously published URLs
- `output/latest_digest.md` — human-readable daily briefing
- `index.html`, `styles.css`, `app.js` — standalone, responsive digest interface

Every story uses a stable normalized structure. Unknown enrichment is represented by an empty array, `null`, or `false`; the pipeline does not infer vendors, products, patch status, CVSS, KEV status, or MITRE ATT&CK mappings without explicit evidence in source metadata.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/main.py
python -m http.server 8000
```

Open `http://localhost:8000`. A web server is required because browsers do not allow the page to fetch local JSON reliably from a `file://` URL.

To validate the current artifact without collecting feeds:

```bash
python src/main.py --validate-only
```

## Collection and reliability

Each feed has an independent timeout and failure boundary. Logs identify feeds that succeeded, failed, or returned no new stories. Dates are normalized to ISO 8601 UTC, source URLs are restricted to HTTP(S), feed HTML is reduced to bounded plain text, and the UI inserts untrusted values through `textContent`.

The publisher validates required fields, severity, IDs, dates, URLs, and non-empty output before atomically replacing the public files. If every source fails or nothing new is collected, the last known good digest remains untouched.

## Transparent scoring

The adjustable signals live in `src/ranker.py`. Current weights include:

| Signal | Points |
|---|---:|
| Active exploitation | 25 |
| CISA KEV evidence | 20 |
| Zero-day | 18 |
| Critical CVSS (9.0+) | 18 |
| High CVSS (7.0–8.9) | 10 |
| Critical infrastructure impact | 12 |
| Nation-state or ransomware activity | 12 |
| Major data exposure | 10 |
| Government advisory or AI security relevance | 8 |
| Patch available or CVE cited | 4 |

Severity thresholds are Critical (55+), High (32–54), Medium (14–31), and Low (0–13). The JSON records the contributing signals in `score_breakdown`.

## Automation

`.github/workflows/ai-cyber-digest.yml` runs at approximately 9:00 AM in `America/New_York`, including daylight-saving changes. It installs pinned dependencies, tests, generates, validates, and commits only when staged artifacts actually changed. No credentials are hardcoded or required.
