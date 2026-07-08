from pathlib import Path
import os
import requests

from config import RSS_FEEDS, OUTPUT_FILE
from feeds import collect_articles
from summarizer import create_digest
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
        print("Discord webhook not configured")
        return

    max_length = 1900

    chunks = [
        message[i:i + max_length]
        for i in range(
            0,
            len(message),
            max_length
        )
    ]

    for index, chunk in enumerate(chunks):

        response = requests.post(
            webhook,
            json={
                "content": chunk
            },
            timeout=10
        )

        print(
            f"Discord chunk {index + 1}/{len(chunks)} status: {response.status_code}"
        )


def save_digest_file(digest):

    output_path = Path(
        OUTPUT_FILE
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(digest)


def main():

    print("Loading state...")

    state = load_state()


    print("Collecting articles...")

    articles = collect_articles(
        RSS_FEEDS,
        state["seen_links"]
    )


    print(
        f"Articles collected: {len(articles)}"
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

            add_seen(
                article["link"],
                state
            )


    print(
        f"New articles: {len(new_articles)}"
    )


    if new_articles:

        print("Creating digest...")

        digest = create_digest(
            new_articles
        )


        save_digest_file(
            digest
        )


        send_discord(
            digest
        )

    else:

        print(
            "No new articles found"
        )


    save_state(
        state
    )


    print(
        "Digest complete"
    )


if __name__ == "__main__":
    main()
