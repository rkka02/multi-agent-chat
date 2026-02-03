import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_SERVER = "http://127.0.0.1:8000"
DEFAULT_ROOM = "default"


def normalize_base(url: str) -> str:
    return url.rstrip("/")


def health_url(server: str) -> str:
    return f"{normalize_base(server)}/health"


def check_health(server: str, *, timeout: float) -> tuple[bool, str]:
    url = health_url(server)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return False, str(exc)
    try:
        payload = json.loads(body)
    except Exception:
        payload = {}
    if isinstance(payload, dict) and payload.get("ok") is True:
        return True, "ok"
    return False, body.strip() or "unexpected response"


def default_config_path() -> Path:
    configured = os.environ.get("AGENTCHAT_CONFIG")
    if configured:
        return Path(configured)
    return Path.home() / ".agentchat.json"


def save_agent_to_config(path: Path, agent: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"agent": agent}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_python(repo_root: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env_python = os.environ.get("AGENTCHAT_PYTHON")
    if env_python:
        return Path(env_python)
    if os.name == "nt":
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def parse_host_port(server: str) -> tuple[str, int]:
    base = server if "://" in server else f"http://{server}"
    parsed = urllib.parse.urlparse(base)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000
    return host, int(port)


def start_server(repo_root: Path, python_exe: Path, server: str, *, new_console: bool) -> subprocess.Popen:
    host, port = parse_host_port(server)
    cmd = [
        str(python_exe),
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_CONSOLE if new_console else 0
        return subprocess.Popen(cmd, cwd=repo_root, env=os.environ.copy(), creationflags=flags)
    return subprocess.Popen(cmd, cwd=repo_root, env=os.environ.copy(), start_new_session=new_console)


def wait_for_health(server: str, *, total_timeout: float, interval: float) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < total_timeout:
        ok, _ = check_health(server, timeout=0.8)
        if ok:
            return True
        time.sleep(interval)
    return False


def spawn_watch(repo_root: Path, python_exe: Path, server: str, room: str, mode: str) -> int:
    cmd = [str(python_exe), "scripts/agent_cli.py", "--server", server, "watch", "--room", room]
    if mode == "inline":
        return subprocess.call(cmd, cwd=repo_root, env=os.environ.copy())
    if mode == "console":
        if os.name == "nt":
            subprocess.Popen(cmd, cwd=repo_root, env=os.environ.copy(), creationflags=subprocess.CREATE_NEW_CONSOLE)
            return 0
        subprocess.Popen(cmd, cwd=repo_root, env=os.environ.copy(), start_new_session=True)
        return 0
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap agent dev session with live watch")
    parser.add_argument("--agent", help="Persist default agent name to config (~/.agentchat.json)")
    parser.add_argument("--server", default=os.environ.get("AGENTCHAT_SERVER", DEFAULT_SERVER))
    parser.add_argument("--room", default=os.environ.get("AGENTCHAT_ROOM", DEFAULT_ROOM))
    parser.add_argument(
        "--watch-mode",
        default="console",
        choices=("console", "inline", "none"),
        help="Where to run the watch stream (default: console)",
    )
    parser.add_argument(
        "--server-mode",
        default="auto",
        choices=("auto", "start", "skip"),
        help="Start server if needed: auto | start | skip (default: auto)",
    )
    parser.add_argument("--check", action="store_true", help="Health check only; do not start watch")
    parser.add_argument("--python", dest="python_path", default=None, help="Override python executable path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]

    if args.agent:
        agent_name = args.agent.strip()
        if not agent_name:
            print("agent name is required when using --agent", file=sys.stderr)
            return 2
        config_path = default_config_path()
        save_agent_to_config(config_path, agent_name)
        print(f"saved agent={agent_name} to {config_path}")

    server = args.server

    ok, detail = check_health(server, timeout=0.8)
    if args.check:
        status = "ok" if ok else "down"
        print(f"server: {server} ({status})")
        if not ok:
            print(f"detail: {detail}")
            return 1
        return 0

    server_ok = ok
    if args.server_mode in {"auto", "start"}:
        if args.server_mode == "start" or not server_ok:
            python_exe = resolve_python(repo_root, args.python_path)
            if not python_exe.exists():
                print(f"python not found: {python_exe}", file=sys.stderr)
                return 2
            print("server: starting...")
            start_server(repo_root, python_exe, server, new_console=True)
            server_ok = wait_for_health(server, total_timeout=8.0, interval=0.5)
            if not server_ok:
                print("server: failed to become healthy within timeout")
        else:
            print("server: already running")

    if args.watch_mode != "none":
        if not server_ok and args.server_mode != "skip":
            print("watch: skipped because server is not healthy")
        else:
            python_exe = resolve_python(repo_root, args.python_path)
            if not python_exe.exists():
                print(f"python not found: {python_exe}", file=sys.stderr)
                return 2
            print(f"watch: starting ({args.watch_mode})")
            return spawn_watch(repo_root, python_exe, server, args.room, args.watch_mode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
