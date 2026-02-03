from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_messages(tmp_path):
    app = create_app(db_path=tmp_path / "test.sqlite3")
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"ok": True}

        payload = {
            "agent": "codex",
            "kind": "status",
            "content": "hello",
            "room": "default",
        }
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 200
        message = resp.json()
        assert message["id"] == 1
        assert message["agent"] == "codex"

        feed = client.get("/api/messages", params={"room": "default"})
        assert feed.status_code == 200
        messages = feed.json()
        assert len(messages) == 1
        assert messages[0]["content"] == "hello"
