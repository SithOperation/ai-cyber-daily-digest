from pathlib import Path
import json
import os
import requests


from config import (
    RSS_FEEDS,
    MAX_ARTICLES,
    DIGEST_FILE,
    MARKDOWN_OUTPUT
)


from feeds import collect_articles


from ranker import rank_articles


from summarizer import build_digest


from state import (
    load_state,
    save_state,
    already_seen,
    add_seen
)



def send_discord(message):

    webhook = os.getenv(
        "DISCORD_WEBHOOK_URL"
    )


    if not webhook:

        print(
            "Discord webhook not configured"
        )

        return


    response = requests.post(

        webhook,

        json={
            "content": message[:1900]
        },

        timeout=10

    )


    print(
        f"Discord status: {response.status_code}"
    )



def save_json_digest(digest):

    path = Path(
        DIGEST_FILE
    )


    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(

        path,

        "w",

        encoding="utf-8"

    ) as file:


        json.dump(

            digest,

            file,

            indent=2,

            ensure_ascii=False

        )



def save_markdown(digest):


    path = Path(
        MARKDOWN_OUTPUT
    )


    path.parent.mkdir(

        parents=True,

        exist_ok=True

    )


    output = "# AI Cyber Daily Digest\n\n"


    output += (
        "Top cybersecurity and AI intelligence reports\n\n"
    )


    for index, story in enumerate(

        digest["stories"],

        start=1

    ):


        output += f"""

## {index}. {story['title']}


**Source:** {story['source']}


**Category:** {story['category']}


{story['summary']}


Read More:

{story['link']}


---

"""


    with open(

        path,

        "w",

        encoding="utf-8"

    ) as file:


        file.write(
            output
        )



def main():


    print(
        "Loading state..."
    )


    state = load_state()



    print(
        "Collecting articles..."
    )


    articles = collect_articles(

        RSS_FEEDS,

        state["seen_links"]

    )


    print(

        f"Collected {len(articles)} articles"

    )



    new_articles = []


    for article in articles:


        if not already_seen(

            article["link"],

            state

        ):


            new_articles.append(
                article
            )



    if not new_articles:


        print(
            "No new articles found"
        )


        save_state(
            state
        )


        return



    print(
        "Ranking articles..."
    )


    ranked_articles = rank_articles(

        new_articles

    )



    top_articles = ranked_articles[:MAX_ARTICLES]



    print(
        "Building digest..."
    )


    digest = build_digest(

        top_articles

    )



    print(
        "Saving JSON digest..."
    )


    save_json_digest(

        digest

    )



    print(
        "Saving markdown digest..."
    )


    save_markdown(

        digest

    )



    discord_message = (

        "🛡 AI Cyber Daily Digest\n\n"

    )


    for story in digest["stories"]:


        discord_message += (

            f"🔥 {story['title']}\n"

            f"{story['link']}\n\n"

        )



    send_discord(

        discord_message

    )



    for article in top_articles:


        add_seen(

            article["link"],

            state

        )



    save_state(

        state

    )



    print(
        "Digest complete"
    )



if __name__ == "__main__":

    main()
