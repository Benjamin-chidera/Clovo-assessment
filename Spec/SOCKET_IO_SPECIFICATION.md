# Clovo Real-Time Socket.IO Architecture & Connection Specification

## 1. Overview & Goal
This specification defines the bidirectional, event-driven real-time communication channel between the **Clovo Mobile Client (Expo / React Native)** and the **Clovo Backend Server (FastAPI + Async Python Socket.IO)**.

### Core Objectives:
1. **Authentication-Driven Lifecycle**: The Socket.IO connection automatically initiates immediately upon user login (`isAuthenticated: true`) and terminates gracefully upon logout (`isAuthenticated: false`).
2. **Real-Time Coaching & Check-ins**: Enables instant streaming and event-based message exchange between user and Coach Amy, activity card actions, and task synchronizations.
3. **Resilience & Reconnection**: Handles automatic reconnection, connection state indicators (`connected`, `connecting`, `disconnected`), and offline buffering.

---

## 2. System Architecture & Lifecycle Matrix

```
┌────────────────────────────────────────────────────────┐
│                   Mobile Client (Expo)                 │
│                                                        │
│   useAuthStore.login() ──► useSocketStore.connect()    │
│   useAuthStore.logout() ──► useSocketStore.disconnect()│
└──────────────────────────┬─────────────────────────────┘
                           │
             WebSocket / HTTP Long-Polling
             Socket.IO v4 Protocol
                           │
┌──────────────────────────▼─────────────────────────────┐
│                  FastAPI Backend Server                │
│                                                        │
│   python-socketio AsyncServer (ASGI Mounted)           │
│   ├── auth & room management (user_{user_id})          │
│   ├── message routing & Coach Amy AI pipeline          │
│   └── task & streak state broadcasts                   │
└────────────────────────────────────────────────────────┘
```

### 2.1 Connection Lifecycle

| Trigger Event | Client Action | Server Action |
| :--- | :--- | :--- |
| **User Logs In** (`login()`) | Initializes `io(SERVER_URL, { auth: { userId, token } })` | Validates auth token/payload, assigns session to room `user_{userId}`, emits `session_ready` |
| **Connection Established** | Updates state to `connected: true`, syncs latest coaching thread | Emits pending updates or initial coach greeting |
| **User Sends Message** | Emits `send_message` payload | Processes message, streams response back via `coach_message` |
| **User Selects Activity** | Emits `select_activity` payload | Updates recovery plan and confirms via `activity_confirmed` |
| **User Logs Out** (`logout()`) | Calls `socket.disconnect()`, resets socket state | Server triggers `disconnect` event and leaves user room |

---

## 3. Server Architecture (FastAPI + Python Socket.IO)

### 3.1 Dependencies (`requirements.txt` / `pyproject.toml`)
```text
fastapi[standard]
python-socketio>=5.11.0
uvicorn[standard]>=0.30.0
sqlmodel
langchain
langgraph
```

### 3.2 ASGI Mounting Pattern
FastAPI and `socketio.AsyncServer` are combined using `socketio.ASGIApp`:

```python
import socketio
from fastapi import FastAPI

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=False
)

app = FastAPI(title="Clovo Backend API")
socket_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)
```

### 3.3 Server Event Handlers

| Event | Direction | Payload | Description |
| :--- | :--- | :--- | :--- |
| `connect` | Client ➔ Server | `auth: { userId: str, token?: str }` | Authenticates client connection and joins room `user_{userId}` |
| `disconnect` | Client ➔ Server | `None` | Cleans up connection session |
| `send_message` | Client ➔ Server | `{ text: str, timestamp: str }` | User sent a chat message to Coach Amy |
| `coach_message` | Server ➔ Client | `{ id: str, text: str, timestamp: str, options?: ActivityCard[] }` | Real-time response from Coach Amy |
| `select_activity`| Client ➔ Server | `{ activityId: str, title: str }` | User selected a recovery activity card |
| `task_toggle` | Client ➔ Server | `{ taskId: str, isCompleted: bool }`| Synchronizes daily task progress |

---

## 4. Client Architecture (React Native / Expo)

### 4.1 Dependency
- `socket.io-client` (`^4.8.1`)

### 4.2 State Store (`useSocketStore.ts`) & Service
A dedicated Zustand store manages socket connection status and exposes send/receive actions:

```typescript
export interface SocketState {
  isConnected: boolean;
  isConnecting: boolean;
  socketId: string | null;
  connect: (userId: string) => void;
  disconnect: () => void;
  sendMessage: (text: string) => void;
  selectActivity: (activityId: string, title: string) => void;
}
```

### 4.3 Integration with `useAuthStore`
- When `useAuthStore.getState().login()` executes:
  - Invokes `useSocketStore.getState().connect(user.id)`.
- When `useAuthStore.getState().logout()` executes:
  - Invokes `useSocketStore.getState().disconnect()`.

---

## 5. Security & Reliability Guidelines

1. **Authentication Handshake**: Connection requests must supply `auth: { userId, token }` during the initial Socket.IO handshake. Unauthenticated connections are rejected with `ConnectionRefusedError`.
2. **Per-User Isolation**: Socket connections join private rooms (`user_{userId}`) to guarantee message privacy.
3. **CORS Configuration**: Restrict allowed origins to mobile app schemes (`mobile://*`, `http://localhost:*`, etc.).
4. **Graceful Degradation**: If socket connection drops, client automatically attempts reconnection with exponential backoff while queuing outgoing messages.

---

## 6. Implementation Checklist

- [ ] **Update Server Dependencies**: Add `python-socketio` to `Server/requirements.txt` and `Server/pyproject.toml`.
- [ ] **Implement FastAPI Socket.IO Server (`Server/main.py`)**: Create `AsyncServer`, configure CORS, connect/disconnect handlers, message routers, and mount as ASGI.
- [ ] **Install Client Dependency**: Install `socket.io-client` in `Client/mobile`.
- [ ] **Create Client Socket Service & Store (`useSocketStore.ts`)**: Implement connection lifecycle and event listeners.
- [ ] **Wire Login/Logout Triggers**: Connect socket initialization to `useAuthStore.login()` and teardown to `useAuthStore.logout()`.
- [ ] **Connect Chat Store to Real-Time Events**: Link `useChatStore` message dispatching and reception with Socket.IO events.
