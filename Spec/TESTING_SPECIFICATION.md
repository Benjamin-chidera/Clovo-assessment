# Specification: Comprehensive Unit & Integration Testing Architecture

**Document Version**: `1.0.0`  
**Feature Name**: Clovo Surgical Recovery — Multi-Tier Quality Assurance & Test Specification  
**Target Systems**:
- **Backend (Server)**: FastAPI + Socket.IO + LangGraph + SQLModel (SQLite) + Redis + OpenAI/Whisper
- **Web (Admin Portal)**: Next.js 15 (App Router) + React 19 + TailwindCSS + Zustand
- **Mobile (Patient App)**: Expo SDK 52 + React Native 0.76 + NativeWind v4 + Zustand + Expo Audio/Speech
**Status**: Approved Architecture / Specification  

---

## 1. Executive Summary & Clinical Context

### 1.1 The Clinical Quality Imperative
Clovo is a clinical digital health platform assisting patients recovering from major surgeries (e.g. Total Knee Arthroplasty). Software regressions in this environment carry real-world patient safety implications:
1. **Safety Triage False Negatives**: Failure to detect a genuine medical emergency (e.g., deep vein thrombosis, wound dehiscence, suicidal crisis) could delay lifesaving intervention.
2. **Safety Triage False Positives**: Over-escalating normal recovery experiences (e.g., low mood, fatigue, lack of motivation) to emergency services (999/111) causes psychological panic, breaks patient trust, and overwhelms clinical care teams.
3. **Data Inconsistency (Adherence Desync)**: If a patient marks an exercise completed in chat, but the Mobile Home dashboard or Clinician Web Portal fails to reflect that completion, clinicians may incorrectly assume non-adherence and prescribe redundant interventions.
4. **Voice Interaction Failures**: Hands-free voice latency or state lockups while performing physical rehab exercises breaks the recovery flow.

### 1.2 Testing Strategy & Test Pyramid
To guarantee 99.9% clinical safety, reliability, and sub-100ms UI responsiveness, Clovo enforces a **three-tier testing pyramid**:

```
                  ┌────────────────────────┐
                  │    Cross-Platform      │  5% (Critical E2E
                  │   E2E Integrations     │  Clinical Journeys)
                  └───────────┬────────────┘
                              │
                ┌─────────────┴─────────────┐
                │    Integration Testing    │  25% (API Endpoints,
                │ (Socket.IO, DB, Stores)   │  Cache Invalidation)
                └─────────────┬─────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │            Unit Testing               │  70% (LangGraph Nodes,
          │  (Safety, Validators, Memoized UI)    │  Stores, Reducers, Pure Fns)
          └───────────────────────────────────────┘
```

| Layer | Coverage Target | Key Focus Areas | Tools |
| :--- | :---: | :--- | :--- |
| **Server** | ≥ 90% Safety / ≥ 85% Core | LangGraph Nodes, Fast-Path Regex, Safety Triage, Socket.IO Events, SQLModel | `pytest`, `pytest-asyncio`, `httpx`, `fakeredis` |
| **Web** | ≥ 80% Components / Stores | Triage Dashboard, Real-Time Alert Feeds, Adherence Metrics, Modal Actions | `Vitest`, `@testing-library/react`, `msw` |
| **Mobile** | ≥ 80% Components / Stores | VAD Silence Detection, Optimistic Task Updates, Memoized Bubble Performance | `Jest`, `jest-expo`, `@testing-library/react-native` |

---

## 2. Server (Backend) Testing Specification

### 2.1 Test Framework & Tooling Setup
- **Runner**: `pytest` with `pytest-asyncio` for asynchronous FastAPI and Socket.IO tests.
- **HTTP Client**: `httpx.AsyncClient` targeting the FastAPI ASGI application.
- **Database**: In-memory SQLite (`sqlite:///:memory:`) instantiated per test session with clean migrations.
- **Cache**: `fakeredis.aioredis` simulating Redis caching and pattern-based invalidation.
- **LLM / External APIs**: Deterministic Mock Fixtures simulating OpenAI ChatCompletion and Whisper API responses.

### 2.2 Server Unit Tests (`Server/tests/unit/`)

#### A. Safety Service & Triage Pipeline (`test_safety_service.py`)
| Test ID | Function Under Test | Scenario / Input | Expected Assertion |
| :--- | :--- | :--- | :--- |
| `SRV-UNIT-SAF-001` | `_check_deterministic_fast_path` | *"I want to kill myself"* or *"I am suicidal"* | Returns `category="mental_health"`, `risk_level="critical"`, `is_safety_alert=True` in < 2ms without invoking LLM. |
| `SRV-UNIT-SAF-002` | `_check_deterministic_fast_path` | *"My knee is hot, swollen, and oozing pus"* | Returns `category="acute_medical"`, `risk_level="high"`, `is_safety_alert=True`. |
| `SRV-UNIT-SAF-003` | `_check_deterministic_fast_path` | *"My pain is an 8 out of 10"* | Returns `category="severe_pain"`, `risk_level="medium"`, `is_safety_alert=True`. |
| `SRV-UNIT-SAF-004` | `screen_message_semantic` | *"I feel really sad to do anything today."* | Returns `category="safe"`, `risk_level=None`, `is_safety_alert=False` (prevents 999 false positive). |
| `SRV-UNIT-SAF-005` | `screen_message_semantic` | *"I have zero motivation and feel completely exhausted today."* | Returns `category="safe"`, `risk_level=None`, `is_safety_alert=False`. |
| `SRV-UNIT-SAF-006` | `screen_message_semantic` | *"Should I double my blood thinner dose?"* | Returns `category="clinical_decision"`, `risk_level="low"`, `is_safety_alert=True`. |

#### B. LangGraph Cognitive Pipeline (`test_amy_graph.py`)
| Test ID | Node / Component | Input State | Expected Node Output |
| :--- | :--- | :--- | :--- |
| `SRV-UNIT-GRF-001` | `safety_triage_node` | Patient mentions sudden shortness of breath | State updated: `is_safety_alert=True`, routes directly to `safety_escalation_node`. |
| `SRV-UNIT-GRF-002` | `intent_classification_node` | *"I finished my Quad Sets today"* | `is_task_completion=True`, `completed_activity_name="Quad Sets"`, `should_show_options=False` (No card clutter). |
| `SRV-UNIT-GRF-003` | `intent_classification_node` | *"I haven't done straight leg raises yet"* | `is_task_unmark=True`, `unmarked_activity_name="Straight Leg Raise"`, `should_show_options=False`. |
| `SRV-UNIT-GRF-004` | `intent_classification_node` | *"What's my plan for today?"* | `intent="view_plan"`, `should_show_options=True` (Interactive cards triggered). |
| `SRV-UNIT-GRF-005` | `intent_classification_node` | *"I feel really sad to do anything today."* | `intent="general"`, `should_show_options=False` (Zero card clutter, routes to emotional support). |
| `SRV-UNIT-GRF-006` | `recommendation_action_node` | `is_task_completion=True`, task ID #1 | SQLite task record updated to `is_completed=True`, completed timestamp set. |
| `SRV-UNIT-GRF-007` | `recommendation_action_node` | `is_task_unmark=True`, task ID #1 | SQLite task record reset to `is_completed=False`, completed timestamp set to `None`. |
| `SRV-UNIT-GRF-008` | `coaching_node` (Emotional) | Patient feeling down/discouraged | Generates compassionate, warm response validating feelings, suggests 4-7-8 breathing or rest day, zero guilt. |
| `SRV-UNIT-GRF-009` | `response_validation_node` | LLM returns text with unapproved medication | Validator rejects or replaces text with safe clinical library grounded advice. |
| `SRV-UNIT-GRF-010` | `extract_quick_replies` | Emotional support message | Returns comforting options: `["I'll take a rest day 🧘", "Guide me in 4-7-8 breathing 🌬️", "Tell me about my progress 🌟"]`. |

#### C. Clinical Patient Services & Models (`test_patient_service.py`)
| Test ID | Function Under Test | Scenario | Expected Assertion |
| :--- | :--- | :--- | :--- |
| `SRV-UNIT-PAT-001` | `audit_daily_adherence_and_missed_tasks` | Patient completed all 4 tasks yesterday | `has_missed_yesterday=False`, `consecutive_missed_days=0`. |
| `SRV-UNIT-PAT-002` | `audit_daily_adherence_and_missed_tasks` | Patient missed tasks for 2 consecutive days | `requires_clinician_alert=True`, `consecutive_missed_days=2`. |
| `SRV-UNIT-PAT-003` | `increment_streak` | Patient completes first task of the day | Streak count increments by 1; `last_active_date` updated to today. |

---

### 2.3 Server Integration Tests (`Server/tests/integration/`)

#### A. REST API Endpoints (`test_api_endpoints.py`)
| Test ID | Endpoint | Method | Payload / Params | Expected Response & State Change |
| :--- | :--- | :---: | :--- | :--- |
| `SRV-INT-API-001` | `/api/home` | GET | `patient_id=1` | Returns `200 OK` with patient header, daily adherence streak, and today's recommendations array. |
| `SRV-INT-API-002` | `/api/recommendations/action` | POST | `{"recommendation_id": 1, "is_completed": true}` | Returns `200 OK`, updates database, invalidates `tasks:*` Redis cache. |
| `SRV-INT-API-003` | `/api/admin/safety-events` | GET | `risk_level=critical` | Returns `200 OK` with list of recorded safety events filtered by risk. |
| `SRV-INT-API-004` | `/api/voice/transcribe` | POST | Multipart WAV audio stream | Returns `200 OK` with `{"text": "I finished my Quad Sets"}` without hallucinated noise. |

#### B. Socket.IO Real-Time Gateway (`test_socket_events.py`)
| Test ID | Event Flow | Payload | Expected Outgoing Broadcasts & Side Effects |
| :--- | :--- | :--- | :--- |
| `SRV-INT-SCK-001` | Client emits `user_message` | `{"text": "I did my Quad Sets today"}` | Server emits `coach_message` (warm celebration) + server emits `task_sync` with `taskId=1, isCompleted=True`. |
| `SRV-INT-SCK-002` | Client emits `user_message` | `{"text": "I have unbearable sharp knee pain 9/10"}` | Server emits `coach_message` with `isSafetyAlert=True, riskLevel="medium"` + records event in `SafetyEvent` table. |
| `SRV-INT-SCK-003` | Client emits `user_message` | `{"text": "[VOICE_SESSION_START]"}` | Server emits welcoming `coach_message` introducing voice mode without treating it as an unrecognized command. |
| `SRV-INT-SCK-004` | Client emits `user_message` | `{"text": "What's my plan for today?"}` | Server emits `coach_message` containing `options: [4 recovery cards]` for mobile UI rendering. |

---

## 3. Web (Clinician & Admin Portal) Testing Specification

### 3.1 Test Framework & Tooling Setup
- **Runner**: `Vitest` with jsdom environment.
- **Component Testing**: `@testing-library/react` and `@testing-library/user-event`.
- **API Mocking**: `Mock Service Worker (MSW)` intercepting HTTP requests to `/api/admin/*`.
- **State Management**: Zustand test harness resetting stores between specs.

### 3.2 Web Unit Tests (`Client/web/__tests__/unit/`)

#### A. Component & UI Unit Tests (`components/`)
| Test ID | Component Under Test | Prop / State Setup | Expected Assertion |
| :--- | :--- | :--- | :--- |
| `WEB-UNIT-CMP-001` | `MetricCard.tsx` | `title="Active Patients"`, `value=42`, `trend="+12%"` | Correct title, value, and emerald positive trend indicator rendered. |
| `WEB-UNIT-CMP-002` | `AlertBanner.tsx` | `riskLevel="critical"`, `patientName="Sarah Jenkins"` | Renders red emergency container (`bg-red-50`), warning icon, and immediate contact action button. |
| `WEB-UNIT-CMP-003` | `AlertBanner.tsx` | `riskLevel="low"`, `trigger="Missed adherence"` | Renders amber clinical notice banner without emergency sirens. |
| `WEB-UNIT-CMP-004` | `PatientRow.tsx` | `streak=5`, `adherence="85%"` | Formats flame emoji `5 days 🔥`, displays colored adherence progress bar. |
| `WEB-UNIT-CMP-005` | `TriageActionModal.tsx` | User clicks *"Acknowledge Alert"* | Triggers `onResolve` callback with resolution note; modal closes. |

#### B. Store Unit Tests (`stores/useAdminStore.ts`)
| Test ID | Store Action | Input | Expected Store State Change |
| :--- | :--- | :--- | :--- |
| `WEB-UNIT-STR-001` | `setFilterRiskLevel` | `"critical"` | `activeFilter` updated to `"critical"`; filtered safety events list contains only critical events. |
| `WEB-UNIT-STR-002` | `resolveSafetyEvent` | `eventId=10` | Event status updated to `"resolved"`; unread emergency badge count decrements by 1. |
| `WEB-UNIT-STR-003` | `selectPatient` | `patientId=1` | `selectedPatientId` set; triggers retrieval of patient timeline and milestone history. |

### 3.3 Web Integration Tests (`Client/web/__tests__/integration/`)

| Test ID | Test Case | User Interaction Flow | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `WEB-INT-FLW-001` | **Emergency Triage Feed** | Clinician opens portal ➔ 1 critical event present in list ➔ clicks *"Contact Patient"* ➔ clicks *"Resolve"* | Modal opens with patient details ➔ resolution POST sent via MSW ➔ UI removes banner ➔ metrics update live. |
| `WEB-INT-FLW-002` | **Patient Adherence Cockpit** | Clinician selects patient *"Sarah Jenkins"* ➔ views 7-day adherence chart | Correct timeline markers rendered for Quad Sets, Protein Snack, and 4-7-8 Breathing. |
| `WEB-INT-FLW-003` | **Real-Time Safety Broadcast** | Socket emits new `safety_alert` event | Web portal displays toast notification and dynamically appends the alert to the top of the feed without page refresh. |

---

## 4. Mobile (Patient App) Testing Specification

### 4.1 Test Framework & Tooling Setup
- **Runner**: `Jest` configured with `jest-expo` preset.
- **Component Testing**: `@testing-library/react-native`.
- **Native Modules Mocked**:
  - `expo-audio`: Recording instance, metering level (`-160 to 0 dBFS`), status listeners.
  - `expo-speech`: Speech synthesis methods (`speak`, `stop`, `isSpeakingAsync`).
  - `expo-haptics`: `impactAsync`, `notificationAsync`.
  - `@expo/vector-icons`: Ionicons mock.

### 4.2 Mobile Unit Tests (`Client/mobile/__tests__/unit/`)

#### A. Component Performance & UI Unit Tests
| Test ID | Component Under Test | Prop / Scenario | Expected Assertion |
| :--- | :--- | :--- | :--- |
| `MOB-UNIT-CMP-001` | `MessageBubble.tsx` | Render user message | Renders right-aligned bubble with blue background (`#3B49DF`) and white text. |
| `MOB-UNIT-CMP-002` | `MessageBubble.tsx` | Render coach message with `isSafetyAlert=True, riskLevel="critical"` | Renders red emergency alert card (`bg-red-50`), alert icon, and red text. |
| `MOB-UNIT-CMP-003` | `MessageBubble.tsx` | Render coach message with `options: [4 tasks]` | Renders `RecoveryActivityCards` child container with 4 cards. |
| `MOB-UNIT-CMP-004` | `MessageBubble.tsx` (Memoization) | Re-render chat list with same message ID and text | `MessageBubble` does **NOT** re-render (verified via render counter spy), preventing `VirtualizedList` slow update warnings. |
| `MOB-UNIT-CMP-005` | `RecoveryActivityCards.tsx` | Tap activity card checkbox | Fires `onTaskToggle` callback with correct `taskId` and triggers haptic impact. |
| `MOB-UNIT-CMP-006` | `CoachHeader.tsx` | `isVoiceActive=true, isListening=true` | Displays `🎙️ Listening...` status and shows explicit `✕ End` button. |
| `MOB-UNIT-CMP-007` | `ChatInputBar.tsx` | User types text and taps send | `onSendMessage` invoked with text; text input clears immediately. |

#### B. Store Unit Tests (`stores/`)
| Test ID | Store | Action / Event | Expected State Change |
| :--- | :--- | :--- | :--- |
| `MOB-UNIT-STR-001` | `useChatStore` | `addMessage` (User) | Optimistically appends message with temporary ID, status `delivered`, and sets `isTyping=True`. |
| `MOB-UNIT-STR-002` | `useChatStore` | Receive `coach_message` | Appends coach message, updates quick replies, and sets `isTyping=False`. |
| `MOB-UNIT-STR-003` | `useVoiceStore` | `startVoiceSession` | Activates audio mode, requests mic permissions, starts recording, sets `isVoiceActive=True`. |
| `MOB-UNIT-STR-004` | `useVoiceStore` (VAD) | Audio meter reads `> -36 dBFS` for 300ms | Flags `isSpeechDetected=True`, resets silence countdown timer. |
| `MOB-UNIT-STR-005` | `useVoiceStore` (VAD) | Audio meter reads `< -36 dBFS` for 1600ms | Triggers `autoStopAndUploadSpeech()` without user tapping any buttons. |
| `MOB-UNIT-STR-006` | `useVoiceStore` (Barge-In) | User starts speaking while Amy is speaking (`isSpeaking=True`) | Immediately invokes `Speech.stop()`, silences Amy, and starts user listening window. |
| `MOB-UNIT-STR-007` | `useHomeStore` | Receive `task_sync` event (`taskId=1, isCompleted=True`) | Task #1 marked complete in home task list; completion percentage recalculates. |

### 4.3 Mobile Integration Tests (`Client/mobile/__tests__/integration/`)

| Test ID | Test Scenario | Interaction Flow | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `MOB-INT-FLW-001` | **Full Chat Task Completion Sync** | User types *"I did my quad sets"* ➔ Send ➔ Server responds with `task_sync` | 1. User message appears in Chat.<br>2. Coach Amy congratulates Sarah.<br>3. Task #1 checkbox checked in Chat.<br>4. Navigating to Home tab shows Quad Sets completed with progress bar advanced. |
| `MOB-INT-FLW-002` | **Hands-Free Voice Dialogue Cycle** | User taps Mic in Header ➔ Speaks *"What tasks do I have?"* ➔ Silence detected | 1. Audio recorded to WAV.<br>2. Uploaded to `/api/voice/transcribe`.<br>3. Amy speaks response aloud.<br>4. Header status updates to `🔊 Amy is speaking...`.<br>5. Chat displays message. |
| `MOB-INT-FLW-003` | **Emergency Triage In-App Handling** | User sends message containing severe chest pain | Chat renders red emergency card with 999 call action button; voice speech halts to avoid speaking over crisis. |

---

## 5. End-to-End (E2E) Cross-Platform Scenarios

These integration tests validate complete data and event propagation across Mobile, Server, and Web simultaneously:

```
[ Mobile Patient App ]              [ Clovo Server ]              [ Web Admin Portal ]
        │                                  │                               │
        │─── 1. "I completed Quad Sets" ──▶│                               │
        │    (via WebSocket)               │                               │
        │                                  │─── 2. Update SQLite & Redis ─▶│
        │                                  │    Invalidate Cache           │
        │                                  │                               │
        │◀── 3. task_sync Event ───────────│─── 4. Update Adherence Metric▶│
        │    (Home & Chat updated)         │    (Progress bar 75% -> 100%) │
```

### Scenario 1: Multi-Tab Real-Time Adherence Synchronization (`E2E-001`)
1. **Pre-condition**: Patient Sarah has 3 of 4 tasks completed today.
2. **Action**: Sarah opens Mobile Chat and sends *"Done with 4-7-8 breathing!"*.
3. **Assertions**:
   - Amy responds celebrating the 4th completed routine.
   - `task_sync` event delivered to Mobile Home store.
   - Navigating to Mobile Home displays **100% Complete** and streak badge increments to **6 Days 🔥**.
   - Admin Web Portal updates Sarah's adherence record from `75%` to `100%` in real time.

### Scenario 2: Emergency Safety Triage & Clinician Escalation (`E2E-002`)
1. **Pre-condition**: Clinician is monitoring the Web Admin Triage feed.
2. **Action**: Patient speaks into Mobile: *"I fell down the stairs and hit my head"*.
3. **Assertions**:
   - Fast-path triage triggers in < 2ms on Server.
   - Mobile Chat displays red **Urgent Medical Alert** instructing patient to call 999.
   - Server records emergency event in SQLite `SafetyEvent` table with `risk_level="critical"`.
   - Web Admin Portal immediately displays pulsating red emergency alert banner at the top of the feed with patient phone number and triage notes.

### Scenario 3: Non-Emergency Emotional Support (Zero False Alarms) (`E2E-003`)
1. **Action**: Patient types *"I feel really sad to do anything today"*.
2. **Assertions**:
   - Triage flags message as `category="safe"` (`is_safety_alert=False`).
   - Amy responds with deep human compassion, normalizes recovery emotions, and suggests gentle 4-7-8 breathing or a rest day.
   - Zero emergency alerts appear in the Web Admin Portal.
   - Zero card dumps or visual distractions are injected into Mobile Chat.

---

## 6. Test Execution & CI/CD Gating

### 6.1 Local Test Commands

#### Server Test Suite:
```bash
# Run all Server unit and integration tests
cd Server
uv run pytest tests/ -v --cov=services --cov=routes --cov-report=term-missing

# Run safety triage tests specifically
uv run pytest tests/unit/test_safety_service.py -v
```

#### Web Test Suite:
```bash
# Run all Web unit and integration tests
cd Client/web
pnpm test
pnpm test:coverage
```

#### Mobile Test Suite:
```bash
# Run all Mobile unit and integration tests
cd Client/mobile
npm test -- --watchAll=false --coverage
```

### 6.2 GitHub Actions CI/CD Pipeline Configuration (`.github/workflows/test.yml`)
```yaml
name: Clovo Quality & Safety CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  server-tests:
    name: Backend PyTest & Safety Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv & Python 3.12
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
      - name: Install Dependencies
        working-directory: ./Server
        run: uv sync
      - name: Execute PyTest with Safety Threshold
        working-directory: ./Server
        run: |
          uv run pytest tests/ -v --cov=services --cov-fail-under=85

  web-tests:
    name: Admin Web Vitest Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: Client/web/pnpm-lock.yaml
      - name: Install Dependencies
        working-directory: ./Client/web
        run: pnpm install --frozen-lockfile
      - name: Run Vitest
        working-directory: ./Client/web
        run: pnpm test --run

  mobile-tests:
    name: Mobile Jest & VAD Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install Dependencies
        working-directory: ./Client/mobile
        run: npm ci
      - name: Run Jest
        working-directory: ./Client/mobile
        run: npm test -- --ci --coverage
```

---

## 7. Definition of Done (DoD) & Acceptance Criteria
A pull request or feature branch touching clinical safety, coaching logic, or mobile chat may only be merged when:
1. **100% Pass Rate** on all `SRV-UNIT-SAF-*` safety classification tests.
2. **Zero False Positives** on benchmark dataset of 50 emotional/low-mood patient expressions.
3. **Zero UI Regressions**: Mobile Chat FlatList renders without `VirtualizedList` latency warnings.
4. **Code Coverage**: Minimum 85% branch coverage on `Server/services/` and 80% on Client stores.
