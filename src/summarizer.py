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

                clean_summary(
                    article["summary"]
                ),



            "link":

                article["link"],



            "category":

                determine_category(
                    article
                ),



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





def clean_summary(text):


    if not text:

        return "No summary available."



    return (

        text

        .replace(
            "&nbsp;",
            " "
        )

        .replace(
            "&quot;",
            '"'
        )

        [:500]

    )





def determine_category(article):


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



    ai_terms = [

        "artificial intelligence",

        "ai ",

        "ai-",

        "machine learning",

        "llm",

        "large language model",

        "coding agent",

        "generative ai"

    ]



    if any(

        term in text

        for term in ai_terms

    ):


        return "Artificial Intelligence"



    return "Cybersecurity"
