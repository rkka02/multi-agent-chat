from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB = Path("data") / "agent_chat.sqlite3"


def get_db_path() -> Path:
    """Return the SQLite path, honoring AGENTCHAT_DB when set."""
    raw = os.environ.get("AGENTCHAT_DB")
    return Path(raw) if raw else DEFAULT_DB


def get_history_limit() -> int:
    raw = os.environ.get("AGENTCHAT_HISTORY_LIMIT", "200")
    try:
        value = int(raw)
    except ValueError:
        return 200
    return max(1, min(value, 1000))
