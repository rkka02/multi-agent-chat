from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                room TEXT NOT NULL,
                agent TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_room_id ON messages(room, id);"
        )


def insert_message(db_path: Path, message: dict) -> dict:
    ts = message.get("ts") or datetime.now(timezone.utc).isoformat()
    room = message["room"]
    agent = message["agent"]
    kind = message["kind"]
    content = message["content"]
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO messages (ts, room, agent, kind, content) VALUES (?, ?, ?, ?, ?)",
            (ts, room, agent, kind, content),
        )
        msg_id = cur.lastrowid
    return {
        "id": msg_id,
        "ts": ts,
        "room": room,
        "agent": agent,
        "kind": kind,
        "content": content,
    }


def fetch_messages(
    db_path: Path, room: str, limit: int, after_id: int | None
) -> list[dict]:
    limit = max(1, min(limit, 1000))
    query = (
        "SELECT id, ts, room, agent, kind, content FROM messages WHERE room = ?"
    )
    params: list[object] = [room]
    if after_id is not None:
        query += " AND id > ?"
        params.append(after_id)
    query += " ORDER BY id ASC LIMIT ?"
    params.append(limit)
    with _connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]
