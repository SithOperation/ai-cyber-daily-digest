import json
from pathlib import Path
from datetime import datetime, timezone


STATE_FILE = Path(
    "data/ai_cyber_digest_state.json"
)


def load_state():

    if not STATE_FILE.exists():

        return {
            "seen_links": [],
            "last_digest": None
        }


    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def save_state(state):

    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    state["last_digest"] = datetime.now(
        timezone.utc
    ).isoformat()


    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2
        )



def already_seen(url, state):

    return url in state.get(
        "seen_links",
        []
    )



def add_seen(url, state):

    if url not in state["seen_links"]:

        state["seen_links"].append(
            url
        )
