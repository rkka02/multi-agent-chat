# Build a Local Multi-Agent Work Chat Hub

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

The repository root contains `PLANS.md`. This document must be maintained in accordance with the requirements in `PLANS.md`.

## Purpose / Big Picture

After this change, a user can run a local web hub that lets multiple CLI coding agents post status updates and read each other’s messages in real time. The hub persists messages in a local SQLite database, provides a WebSocket feed for live updates, and serves a small web UI so the user can monitor progress in the browser. A newcomer can verify the system by starting the server, opening the web UI, posting a message via HTTP, and seeing it appear live in the UI.

## Progress

- [x] (2026-02-04T04:15:34+09:00) Read `PLANS.md` and drafted the initial ExecPlan.
- [x] (2026-02-04T04:21:37+09:00) Implemented the FastAPI server, SQLite persistence, and WebSocket broadcast.
- [x] (2026-02-04T04:21:37+09:00) Built the web UI and CLI helper for agents.
- [x] (2026-02-04T04:21:37+09:00) Added README guidance, a basic API test, and validated with `pytest`.
- [x] (2026-02-04T04:25:03+09:00) Added `AGENTS.md` usage instructions for autonomous agents.

## Surprises & Discoveries

- Observation: `pytest` could not import the `app` package until the repo root was added to the Python path.
  Evidence: `ModuleNotFoundError: No module named 'app'` during collection, resolved by adding `pytest.ini` with `pythonpath = .`.

- Observation: Installing the pinned dependencies downgraded preinstalled packages and produced a pip conflict warning.
  Evidence: pip reported `supabase 2.3.4 requires httpx<0.26,>=0.24, but you have httpx 0.28.1 which is incompatible.`

## Decision Log

- Decision: Use FastAPI with WebSocket support and a simple SQLite database for persistence.
  Rationale: FastAPI is productive for HTTP and WebSocket endpoints, and SQLite is sufficient for a single-machine hub with low operational overhead.
  Date/Author: 2026-02-04T04:15:34+09:00 (Codex)

- Decision: Provide a minimal browser UI plus HTTP endpoints, with WebSocket updates for real-time viewing.
  Rationale: The UI satisfies the user’s monitoring needs while HTTP endpoints keep it easy for CLI agents to post updates without extra integration work.
  Date/Author: 2026-02-04T04:15:34+09:00 (Codex)

- Decision: Use a FastAPI lifespan handler to initialize the database instead of deprecated `on_event` hooks.
  Rationale: This avoids deprecation warnings and keeps startup behavior explicit and future-proof.
  Date/Author: 2026-02-04T04:21:37+09:00 (Codex)

- Decision: Add `pytest.ini` to set `pythonpath = .` so tests can import `app` without installing the package.
  Rationale: Keeps tests lightweight and makes the repo runnable without packaging steps.
  Date/Author: 2026-02-04T04:21:37+09:00 (Codex)

- Decision: Provide a dedicated `AGENTS.md` quickstart so agent processes can self-serve.
  Rationale: The user explicitly requested agent-facing usage guidance; keeping it separate makes it easy to find and copy into agent prompts.
  Date/Author: 2026-02-04T04:25:03+09:00 (Codex)

## Outcomes & Retrospective

The local hub is implemented with a FastAPI server, SQLite persistence, a WebSocket broadcast channel, and a browser UI for monitoring. A CLI helper script enables agents to post or watch updates. Basic API tests pass. The agent-facing `AGENTS.md` quickstart is now available. The remaining work is optional polish, such as authentication or multi-room management UI, which was intentionally out of scope for the single-machine MVP.

## Context and Orientation

The repository now includes a Python application under `app/`, a frontend under `frontend/`, a CLI helper at `scripts/agent_cli.py`, tests under `tests/`, and configuration files (`requirements.txt`, `pytest.ini`, `README.md`, `AGENTS.md`). The server stores messages in `data/agent_chat.sqlite3` by default. The term “hub” refers to the HTTP/WebSocket server that collects messages. A “room” is a named channel used to group messages. A “message” is a structured record containing an agent name, a kind (such as status or blocker), and the text content.

## Plan of Work

Build a FastAPI application in `app/main.py` that wires together SQLite helpers from `app/db.py`, Pydantic schemas from `app/schema.py`, and a WebSocket connection manager from `app/realtime.py`. Serve the browser UI from `frontend/index.html` with static assets in the same folder. Provide a CLI helper in `scripts/agent_cli.py` for posting and watching updates. Document usage in `README.md` and `AGENTS.md` and add a small test in `tests/test_api.py` plus `pytest.ini` to make imports work without packaging.

## Concrete Steps

From the repository root, install dependencies, start the server, and open the UI. The following commands are the working, repeatable sequence:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m uvicorn app.main:app --reload

Open `http://127.0.0.1:8000/` in a browser. To post a message via HTTP, run:

    curl -X POST http://127.0.0.1:8000/api/messages -H "Content-Type: application/json" -d "{\"agent\":\"codex\",\"kind\":\"status\",\"content\":\"hello\",\"room\":\"default\"}"

To run the automated test:

    pytest

## Validation and Acceptance

Acceptance is achieved when starting the server and opening the browser UI shows a live feed that updates as new messages are posted. A POST to `/api/messages` should return JSON with an `id` and `ts`, and the message should appear in the UI without refreshing. `pytest` should report one passing test (`tests/test_api.py`).

## Idempotence and Recovery

Initialization creates tables only if they do not exist and reuses the same SQLite database on repeated runs. To reset the data, delete `data/agent_chat.sqlite3`; the server will recreate it on the next startup. The steps in this plan can be rerun without causing drift, aside from overwriting existing data if the database file is removed.

## Artifacts and Notes

Example validation output:

    ============================= test session starts =============================
    collected 1 item

    tests\test_api.py .                                                      [100%]

    ============================== 1 passed in 0.38s ===============================

## Interfaces and Dependencies

Use Python 3 with FastAPI and Uvicorn. Store messages in SQLite using the standard library `sqlite3` module. Provide the following modules and functions:

- `app.main` defines `create_app(db_path: pathlib.Path | None = None) -> fastapi.FastAPI` and a module-level `app = create_app()` for Uvicorn to import.
- `app.db` defines `init_db(db_path: pathlib.Path)`, `insert_message(db_path: pathlib.Path, message: dict) -> dict`, and `fetch_messages(db_path: pathlib.Path, room: str, limit: int, after_id: int | None) -> list[dict]`.
- `app.realtime` defines a `ConnectionManager` with `connect`, `disconnect`, and `broadcast` coroutine methods for WebSocket clients.
- `app.schema` defines Pydantic models `MessageIn` and `MessageOut`.
- `pytest.ini` sets `pythonpath = .` so tests can import the `app` package.

Plan update note (2026-02-04T04:25:03+09:00): Added `AGENTS.md` and updated progress, decision log, and outcomes to reflect the new usage guide.
