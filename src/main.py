from config import (
    RSS_FEEDS,
    STATE_FILE,
    OUTPUT_FILE,
    MAX_ARTICLES
)

from feeds import collect_articles

from state import (
    load_state,
    save_state
)

from summarizer import (
    create_digest
)

from pathlib import Path



def main():

    print(
        "[+] Starting AI Cyber Digest"
    )


    state = load_state(
        STATE_FILE
    )


    seen=set(
        state["seen_links"]
    )


    articles = collect_articles(
        RSS_FEEDS,
        seen
    )


    if not articles:

        print(
            "No new intelligence found"
        )

        return


    articles = articles[
        :MAX_ARTICLES
    ]


    digest=create_digest(
        articles
    )


    Path(
        OUTPUT_FILE
    ).parent.mkdir(
        exist_ok=True
    )


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            digest
        )


    for article in articles:

        state["seen_links"].append(
            article["link"]
        )


    save_state(
        STATE_FILE,
        state
    )


    print(
        "[+] Digest complete"
    )



if __name__=="__main__":
    main()
