from datetime import datetime, timezone


def build_digest(articles):


    stories = []


    for article in articles:


        stories.append({

            "title":
                article["title"],


            "source":
                article["source"],


            "summary":
                article["summary"][:500],


            "link":
                article["link"],


            "category":
                determine_category(article),


            "score":
                article.get(
                    "score",
                    0
                )

        })


    return {

        "generated":

            datetime.now(
                timezone.utc
            ).isoformat(),


        "stories":

            stories

    }



def determine_category(article):


    text = (

        article["title"]

        +

        article["summary"]

    ).lower()


    if "ai" in text or "artificial intelligence" in text:

        return "Artificial Intelligence"


    return "Cybersecurity"
