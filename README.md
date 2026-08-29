# Clovo — Personalized Wellness & Recovery Coaching Platform

**Clovo** is an AI-powered personalized wellness and surgical recovery coaching platform. It guides users through daily check-ins, recovery routines, milestone tracking, and conversational coaching with **Amy** (Recovery Coach).

---

## 🌟 Architecture & Features

### 1. Mobile Client (`Client/mobile`)
- **Framework**: React Native with **Expo SDK 57** and **Expo Router** (File-based navigation).
- **Styling**: **Tailwind CSS** (via NativeWind v4) with custom Clovo design tokens.
- **State Management**: **Zustand** stores for decoupled, modular global state (`useAuthStore`, `useUserStore`, `useChatStore`, `useTaskStore`).
- **Networking & Real-Time**: **Axios** for REST API communication and **`socket.io-client`** for bidirectional WebSocket events.
- **Screens & Flows**:
  - **Auth / Login (`/login`)**: Minimalist login flow that initiates session and real-time socket connections.
  - **Home Dashboard (`/(tabs)/index`)**: High-res lifestyle hero banner, greeting ("Good morning, Sarah"), milestone achievements stack (`+3`), streak badge pill (`🔥 5 day streak`), surgery countdown ("Your surgery · 21 days away"), primary "Check in with Amy" CTA, and interactive daily preparation checklist.
  - **Profile & Logout Pop-up**: Bottom sheet modal triggered from the hero banner's `swap-horizontal` button for profile switching and secure logout.
  - **Coach Chat (`/(tabs)/chat`)**: Interactive message thread with Coach Amy, rich recovery activity selection cards (*Gentle Stretching*, *Recovery Walk*, *Yoga for Beginners*, *Surprise Me! 🎁*), quick reply pills, and pill-shaped input bar.

### 2. Backend Server (`Server`)
- **Framework**: **FastAPI** with **SQLModel** (SQLite ORM) and **Python Socket.IO** (`AsyncServer` mounted via ASGI).
- **Package Management**: **`uv`** fast Python package manager.
- **Modular Routing Architecture**:
  - `Server/main.py`: Clean entry point containing exclusively `/health` and `/` endpoints.
  - `Server/routes/home.py`: Aggregated dashboard data endpoint (`GET /api/home`).
  - `Server/routes/users.py`: User profile endpoints (`GET /api/user`, `GET /api/users/me`, `GET /api/users/{user_id}`).
  - `Server/routes/tasks.py`: Daily preparation tasks and status toggle (`GET /api/tasks`, `PATCH /api/tasks/{task_id}/toggle`).
  - `Server/routes/patients.py`: Patient management and patient-specific recommendations.
  - `Server/routes/recommendations.py`: Recommendation status management.
  - `Server/routes/sockets.py`: Real-time Socket.IO event handlers (`connect`, `disconnect`, `send_message`, `select_activity`, `task_toggle`).

---

## 📁 Project Structure

```
Clovo/
├── Client/
│   ├── mobile/                    # React Native Expo Mobile App
│   │   ├── src/
│   │   │   ├── app/               # Expo Router file-based screens
│   │   │   │   ├── _layout.tsx    # Root layout & auth gating
│   │   │   │   ├── login.tsx      # Login screen
│   │   │   │   ├── index.tsx      # Home tab screen
│   │   │   │   └── chat.tsx       # Coach Amy chat tab screen
│   │   │   ├── components/        # Tailwind-styled components
│   │   │   │   ├── home/          # HeroBanner, GreetingBadges, ProfileModal, etc.
│   │   │   │   └── chat/          # CoachHeader, MessageBubble, RecoveryActivityCards, etc.
│   │   │   ├── stores/            # Zustand global state stores
│   │   │   ├── services/          # Socket.IO client service
│   │   │   └── constants/         # Theme tokens and colors
│   │   ├── tailwind.config.js     # NativeWind / Tailwind configuration
│   │   └── package.json
│   └── web/                       # Web client (Next.js)
├── Server/                        # FastAPI Backend
│   ├── routes/                    # Modular API route controllers
│   │   ├── home.py                # Home dashboard routes
│   │   ├── users.py               # User profile routes
│   │   ├── tasks.py               # Task management routes
│   │   ├── patients.py            # Patient routes
│   │   ├── recommendations.py     # Recommendations routes
│   │   ├── sockets.py             # Real-time Socket.IO event handlers
│   │   └── __init__.py            # Aggregated API router
│   ├── models/                    # SQLModel database schemas
│   ├── services/                  # Business logic & database operations
│   ├── database.py                # Database connection & session setup
│   ├── main.py                    # Root FastAPI & ASGI Socket.IO app
│   ├── pyproject.toml             # Python dependencies
│   └── requirements.txt
└── Spec/                          # Architectural & Design Specifications
    ├── UI_SPECIFICATION.md        # UI/UX, screen layouts, design tokens
    ├── AUTH_SPECIFICATION.md      # Auth lifecycle & profile modal spec
    └── SOCKET_IO_SPECIFICATION.md # Real-time Socket.IO data contracts & events
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js** (v18+) & **npm**
- **Python** (v3.12+) and **`uv`**
- **Expo Go** app or iOS Simulator / Android Emulator

---

### 2. Backend Setup (`Server`)

```bash
cd Server

# Install dependencies using uv
uv sync

# Run the FastAPI + Socket.IO server
uv run python main.py
```

- API Server: `http://localhost:8000`
- Interactive API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

### 3. Mobile Client Setup (`Client/mobile`)

```bash
cd Client/mobile

# Install dependencies
npm install

# Start the Expo development server
npm run start
```

- To open on iOS Simulator: Press **`i`** or run `npm run ios`.
- To open on Android Emulator: Press **`a`** or run `npm run android`.
- To open on Web Preview: Press **`w`** or run `npm run web`.

---

## 📖 Specifications
Refer to the [`Spec/`](./Spec/) directory for in-depth technical documents:
- [UI & UX Specification (`Spec/UI_SPECIFICATION.md`)](./Spec/UI_SPECIFICATION.md)
- [Authentication Specification (`Spec/AUTH_SPECIFICATION.md`)](./Spec/AUTH_SPECIFICATION.md)
- [Socket.IO Specification (`Spec/SOCKET_IO_SPECIFICATION.md`)](./Spec/SOCKET_IO_SPECIFICATION.md)

---

## 📌 Project Context
> **Note**: This project was developed as a **Technical Assessment** for an engineering interview, demonstrating full-stack engineering proficiency with React Native (Expo SDK 57, Tailwind/NativeWind, Zustand, Axios), FastAPI (Python 3.12, SQLModel/SQLite), and real-time bidirectional Socket.IO communication.

---

## 📄 License
This project is licensed under the MIT License.
