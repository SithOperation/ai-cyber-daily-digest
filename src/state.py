"""Persistent state with bounded history and corruption recovery."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from config import STATE_FILE

LOG = logging.getLogger(__name__)
MAX_SEEN_LINKS = 2000


def load_state() -> dict:
    default = {"seen_links": [], "last_digest": None}
    if not STATE_FILE.exists():
        return default
    try:
        value = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(value.get("seen_links"), list):
            raise ValueError("seen_links must be a list")
        return value
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        LOG.warning("Ignoring malformed state file: %s", exc)
        return default


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["seen_links"] = list(dict.fromkeys(state.get("seen_links", [])))[-MAX_SEEN_LINKS:]
    state["last_digest"] = datetime.now(timezone.utc).isoformat()
    temporary = STATE_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary.replace(STATE_FILE)
