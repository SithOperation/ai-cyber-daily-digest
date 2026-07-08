def summarize(article):

    title = article["title"]

    summary = article["summary"]


    return f"""
## {title}

**Source:** {article['source']}

{summary[:500]}

**Security Impact:**

Analyst review recommended.
Evaluate affected systems,
exposure,
and mitigation requirements.

Link:
{article['link']}

---
"""


def create_digest(articles):

    output = """
# AI Cyber Digest

Top 5 AI + Cybersecurity Intelligence Reports

"""


    for article in articles:

        output += summarize(
            article
        )


    return output
