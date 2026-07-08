from feeds import collect_articles
from summarizer import summarize_articles
from state import load_state, save_state, already_seen, add_seen
import os
import requests


def send_discord(message):

    webhook = os.getenv(
        "DISCORD_WEBHOOK_URL"
    )

    if not webhook:
        return

    requests.post(
        webhook,
        json={
            "content": message
        }
    )


def main():

    state = load_state()

    articles = collect_articles()

    new_articles = []

    for article in articles:

        if not already_seen(
            article["link"],
            state
        ):
            new_articles.append(article)
            add_seen(
                article["link"],
                state
            )


    if new_articles:

        digest = summarize_articles(
            new_articles
        )

        send_discord(digest)


    save_state(state)


if __name__ == "__main__":
    main()
