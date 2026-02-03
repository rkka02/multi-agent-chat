# Multi-Agent Chat Hub

Local coordination hub for running multiple CLI coding agents on one machine. Agents post status updates to an HTTP endpoint and receive live updates via WebSocket. A small web UI lets you monitor everything in real time. Messages persist in a local SQLite database.

## Quick Start

1. Create a virtual environment and install dependencies.

   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Start the server.

   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. Open the UI.

   - http://127.0.0.1:8000/

4. Post a message from a terminal.

   ```bash
   curl -X POST http://127.0.0.1:8000/api/messages -H "Content-Type: application/json" -d "{\"agent\":\"codex\",\"kind\":\"status\",\"content\":\"hello\",\"room\":\"default\"}"
   ```

## CLI Helper

Use the bundled CLI to post or watch messages.

```bash
python scripts/agent_cli.py post --agent codex --kind status "starting work on feature-x"
python scripts/agent_cli.py watch --room default
```

## Configuration

- `AGENTCHAT_DB`: override the SQLite path (default: `data/agent_chat.sqlite3`).
- `AGENTCHAT_HISTORY_LIMIT`: max messages sent on WebSocket connect (default: 200).

## Tests

```bash
pytest
```
