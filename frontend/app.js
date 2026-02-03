const roomInput = document.getElementById('room');
const agentInput = document.getElementById('agent');
const kindSelect = document.getElementById('kind');
const contentInput = document.getElementById('content');
const sendButton = document.getElementById('send');
const messagesEl = document.getElementById('messages');
const statusEl = document.getElementById('ws-status');
const roomLabel = document.getElementById('room-label');
const reconnectButton = document.getElementById('reconnect');

const seenIds = new Set();
let socket = null;

function loadSetting(key, fallback) {
  const value = window.localStorage.getItem(key);
  return value || fallback;
}

function saveSetting(key, value) {
  window.localStorage.setItem(key, value);
}

roomInput.value = loadSetting('room', 'default');
agentInput.value = loadSetting('agent', 'codex');

function setStatus(text, tone) {
  statusEl.textContent = text;
  statusEl.style.color = tone === 'bad' ? '#c85c3c' : '#1f6f78';
  statusEl.style.background =
    tone === 'bad' ? 'rgba(200, 92, 60, 0.15)' : 'rgba(31, 111, 120, 0.12)';
}

function formatTime(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleTimeString();
}

function renderMessages(messages, reset) {
  if (reset) {
    messagesEl.innerHTML = '';
    seenIds.clear();
  }
  messages.forEach((msg) => appendMessage(msg));
}

function appendMessage(msg) {
  if (msg.id && seenIds.has(msg.id)) {
    return;
  }
  if (msg.id) {
    seenIds.add(msg.id);
  }

  const card = document.createElement('div');
  card.className = 'message';
  card.dataset.kind = msg.kind || 'status';

  const header = document.createElement('div');
  header.className = 'message-header';

  const agent = document.createElement('div');
  agent.className = 'message-agent';
  agent.textContent = msg.agent || 'unknown';

  const meta = document.createElement('div');
  meta.className = 'message-meta';
  meta.textContent = `${msg.kind || 'status'} · ${formatTime(msg.ts || '')}`;

  header.appendChild(agent);
  header.appendChild(meta);

  const body = document.createElement('div');
  body.className = 'message-body';
  body.textContent = msg.content || '';

  card.appendChild(header);
  card.appendChild(body);

  messagesEl.appendChild(card);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function buildWsUrl(room) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.host;
  const params = new URLSearchParams({ room });
  return `${protocol}://${host}/ws?${params.toString()}`;
}

function connect() {
  const room = roomInput.value.trim() || 'default';
  roomLabel.textContent = room;
  saveSetting('room', room);

  if (socket) {
    socket.close();
  }

  setStatus('Connecting…');
  socket = new WebSocket(buildWsUrl(room));

  socket.addEventListener('open', () => {
    setStatus('Live');
  });

  socket.addEventListener('message', (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.type === 'history') {
        renderMessages(payload.data || [], true);
        return;
      }
      if (payload.type === 'message') {
        appendMessage(payload.data || payload);
      }
    } catch (err) {
      console.error('Bad message', err);
    }
  });

  socket.addEventListener('close', () => {
    setStatus('Disconnected', 'bad');
  });

  socket.addEventListener('error', () => {
    setStatus('Error', 'bad');
  });
}

async function sendMessage() {
  const room = roomInput.value.trim() || 'default';
  const agent = agentInput.value.trim();
  const kind = kindSelect.value;
  const content = contentInput.value.trim();

  if (!agent || !content) {
    return;
  }

  saveSetting('agent', agent);
  saveSetting('room', room);

  const response = await fetch('/api/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room, agent, kind, content }),
  });

  if (response.ok) {
    contentInput.value = '';
  } else {
    setStatus('Send failed', 'bad');
  }
}

sendButton.addEventListener('click', () => {
  sendMessage();
});

contentInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    sendMessage();
  }
});

roomInput.addEventListener('change', connect);
reconnectButton.addEventListener('click', connect);

connect();
