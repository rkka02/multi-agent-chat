from __future__ import annotations

from pathlib import Path

from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Query, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from app import db, settings
from app.realtime import ConnectionManager
from app.schema import MessageIn, MessageOut


def create_app(db_path: Path | None = None) -> FastAPI:
    base_dir = Path(__file__).resolve().parent.parent
    frontend_dir = base_dir / "frontend"
    static_dir = frontend_dir

    resolved_db = db_path or settings.get_db_path()
    history_limit = settings.get_history_limit()
    manager = ConnectionManager()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db.init_db(resolved_db)
        yield

    app = FastAPI(title="Multi-Agent Chat Hub", lifespan=lifespan)

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html", media_type="text/html")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/messages", response_model=list[MessageOut])
    async def get_messages(
        room: str = Query(default="default"),
        limit: int = Query(default=200, ge=1, le=1000),
        after_id: int | None = Query(default=None, ge=1),
    ) -> list[dict]:
        return await anyio.to_thread.run_sync(
            db.fetch_messages, resolved_db, room, limit, after_id
        )

    @app.post("/api/messages", response_model=MessageOut)
    async def post_message(message: MessageIn) -> dict:
        saved = await anyio.to_thread.run_sync(
            db.insert_message, resolved_db, message.model_dump()
        )
        await manager.broadcast(message.room, {"type": "message", "data": saved})
        return saved

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, room: str = "default") -> None:
        await manager.connect(room, websocket)
        try:
            history = await anyio.to_thread.run_sync(
                db.fetch_messages, resolved_db, room, history_limit, None
            )
            await websocket.send_json({"type": "history", "data": history})
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await manager.disconnect(room, websocket)

    return app


app = create_app()
