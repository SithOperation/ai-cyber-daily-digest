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

        article.get(
            "title",
            ""
        )

        +

        article.get(
            "summary",
            ""
        )

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





def diversify_articles(articles, limit=5):


    selected = []

    sources = set()



    for article in articles:


        source = article.get(

            "source",

            "Unknown"

        )



        if source not in sources:


            selected.append(
                article
            )


            sources.add(
                source
            )



        if len(selected) >= limit:

            break



    return selected
