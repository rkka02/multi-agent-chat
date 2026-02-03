import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_SERVER = "http://127.0.0.1:8000"
DEFAULT_ROOM = "default"
DEFAULT_KIND = "status"


def normalize_base(url: str) -> str:
    return url.rstrip("/")


def default_config_path() -> Path:
    configured = os.environ.get("AGENTCHAT_CONFIG")
    if configured:
        return Path(configured)
    return Path.home() / ".agentchat.json"


def load_agent_from_config(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None
    agent = data.get("agent")
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def save_agent_to_config(path: Path, agent: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"agent": agent}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_agent(cli_agent: str | None, config_path: Path) -> str | None:
    if cli_agent and cli_agent.strip():
        return cli_agent.strip()
    env_agent = os.environ.get("AGENTCHAT_AGENT") or os.environ.get("AGENT_NAME")
    if env_agent and env_agent.strip():
        return env_agent.strip()
    return load_agent_from_config(config_path)


def post_message(server: str, payload: dict) -> int:
    url = f"{normalize_base(server)}/api/messages"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            print(body)
            return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"post failed: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a message to Multi-Agent Chat Hub")
    parser.add_argument("--server", default=os.environ.get("AGENTCHAT_SERVER", DEFAULT_SERVER))
    parser.add_argument("--room", default=os.environ.get("AGENTCHAT_ROOM", DEFAULT_ROOM))
    parser.add_argument("--kind", default=os.environ.get("AGENTCHAT_KIND", DEFAULT_KIND))
    parser.add_argument("--agent", help="agent name (overrides env/config)")
    parser.add_argument(
        "--set-agent",
        metavar="NAME",
        help="persist default agent name to ~/.agentchat.json (or $env:AGENTCHAT_CONFIG)",
    )
    parser.add_argument("content", nargs="*", help="message content (or read from stdin)")
    args = parser.parse_args()

    config_path = default_config_path()

    if args.set_agent:
        agent = args.set_agent.strip()
        if not agent:
            print("--set-agent requires a non-empty name", file=sys.stderr)
            return 2
        save_agent_to_config(config_path, agent)
        print(f"saved agent={agent} to {config_path}")
        return 0

    content = " ".join(args.content).strip()
    if not content:
        content = sys.stdin.read().strip()
    if not content:
        print("content is required (arg or stdin)", file=sys.stderr)
        return 2

    agent = resolve_agent(args.agent, config_path)
    if not agent:
        print(
            "agent name not set. Use --agent, set $env:AGENTCHAT_AGENT, or run with --set-agent NAME.",
            file=sys.stderr,
        )
        return 2

    payload = {"room": args.room, "agent": agent, "kind": args.kind, "content": content}
    return post_message(args.server, payload)


if __name__ == "__main__":
    raise SystemExit(main())

