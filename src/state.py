import json
from pathlib import Path
from datetime import datetime, timezone


def load_state(path):

    file = Path(path)

    if not file.exists():

        return {
            "seen_links": [],
            "last_digest": None
        }

    with open(file,"r",encoding="utf-8") as f:
        return json.load(f)



def save_state(path,state):

    Path(path).parent.mkdir(
        exist_ok=True
    )

    state["last_digest"] = (
        datetime.now(timezone.utc)
        .isoformat()
    )


    with open(path,"w",encoding="utf-8") as f:
        json.dump(
            state,
            f,
            indent=2
        )
