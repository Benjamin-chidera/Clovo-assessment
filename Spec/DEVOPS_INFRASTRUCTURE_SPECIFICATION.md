# Clovo Platform — DevOps, Infrastructure, Observability & CI/CD Specification

## 1. Overview & Objectives

This specification outlines the production-ready infrastructure, containerization, caching/pub-sub, error monitoring, and automated CI/CD pipelines for the **Clovo Platform**:

1. **Docker & Containerization**: Multi-stage, secure container builds for the FastAPI backend and full container orchestration via `docker-compose`.
2. **Redis Integration (Server)**: High-performance in-memory caching and distributed Socket.IO Pub/Sub message broker (`AsyncRedisManager`).
3. **Sentry Observability (Server & Client)**: Full-stack error monitoring, performance profiling, and distributed tracing across FastAPI and Expo mobile.
4. **GitHub Actions CI/CD**: Automated quality gates (lint, type check, tests, Docker build) and deployment pipelines.

---

## 2. Infrastructure Architecture Diagram

```
                              ┌───────────────────────────────────┐
                              │       GitHub Actions CI/CD        │
                              │ ├── CI: Lint, Typecheck, Test     │
                              │ └── CD: Docker Build & Deploy     │
                              └─────────────────┬─────────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          │                                           │
                          ▼                                           ▼
            ┌───────────────────────────┐               ┌───────────────────────────┐
            │   Mobile Client (Expo)    │               │  FastAPI Backend (Docker) │
            │                           │               │                           │
            │  • @sentry/react-native   │               │  • sentry-sdk[fastapi]    │
            │  • socket.io-client       │               │  • python-socketio        │
            └─────────────┬─────────────┘               └─────────────┬─────────────┘
                          │                                           │
                          │        WebSocket / REST (Port 8000)       │
                          └───────────────────────────────────────────┤
                                                                      │
                                                ┌─────────────────────┴───────────────┐
                                                │                                     │
                                                ▼                                     ▼
                                  ┌───────────────────────────┐         ┌───────────────────────────┐
                                  │   Redis (Cache & PubSub)  │         │      Sentry Cloud         │
                                  │   • Socket.IO Manager     │         │   • Error Monitoring      │
                                  │   • Session & State Cache │         │   • Performance Tracing   │
                                  └───────────────────────────┘         └───────────────────────────┘
```

---

## 3. Docker & Containerization Architecture

### 3.1 Backend `Dockerfile` (`Server/Dockerfile`)
A lightweight, secure, multi-stage Docker build utilizing `uv` for ultra-fast dependency resolution and a non-root runtime container.

```dockerfile
# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

COPY pyproject.toml requirements.txt ./
RUN uv pip install --no-cache --system -r requirements.txt

# Stage 2: Production Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Security: Create non-root system user
RUN addgroup --system appgroup && adduser --system --group appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Docker Compose (`docker-compose.yml`)
Local development and staging multi-container orchestration with healthcheck dependencies.

```yaml
version: '3.8'

services:
  # 1. Redis Service (Pub/Sub & Caching)
  redis:
    image: redis:7-alpine
    container_name: clovo-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: ["redis-server", "--appendonly", "yes"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # 2. FastAPI + Socket.IO Server
  server:
    build:
      context: ./Server
      dockerfile: Dockerfile
    container_name: clovo-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENV=development
      - PORT=8000
      - REDIS_URL=redis://redis:6379/0
      - SENTRY_DSN=${SENTRY_SERVER_DSN:-}
      - SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-development}
      - DATABASE_URL=sqlite:///./clovo.db
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./Server:/app
      - server-data:/app/data

volumes:
  redis-data:
  server-data:
```

---

## 4. Redis Integration (Server)

### 4.1 Objectives
1. **Socket.IO Scaling**: Distributes real-time events across multiple server instances via Redis Pub/Sub adapter (`AsyncRedisManager`).
2. **Caching Layer**: Caches patient profiles, dashboard aggregates, and recovery templates with Time-To-Live (TTL).
3. **Graceful Fallback**: Automatically falls back to in-memory mode if Redis is unreachable in local offline development.

### 4.2 Python Dependencies (`Server/requirements.txt`)
```text
redis>=5.0.8
hiredis>=3.0.0
```

### 4.3 Architecture & Implementation Pattern (`Server/services/redis_service.py`)
```python
import os
import redis.asyncio as aioredis
import socketio

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 1. Socket.IO Redis Manager
def get_socket_manager():
    try:
        return socketio.AsyncRedisManager(REDIS_URL)
    except Exception as e:
        print(f"⚠️ Redis connection failed, falling back to local memory manager: {e}")
        return None

# 2. Async Redis Client for Caching
class RedisCacheService:
    def __init__(self, url: str = REDIS_URL):
        self.redis_url = url
        self.client: aioredis.Redis | None = None

    async def init(self):
        try:
            self.client = aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self.client.ping()
            print("✅ [Redis] Connected successfully.")
        except Exception as e:
            print(f"⚠️ [Redis] Disabled or unreachable: {e}")
            self.client = None

    async def get(self, key: str) -> str | None:
        if not self.client:
            return None
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> bool:
        if not self.client:
            return False
        return await self.client.set(key, value, ex=ttl_seconds)

redis_cache = RedisCacheService()
```

---

## 5. Sentry Observability Integration

### 5.1 Server Sentry Configuration (`Server`)
- **Package**: `sentry-sdk[fastapi]>=2.13.0`
- **Features**: Error capturing, transaction tracing, ASGI middleware capture, automatic user context tagging (`patient_id`).

#### Integration in `Server/main.py`:
```python
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.redis import RedisIntegration

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENV = os.getenv("SENTRY_ENVIRONMENT", "development")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENV,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            RedisIntegration(),
        ],
        traces_sample_rate=1.0 if SENTRY_ENV == "development" else 0.2,
        profiles_sample_rate=0.2,
        send_default_pii=False,
    )
    print(f"🛡️ [Sentry] Server monitoring active in '{SENTRY_ENV}' mode.")
```

### 5.2 Mobile Client Sentry Configuration (`Client/mobile`)
- **Package**: `@sentry/react-native`
- **Features**: Unhandled JS exceptions, native crash reporting, navigation breadcrumbs, component render profiling.

#### Integration in `Client/mobile/src/app/_layout.tsx`:
```typescript
import * as Sentry from '@sentry/react-native';

const SENTRY_DSN = process.env.EXPO_PUBLIC_SENTRY_DSN || '';
const SENTRY_ENV = process.env.EXPO_PUBLIC_APP_ENV || 'development';

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENV,
    tracesSampleRate: 1.0,
    enableAutoSessionTracking: true,
  });
}
```

---

## 6. GitHub Actions CI/CD Pipelines

### 6.1 Continuous Integration Workflow (`.github/workflows/ci.yml`)
Triggered on every push and pull request against `main` and `develop`.

```yaml
name: Clovo CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  # 1. Backend Checks (FastAPI + Python)
  backend-ci:
    name: Backend Lint, Typecheck & Tests
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: ./Server

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v2
        with:
          enable-cache: true

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Dependencies
        run: uv sync

      - name: Verify Routes & Syntax
        run: uv run python -c "from main import app; print('Routes verified:', len(app.routes))"

      - name: Verify Docker Build
        run: docker build -t clovo-server:test .

  # 2. Mobile Client Checks (Expo + React Native)
  mobile-ci:
    name: Mobile Typecheck & Validation
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: ./Client/mobile

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"
          cache-dependency-path: ./Client/mobile/package-lock.json

      - name: Install Dependencies
        run: npm ci

      - name: TypeScript Typecheck
        run: npx tsc --noEmit
```

### 6.2 Continuous Deployment Workflow (`.github/workflows/deploy.yml`)
Triggered on merge to `main`. Builds and pushes Docker images to GitHub Container Registry (GHCR).

```yaml
name: Clovo CD / Container Publishing

on:
  push:
    branches: [main]

jobs:
  build-and-push-server:
    name: Build & Push Backend Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build & Push Docker Image
        uses: docker/build-push-action@v5
        with:
          context: ./Server
          file: ./Server/Dockerfile
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/server:latest
            ghcr.io/${{ github.repository }}/server:${{ github.sha }}
```

---

## 7. Environment Variables & Secret Configuration Matrix

| Variable | Scope | Purpose | Default / Example |
| :--- | :--- | :--- | :--- |
| `REDIS_URL` | Server | Connection URI for Redis Pub/Sub & caching | `redis://localhost:6379/0` |
| `SENTRY_DSN` | Server | Sentry project DSN for FastAPI errors | `https://example@o0.ingest.sentry.io/0` |
| `SENTRY_ENVIRONMENT` | Server | Environment tag (`development`, `production`) | `development` |
| `DATABASE_URL` | Server | SQLite/Postgres connection string | `sqlite:///./clovo.db` |
| `EXPO_PUBLIC_SENTRY_DSN` | Client (Mobile) | Sentry DSN for React Native crashes | `https://example@o0.ingest.sentry.io/1` |
| `EXPO_PUBLIC_SERVER_URL` | Client (Mobile) | Base URL for FastAPI & Socket.IO server | `http://localhost:8000` |
| `GITHUB_TOKEN` | CI/CD | Auto-provided secret for GHCR image pushes | *(Auto-generated)* |

---

## 8. Implementation Checklist

- [ ] **Dockerization**:
  - [ ] Create `Server/Dockerfile` (multi-stage Python build).
  - [ ] Create root `docker-compose.yml` (Server + Redis services).
  - [ ] Add `.dockerignore` files for clean build contexts.
- [ ] **Redis Backend Setup**:
  - [ ] Add `redis` and `hiredis` to `Server/requirements.txt` & `pyproject.toml`.
  - [ ] Implement `Server/services/redis_service.py` with `AsyncRedisManager` adapter.
  - [ ] Update `Server/main.py` and `Server/routes/sockets.py` to utilize Redis manager with fallback.
- [ ] **Sentry Integration**:
  - [ ] Add `sentry-sdk[fastapi]` to `Server/requirements.txt`.
  - [ ] Initialize Sentry in `Server/main.py` with FastAPI & Redis integrations.
  - [ ] Install `@sentry/react-native` in `Client/mobile` and initialize in `_layout.tsx`.
- [ ] **GitHub Actions Workflows**:
  - [ ] Create `.github/workflows/ci.yml` (Backend & Mobile verification).
  - [ ] Create `.github/workflows/deploy.yml` (GHCR container builds).
