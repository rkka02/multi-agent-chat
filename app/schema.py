from __future__ import annotations

from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    room: str = Field(default="default", min_length=1, max_length=64)
    agent: str = Field(min_length=1, max_length=64)
    kind: str = Field(default="status", min_length=1, max_length=32)
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(MessageIn):
    id: int
    ts: str
