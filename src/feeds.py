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
                    feed.feed.get(
                        "title",
                        "Unknown"
                    )

            })


            if len(articles) >= MAX_ARTICLES:

                return articles


    return articles
