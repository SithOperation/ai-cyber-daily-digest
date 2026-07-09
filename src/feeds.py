import feedparser

from config import MAX_ARTICLES



def collect_articles(feeds, seen):

    articles = []


    for url in feeds:


        print(
            f"Reading feed: {url}"
        )


        feed = feedparser.parse(
            url
        )


        source_name = feed.feed.get(
            "title",
            "Unknown"
        )


        for item in feed.entries:


            link = item.get(
                "link",
                ""
            )


            if not link:

                continue



            if link in seen:

                continue



            articles.append({

                "title":
                    item.get(
                        "title",
                        "Unknown"
                    ),


                "link":
                    link,


                "summary":
                    item.get(
                        "summary",
                        ""
                    ),


                "source":
                    source_name

            })



            # Collect more than we need.
            # Ranking happens later.

            if len(articles) >= MAX_ARTICLES * 5:

                break



        if len(articles) >= MAX_ARTICLES * 5:

            break



    return articles
