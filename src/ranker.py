KEYWORDS = [

    "critical",
    "zero-day",
    "zeroday",
    "ransomware",
    "breach",
    "exploit",
    "vulnerability",
    "CVE",
    "malware",
    "security",
    "attack",
    "incident",
    "hack",
    "AI security",
    "artificial intelligence"

]


def score_article(article):

    score = 0


    text = (

        article.get("title", "")
        +
        article.get("summary", "")

    ).lower()


    for keyword in KEYWORDS:

        if keyword.lower() in text:

            score += 5


    return score



def rank_articles(articles):


    for article in articles:

        article["score"] = score_article(
            article
        )


    articles.sort(

        key=lambda x: x["score"],

        reverse=True

    )


    return articles
