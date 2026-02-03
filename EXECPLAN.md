# Add one-command agent bootstrap and live watch helper

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

The repository root contains `PLANS.md`. This document must be maintained in accordance with the requirements in `PLANS.md`.

## Purpose / Big Picture

After this change, an agent can run a single script from `multi-agent-chat` and immediately have a live watch stream running in a separate terminal (or inline if desired) while keeping the current CLI free for development. The same script should optionally set the agent name once, check whether the server is already running, and start the server automatically if it is not. A newcomer can verify the behavior by running the script, seeing a new watch window with live chat output, and continuing to type in their original terminal without interruption.

## Progress

- [x] (2026-02-03T20:15Z) Read `PLANS.md` and rewrote the ExecPlan for the bootstrap/watch helper.
- [x] (2026-02-03T20:18Z) Implemented `scripts/agent_dev.py` with server bootstrap and watch modes.
- [x] (2026-02-03T20:18Z) Updated `AGENTS.md` and `README.md` with the one-command workflow.
- [x] (2026-02-03T20:19Z) Validated `python scripts/agent_dev.py --check` against the running server.

## Surprises & Discoveries

None yet.

## Decision Log

- Decision: Implement the helper as a new Python script under `scripts/` using only the standard library.
  Rationale: This matches the existing CLI helpers and keeps the workflow self-contained without introducing new dependencies.
  Date/Author: 2026-02-03 / Codex

- Decision: On Windows, open the watch stream in a new console by default and fall back to inline mode when requested.
  Rationale: The goal is to keep the current terminal free for development while still showing live chat updates.
  Date/Author: 2026-02-03 / Codex

- Decision: Prefer the project’s `.venv` Python if available, otherwise fall back to the current interpreter.
  Rationale: The watch and server dependencies are installed in the project venv in the normal setup path.
  Date/Author: 2026-02-03 / Codex

- Decision: Add a `--check` mode for safe validation without launching extra consoles.
  Rationale: It enables quick verification in automated or shared terminals without side effects.
  Date/Author: 2026-02-03 / Codex

## Outcomes & Retrospective

The repository now includes a single-command bootstrap helper that checks server health, starts the server if needed, and opens a live watch stream in a separate console by default. Documentation was updated to point agents to the new workflow. A health-check validation run succeeded. Remaining work is optional polish (for example, auto-venv bootstrap), which is out of scope for this change.

## Context and Orientation

The repository already contains a FastAPI server (`app/`) and two CLI helpers: `scripts/post_message.py` for posting messages and `scripts/agent_cli.py` for posting or watching via WebSocket. The server is expected to run on `http://127.0.0.1:8000` by default and exposes a `/health` endpoint. Agents currently need multiple manual steps to start the server, set their agent name, and run a watch stream. The new helper will bundle those steps into one command.

Terms used in this plan:

“Watch stream” refers to the long-running WebSocket listener provided by `scripts/agent_cli.py watch`, which prints messages as they arrive. “Bootstrap” refers to the sequence of checking server health and starting `uvicorn` if the server is not already running.

## Plan of Work

Add a new script `scripts/agent_dev.py` that provides a single entry point. The script will check server health via HTTP. If the server is down, it will start `uvicorn` using the project’s `.venv` Python when available and fall back to the current Python otherwise. The script will then launch the watch stream in a new console window on Windows, or inline when explicitly requested. It will optionally persist an agent name to the standard config file so that later `post_message.py` calls do not require `--agent`.

Update `AGENTS.md` and `README.md` to show the new single-command workflow, including the default behavior and how to select inline mode.

## Concrete Steps

From the repository root (`C:\rkka_Projects\multi-agent-chat`):

1) Add `scripts/agent_dev.py` with command-line flags for `--agent`, `--server`, `--room`, `--watch-mode`, `--server-mode`, and `--check`.
2) Document the helper in `AGENTS.md` and `README.md`.
3) Validate by running:

    python scripts/agent_dev.py --check

Then run:

    python scripts/agent_dev.py --agent DemoAgent

You should see a new console window running the watch stream while the original terminal remains free.

## Validation and Acceptance

Acceptance is achieved when:

1) `python scripts/agent_dev.py --check` reports server health without launching a watch stream.
2) `python scripts/agent_dev.py --agent DemoAgent` opens a separate watch console (Windows) and keeps the original terminal available for other commands.
3) If the server is not running, the helper starts it automatically and the watch stream connects successfully within a few seconds.

## Idempotence and Recovery

The helper is safe to run multiple times. If the server is already running, it does not start a second instance. The watch stream can be closed independently without affecting the server. If anything becomes inconsistent, stop the server process and rerun the helper; it will relaunch as needed.

## Artifacts and Notes

Example expected output for a health check:

    server: http://127.0.0.1:8000 (ok)

## Interfaces and Dependencies

The helper must use only the Python standard library and reuse existing scripts for watch behavior. The new public entry point is:

- `scripts/agent_dev.py` with a `main()` that can be invoked via `python scripts/agent_dev.py`.

Plan update note (2026-02-03): Replaced the prior completed plan with a new ExecPlan focused on the one-command agent bootstrap and watch helper.
Plan update note (2026-02-03): Marked implementation, docs, and validation steps complete and recorded additional decisions after the health-check validation.
