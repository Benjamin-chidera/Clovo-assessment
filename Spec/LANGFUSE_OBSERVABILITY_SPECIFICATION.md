# Clovo Platform — Self-Hosted Langfuse LLM Observability Specification

## 1. Executive Overview & Data Privacy

Clovo uses a **100% Self-Hosted Langfuse** deployment for complete data sovereignty, LLM tracing, prompt management, and safety evaluation. 

All patient conversations, clinical rationales, tokens, latency metrics, and safety triage events remain **strictly within your own infrastructure**—ensuring total compliance with **UK GDPR**, **NHS England Information Governance**, and **Caldicott Principles**.

---

## 2. Self-Hosted Architecture & Storage Components

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              Clovo Self-Hosted Stack                                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. FastAPI + Socket.IO Server  │ Executes LangGraph Coach Amy pipeline, streams traces │
│    (`clovo-server:8000`)       │ to Langfuse via Async SDK / Callbacks.                │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 2. Langfuse Web Server & UI    │ Next.js / Node API web dashboard for trace inspection │
│    (`langfuse-server:3000`)    │ and Prompt Hub management. Accessible in browser.     │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 3. Langfuse Worker             │ Background worker for asynchronous trace ingestion,   │
│    (`langfuse-worker`)         │ automated evaluators, and metric aggregation.         │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 4. PostgreSQL Database         │ Stores users, projects, API keys, prompt versions,    │
│    (`langfuse-db:5432`)        │ and metadata tables with persistent volumes.          │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 5. ClickHouse Analytics        │ High-performance columnar database for high-volume    │
│    (`langfuse-clickhouse:8123`)│ trace indexing, span querying, and latency analytics. │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 6. MinIO Object Storage        │ Local S3-compatible storage for raw LLM prompt        │
│    (`langfuse-minio:9000`)     │ inputs, generation payloads, and large batch evals.   │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 7. Redis Message Queue         │ In-memory queue for ingestion buffering and cache.    │
│    (`clovo-redis:6379`)        │ (Shared with Socket.IO / Server cache).               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Docker Compose Orchestration (`docker-compose.yml`)

The following services are configured in Docker to orchestrate the entire self-hosted stack:

```yaml
version: '3.8'

services:
  # -------------------------------------------------------------
  # 1. Clovo Application Services
  # -------------------------------------------------------------
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
      - LANGFUSE_HOST=http://langfuse-server:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY:-pk-lf-local}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY:-sk-lf-local}
      - SENTRY_DSN=${SENTRY_SERVER_DSN:-}
      - DATABASE_URL=sqlite:///./clovo.db
    depends_on:
      redis:
        condition: service_healthy
      langfuse-server:
        condition: service_started
    volumes:
      - ./Server:/app
      - server-data:/app/data

  # -------------------------------------------------------------
  # 2. Self-Hosted Langfuse Observability Services
  # -------------------------------------------------------------
  langfuse-db:
    image: postgres:16-alpine
    container_name: clovo-langfuse-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  langfuse-server:
    image: ghcr.io/langfuse/langfuse:3
    container_name: clovo-langfuse-server
    restart: unless-stopped
    depends_on:
      langfuse-db:
        condition: service_healthy
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:postgres@langfuse-db:5432/langfuse
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=clovo-secret-key-32-chars-minimum-auth!
      - SALT=clovo-salt-for-langfuse-hashing-secure
      - TELEMETRY_ENABLED=false
      - LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=true

volumes:
  redis-data:
  server-data:
  langfuse-pgdata:
```

---

## 4. Backend Instrumentation (`Server/services/amy.py`)

Langfuse is instrumented as a standard callback handler in LangGraph, sending traces to the self-hosted instance at `LANGFUSE_HOST`:

```python
import os
from langfuse.callback import CallbackHandler
from langfuse import Langfuse

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-local")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-local")

# Gracefully initialize Langfuse client with fallback
langfuse_client = None
try:
    if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        print(f"📡 [Langfuse] Self-hosted client initialized for {LANGFUSE_HOST}")
except Exception as exc:
    print(f"⚠️ [Langfuse] Self-hosted connection notice: {exc}")


def get_conversation_callback_handler(patient_id: int, conversation_id: str, tags: list[str]) -> CallbackHandler:
    """Create a scoped Langfuse callback handler for the active patient session."""
    return CallbackHandler(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
        user_id=f"patient-{patient_id}",
        session_id=str(conversation_id),
        tags=tags,
    )
```

---

## 5. What You Will See in Your Self-Hosted Dashboard (`http://localhost:3000`)

1. **Traces & Execution Waterfall**:
   - Every patient question and Coach Amy generation visually broken down into spans (`safety_triage`, `coaching`).
   - Exact execution latency, prompt input, and token usage breakdown.
2. **Clinical Safety Events**:
   - Filterable traces tagged with `is_safety_alert: true` and `risk_level: high/critical` for clinical audit review.
3. **Prompt Hub**:
   - Create, edit, and version `AMY_SYSTEM_PROMPT` in the UI and promote versions to `production` with zero code restarts.
4. **Analytics & Performance**:
   - P50, P90, and P99 latency percentiles, error rates, and total token costs.

---

## 6. How to Start the Self-Hosted Stack

```bash
# 1. Start all containers (Server, Redis, Langfuse Server, Postgres DB)
docker-compose up -d

# 2. Open Langfuse Web UI in your browser
open http://localhost:3000

# 3. Create your local admin account and create project 'Clovo'
# 4. Generate your API keys (Settings -> API Keys)
# 5. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in Server/.env
```
