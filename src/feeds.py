import feedparser


def collect_articles(feeds,seen):

    articles=[]


    for url in feeds:

        feed = feedparser.parse(url)


        for item in feed.entries:

            link=item.get(
                "link",
                ""
            )


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


    return articles
