import argparse
import asyncio
import json
import sys
import urllib.parse
import urllib.request

import websockets


def normalize_base(url: str) -> str:
    return url.rstrip('/')


def build_ws_url(base: str, room: str) -> str:
    if base.startswith('https://'):
        ws_base = 'wss://' + base[len('https://') :]
    elif base.startswith('http://'):
        ws_base = 'ws://' + base[len('http://') :]
    else:
        ws_base = 'ws://' + base
    params = urllib.parse.urlencode({'room': room})
    return f"{ws_base}/ws?{params}"


def post_message(args: argparse.Namespace) -> int:
    url = f"{normalize_base(args.server)}/api/messages"
    payload = {
        'room': args.room,
        'agent': args.agent,
        'kind': args.kind,
        'content': args.content,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, data=data, headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            print(body)
            return 0
    except Exception as exc:
        print(f"post failed: {exc}", file=sys.stderr)
        return 1


def format_line(msg: dict) -> str:
    ts = msg.get('ts', '')
    room = msg.get('room', '')
    agent = msg.get('agent', '')
    kind = msg.get('kind', '')
    content = msg.get('content', '')
    return f"[{ts}] ({room}) {agent} {kind}: {content}"


async def watch_messages(args: argparse.Namespace) -> int:
    ws_url = build_ws_url(normalize_base(args.server), args.room)
    try:
        async with websockets.connect(ws_url) as ws:
            async for raw in ws:
                payload = json.loads(raw)
                if payload.get('type') == 'history':
                    for msg in payload.get('data', []):
                        print(format_line(msg))
                    continue
                if payload.get('type') == 'message':
                    msg = payload.get('data', {})
                else:
                    msg = payload
                print(format_line(msg))
    except Exception as exc:
        print(f"watch failed: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Multi-agent chat hub CLI')
    parser.add_argument('--server', default='http://127.0.0.1:8000')

    subparsers = parser.add_subparsers(dest='command', required=True)

    post_parser = subparsers.add_parser('post', help='post a message')
    post_parser.add_argument('--room', default='default')
    post_parser.add_argument('--agent', required=True)
    post_parser.add_argument('--kind', default='status')
    post_parser.add_argument('content')

    watch_parser = subparsers.add_parser('watch', help='watch live messages')
    watch_parser.add_argument('--room', default='default')

    args = parser.parse_args()

    if args.command == 'post':
        return post_message(args)
    if args.command == 'watch':
        return asyncio.run(watch_messages(args))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
