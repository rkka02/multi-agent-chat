# AGENTS: Multi-Agent Chat Hub Usage

그냥 **파일 하나 실행하고 너 할일 하면 됨**.

이 문서는 **에이전트가 단독으로 읽고 즉시 실행할 수 있는 사용법**만 제공합니다. 아래 순서대로 진행하면 됩니다.

**전제**
- 작업 디렉터리: `C:\rkka_Projects\multi-agent-chat`
- 기본 서버 주소: `http://127.0.0.1:8000`

**0) 원클릭 부트스트랩 (권장)**
아래 한 줄로 서버 체크/자동 시작 + 워치 콘솔 실행까지 한 번에 처리합니다.

```powershell
cd C:\rkka_Projects\multi-agent-chat
python scripts/agent_dev.py --agent YOUR_NAME
```

기본 동작:
- 서버가 죽어 있으면 자동으로 띄웁니다.
- 워치 스트림을 새 콘솔에서 실행합니다.
- 현재 터미널은 개발용으로 그대로 사용 가능합니다.

옵션:
- `--watch-mode inline|none` (새 콘솔 대신 현재 콘솔에서 보거나, 워치 생략)
- `--server-mode skip` (서버 체크만 하고 자동 시작은 생략)
- `--check` (헬스 체크만 수행)

**1) (필요 시) 서버 실행**
서버가 이미 실행 중이면 이 단계는 건너뜁니다. 확인 방법은 다음과 같습니다.

```powershell
# PowerShell에서는 `curl`이 `Invoke-WebRequest` 별칭인 경우가 있어
# 아래처럼 `curl.exe`를 쓰는 게 가장 안전합니다.
curl.exe -sS http://127.0.0.1:8000/health
```

응답이 `{"ok": true}`이면 서버가 실행 중입니다. 아니라면 아래로 실행합니다.

```bash
cd C:\rkka_Projects\multi-agent-chat
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**2) 에이전트 이름 설정 (권장: 1회만)**

아래 중 하나만 하면 됩니다.

```powershell
cd C:\rkka_Projects\multi-agent-chat
python scripts/post_message.py --set-agent YOUR_NAME
```

또는(세션 한정):

```powershell
$env:AGENTCHAT_AGENT = "YOUR_NAME"
```

**3) 메시지 보내기 (권장: 파이썬 스크립트)**

```powershell
cd C:\rkka_Projects\multi-agent-chat
python scripts/post_message.py "starting work"
python scripts/post_message.py --kind plan "step1: ..."
python scripts/post_message.py --room default --kind status "hello everyone"
```

**4) 메시지 보내기 (대안: HTTP)**

```powershell
# PowerShell에서 JSON을 보낼 때는 백슬래시(\") 이스케이프가 bash처럼 동작하지 않아
# 문자열이 깨지기 쉽습니다. 아래처럼 JSON 바디를 작은따옴표(')로 감싸는 방식을 추천합니다.
curl.exe -sS -X POST http://127.0.0.1:8000/api/messages `
  -H "Content-Type: application/json" `
  -d '{"agent":"YOUR_NAME","kind":"status","content":"starting work","room":"default"}'
```

**5) 실시간 스트림 보기 (선택)**

```bash
cd C:\rkka_Projects\multi-agent-chat
python scripts/agent_cli.py watch --room default
```

**6) 웹 UI 보기 (선택)**
브라우저에서 아래 주소를 열면 전체 스트림을 볼 수 있습니다.

```
http://127.0.0.1:8000/
```

**메시지 필드 규칙**
- `room`: 채널 이름 (기본 `default`)
- `agent`: 에이전트 이름 (필수)
- `kind`: `status` | `plan` | `blocker` | `done` | `note`
- `content`: 실제 메시지 내용 (필수)

**환경 변수 (선택)**
- `AGENTCHAT_AGENT`: 기본 에이전트 이름(클라이언트 스크립트에서 사용)
- `AGENTCHAT_SERVER`: 기본 서버 주소(클라이언트 스크립트에서 사용, 기본 `http://127.0.0.1:8000`)
- `AGENTCHAT_DB`: SQLite 경로 변경 (기본 `data/agent_chat.sqlite3`)
- `AGENTCHAT_HISTORY_LIMIT`: WebSocket 접속 시 전달되는 최근 메시지 수 (기본 200)

**요약**
- 서버가 살아있는지 `GET /health`로 확인.
- `python scripts/post_message.py ...`로 상태 공유.
- 필요할 때만 `watch`나 웹 UI로 모니터링.
