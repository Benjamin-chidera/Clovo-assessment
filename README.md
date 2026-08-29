# Clovo — Personalized Wellness & Recovery Coaching Platform

**Clovo** is an AI-powered personalized wellness and surgical recovery coaching platform. It guides patients through daily check-ins, evidence-based recovery routines, milestone tracking, and clinically-governed conversational coaching with **Amy** (AI Recovery Coach).

---

## 🌟 Architecture & Key Features

### 1. Mobile Client (`Client/mobile`)
- **Framework**: React Native with **Expo SDK 57** and **Expo Router** (File-based navigation).
- **Styling**: **Tailwind CSS** (via NativeWind v4) with custom Clovo design tokens and palette.
- **State Management**: **Zustand** stores for decoupled, modular global state (`useAuthStore`, `useUserStore`, `useChatStore`, `useTaskStore`).
- **Networking & Real-Time**: **Axios** for REST API communication and **`socket.io-client`** for bidirectional WebSocket events.
- **Observability**: **Sentry React Native** for crash reporting and session monitoring.
- **Screens & Flows**:
  - **Auth / Login (`/login`)**: Minimalist login flow that initializes user session and establishes real-time socket connection.
  - **Home Dashboard (`/(tabs)/index`)**: Lifestyle hero banner, patient greeting ("Good morning, Sarah"), milestone achievements stack (`+3`), streak badge pill (`🔥 5 day streak`), surgery countdown ("Your surgery · 21 days away"), primary "Check in with Amy" CTA, and interactive daily preparation checklist.
  - **Profile & Logout Pop-up**: Bottom sheet modal triggered from the hero banner's `swap-horizontal` button for profile switching and secure logout.
  - **Coach Chat (`/(tabs)/chat`)**: Interactive message thread with Coach Amy, dynamic recovery activity cards (*Quad Sets*, *4-7-8 Breathing*, *Protein Power Snack*, *Surprise Me! 🎁*), contextual quick reply pills, and real-time typing indicators.

---

### 2. Backend Server (`Server`)
- **Framework**: **FastAPI** with **SQLModel** (SQLite ORM) and **Python Socket.IO** (`AsyncServer` mounted via ASGI).
- **AI Agent Engine**: **LangGraph** multi-node state machine with safety triage guardrails, clinical content grounding, and LLM inference.
- **Package Management**: **`uv`** fast Python package manager.
- **Observability**: **Sentry SDK** (`sentry-sdk[fastapi]`) monitoring endpoints, transactions, and Redis calls.
- **Caching & Real-Time Scaling**: **Redis** cache-aside service and Socket.IO `AsyncRedisManager`.
- **Modular Routing Architecture**:
  - `Server/main.py`: Clean entry point containing exclusively `/health` and `/` endpoints.
  - `Server/routes/home.py`: Aggregated dashboard data endpoint (`GET /api/home`).
  - `Server/routes/users.py`: User profile endpoints (`GET /api/user`, `GET /api/users/me`, `GET /api/users/{user_id}`).
  - `Server/routes/tasks.py`: Daily preparation tasks and status toggle (`GET /api/tasks`, `PATCH /api/tasks/{task_id}/toggle`).
  - `Server/routes/patients.py`: Patient management and patient-specific recommendations (`GET /api/patients`, `GET /api/patients/{id}/home`, `GET /api/patients/{id}/recommendations`).
  - `Server/routes/recommendations.py`: Recommendation status toggle (`PATCH /api/recommendations/{id}/toggle`).
  - `Server/routes/conversations.py`: Chat history and message endpoints (`GET /api/conversations/messages`, `POST /api/conversations/messages`).
  - `Server/routes/sockets.py`: Real-time Socket.IO event handlers (`connect`, `disconnect`, `send_message`, `select_activity`, `task_toggle`).

---

### 3. Clinical Content & Recommendation Architecture
The platform strictly decouples content definition from patient prescriptions:
- **`ClinicalContent` ("The What")**: Curated, evidence-based exercises (*Quad Sets*, *Straight Leg Raise*), nutrition protocols (*Protein Power Snack*), and mindfulness practices (*4-7-8 Breathing*) with clinical rationales, target stages (`pre-op-21`, `pre-op-14`, `pre-op-all`), and rich media.
- **`Recommendation` ("The How Much & When")**: Personalized patient assignments linking a patient to clinical content with custom durations (`duration_minutes`), repetitions, scheduled dates, and progress status (`active`, `completed`, `skipped`).

---

### 4. AI Coach Amy & UK Clinical Governance
- **UK MHRA & NHS Alignment**: Operating as a supportive healthcare guidance tool adhering to DCB0129 / DCB0160 clinical safety principles. Clinicians retain 100% authority over diagnoses and treatment.
- **Hard Guardrails**: Amy never diagnoses medical conditions, never alters dosages/durations, and never invents unapproved exercises.
- **Safety Triage & Escalation**: Identifies pain, dizziness, or clinical red flags, immediately pauses unsafe exercises, creates formal `SafetyEvent` records in SQLite, and directs patients to clinical care teams / NHS 111 / 999.

---

### 5. DevOps & Infrastructure
- **Docker Multi-Stage Build**: `Server/Dockerfile` with non-root security (`appuser`) and container health checks.
- **Container Orchestration**: `docker-compose.yml` orchestrating `clovo-server` and `clovo-redis`.
- **CI/CD Pipelines**:
  - `.github/workflows/ci.yml`: Automated backend validation (`uv sync`, route tests, Docker build) and mobile typecheck (`tsc --noEmit`).
  - `.github/workflows/deploy.yml`: Automated container image build and publishing to GitHub Container Registry (GHCR).

---

## 📁 Project Structure

```
Clovo/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Backend & Mobile CI Pipeline
│       └── deploy.yml             # Docker Container Publishing CD Pipeline
├── Client/
│   ├── mobile/                    # React Native Expo Mobile App
│   │   ├── src/
│   │   │   ├── app/               # Expo Router file-based screens
│   │   │   │   ├── _layout.tsx    # Root layout, Sentry & auth gating
│   │   │   │   ├── login.tsx      # Login screen
│   │   │   │   ├── index.tsx      # Home tab dashboard
│   │   │   │   └── chat.tsx       # Coach Amy chat screen
│   │   │   ├── components/        # Tailwind-styled components
│   │   │   │   ├── home/          # HeroBanner, GreetingBadges, ProfileModal, etc.
│   │   │   │   └── chat/          # CoachHeader, MessageBubble, RecoveryActivityCards, etc.
│   │   │   ├── stores/            # Zustand global state stores
│   │   │   ├── services/          # Socket.IO & Axios API client services
│   │   │   └── constants/         # Theme tokens and ClovoColors
│   │   ├── tailwind.config.js     # NativeWind / Tailwind configuration
│   │   └── package.json
│   └── web/                       # Web client
├── Server/                        # FastAPI Backend
│   ├── routes/                    # Modular API route controllers
│   │   ├── home.py                # Home dashboard routes
│   │   ├── users.py               # User profile routes
│   │   ├── tasks.py               # Task management routes
│   │   ├── patients.py            # Patient routes
│   │   ├── recommendations.py     # Recommendations routes
│   │   ├── conversations.py       # Chat conversation endpoints
│   │   ├── sockets.py             # Real-time Socket.IO event handlers
│   │   └── __init__.py            # Aggregated API router
│   ├── models/                    # SQLModel schemas (ClinicalContent, Recommendation, Patient, etc.)
│   ├── services/                  # Business logic (coach_service, safety_service, redis_service, etc.)
│   ├── database.py                # Database connection, tables, and content seeding
│   ├── main.py                    # Root FastAPI & ASGI Socket.IO app
│   ├── Dockerfile                 # Multi-stage production container build
│   ├── pyproject.toml             # Python dependencies
│   └── requirements.txt
├── docker-compose.yml             # Docker Compose orchestration (Server + Redis)
└── Spec/                          # Architectural & Design Specifications
    ├── UI_SPECIFICATION.md        # UI/UX, screen layouts, design tokens
    ├── AUTH_SPECIFICATION.md      # Auth lifecycle & profile modal spec
    ├── SOCKET_IO_SPECIFICATION.md # Real-time Socket.IO data contracts & events
    ├── DEVOPS_INFRASTRUCTURE_SPECIFICATION.md # Docker, Redis, Sentry, CI/CD spec
    ├── CLINICAL_CONTENT_RECOMMENDATIONS_SPECIFICATION.md # Decoupled content library spec
    └── AMY_AI_COACHING_SPECIFICATION.md # Coach Amy LangGraph & governance spec
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js** (v20+) & **npm**
- **Python** (v3.12+) and **`uv`**
- **Docker** & **Docker Compose** (optional, for containerized run)
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

- **API Server**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

### 3. Docker Compose Setup (Optional)

```bash
# Run FastAPI server and Redis in Docker
docker-compose up --build
```

---

### 4. Mobile Client Setup (`Client/mobile`)

```bash
cd Client/mobile

# Install dependencies
npm install

# Start the Expo development server
npm run start
```

- To open on **iOS Simulator**: Press **`i`** or run `npm run ios`.
- To open on **Android Emulator**: Press **`a`** or run `npm run android`.
- To open on **Web Preview**: Press **`w`** or run `npm run web`.

---

## 📖 Specifications Directory
For detailed design rationale and data contracts, refer to the [`Spec/`](./Spec/) directory:
- [UI & UX Specification (`Spec/UI_SPECIFICATION.md`)](./Spec/UI_SPECIFICATION.md)
- [Authentication Specification (`Spec/AUTH_SPECIFICATION.md`)](./Spec/AUTH_SPECIFICATION.md)
- [Socket.IO Specification (`Spec/SOCKET_IO_SPECIFICATION.md`)](./Spec/SOCKET_IO_SPECIFICATION.md)
- [DevOps & Infrastructure Specification (`Spec/DEVOPS_INFRASTRUCTURE_SPECIFICATION.md`)](./Spec/DEVOPS_INFRASTRUCTURE_SPECIFICATION.md)
- [Clinical Content & Recommendations Specification (`Spec/CLINICAL_CONTENT_RECOMMENDATIONS_SPECIFICATION.md`)](./Spec/CLINICAL_CONTENT_RECOMMENDATIONS_SPECIFICATION.md)
- [Amy AI Recovery Coach Specification (`Spec/AMY_AI_COACHING_SPECIFICATION.md`)](./Spec/AMY_AI_COACHING_SPECIFICATION.md)

---

## 📄 License
This project is licensed under the MIT License.
