# Clovo Clinician & Admin Web Portal — Lightweight Technical & UX Specification

## 1. Executive Summary & Assessment Focus

This specification defines the lightweight, privacy-compliant **Next.js Clinician & Admin Portal** for the Clovo AI Recovery Coach assessment.

The primary focus of this assessment is **Coach Amy** (the intelligent LangGraph agent). The Admin Web Portal serves as the essential, lightweight **Clinician Oversight & Safety Triage Cockpit** to demonstrate:
1. **Real-Time Safety Triage**: Immediate visibility into Amy's 4-tier safety escalations (`Critical`, `High`, `Medium`, `Low`) via Socket.IO.
2. **AI Transparency & Auditability**: Audited inspection of Amy's multi-turn conversations and Langfuse trace links.
3. **Healthcare Privacy & Ethics (HIPAA / GDPR / NHS DTAC)**: Anomaly/alert-driven access (no unrestricted chat browsing), automatic PII masking, and access logging.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Streamlined 4-Screen Architecture                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. Dashboard (/dashboard)     │ High-level KPIs + Live incoming safety alerts    │
│ 2. Safety Events (/safety)    │ 4-Tier Clinical Triage Queue & Resolution Drawer │
│ 3. Conversations (/chats)     │ Escalated Cases & Audited Message Inspector      │
│ 4. Patients (/patients)       │ Lightweight Patient Directory & Recovery Status  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Privacy & Governance Principles (Lightweight Implementation)

### 2.1 The "Need-to-Know" Principle
- **Alert-Driven Default**: The clinician lands on the **Safety Triage Queue** rather than an open list of all patient chats.
- **Access Gating**: Conversations are accessed directly through active **Safety Alerts** or an audited search requiring a simple **Clinical Reason for Access** (e.g., *"Routine review"*, *"Safety alert follow-up"*).

### 2.2 Data Minimization & Redaction
- Sensitive PII (NHS numbers, phone numbers) are masked by default: `NHS: •••••• 4819`.

### 2.3 Lightweight Audit Logging
- Every view of a conversation or patient record creates an entry in the `audit_logs` table (`user_id`, `action`, `patient_id`, `access_reason`, `timestamp`).

---

## 3. Technology Stack & Design System

### 3.1 Tech Stack
- **Framework**: Next.js 16 (App Router, TypeScript)
- **State Management**: **Zustand** (`useSafetyTriageStore.ts`, `useAuthStore.ts`)
- **Styling**: Tailwind CSS v4 with clean, modern healthcare tokens
- **Real-Time Socket**: `socket.io-client` connected to `http://localhost:8000` (`/socket.io`)
- **Icons**: Lucide React
- **Observability Links**: Direct URLs to local Langfuse traces (`http://localhost:3000`)

### 3.2 Design System Color Palette
```
┌──────────────────────────────┬───────────────────────────────────────────────────┐
│ Token                        │ Hex / Value                                       │
├──────────────────────────────┼───────────────────────────────────────────────────┤
│ Brand Primary                │ #3B49DF (Vibrant Royal Indigo)                    │
│ Brand Primary Light          │ #EEF2FF (Soft Lavender Tint)                      │
│ Background Surface           │ #F8F9FD (Clean Off-White) / #0B0F19 (Dark)        │
│ Card Surface                 │ #FFFFFF / #111827 (Dark Charcoal)                 │
│ Border / Divider             │ #E5E7EB / #1F2937                                 │
│ Critical Severity (Tier 1)   │ #EF4444 (Crimson Red) / Badge: #FEE2E2            │
│ High Severity (Tier 2)       │ #F97316 (Flame Orange) / Badge: #FFEDD5           │
│ Medium Severity (Tier 3)     │ #F59E0B (Amber Gold) / Badge: #FEF3C7             │
│ Low / Info Severity (Tier 4) │ #3B82F6 (Sky Blue) / Badge: #DBEAFE               │
│ Success / Resolved           │ #10B981 (Emerald Green) / Badge: #D1FAE5          │
└──────────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 4. Route Hierarchy & Screen Specifications

```
Client/web/app/
├── layout.tsx                   # Root layout with sidebar navigation & Socket.IO listener
├── page.tsx                     # Redirects to /dashboard
├── dashboard/
│   └── page.tsx                 # 1. Executive KPIs & Real-Time Alert Feed
├── safety-events/
│   └── page.tsx                 # 2. 4-Tier Safety Triage Board & Resolution Drawer
├── conversations/
│   └── page.tsx                 # 3. Escalated Cases & Audited Conversation Inspector
└── patients/
    └── page.tsx                 # 4. Lightweight Patient Directory & Recovery Status
```

---

### 4.1 Screen 1: Dashboard (`/dashboard`)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  CLOVO CLINICIAN OVERVIEW                      [Status: 🟢 Connected]  [🔔 Alerts (2)] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  KPI CARDS                                                                             │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐  │
│  │ Enrolled Patients│ │ Active Alerts    │ │ 7-Day Adherence  │ │ AI Safety Score  │  │
│  │ 12 Patients      │ │ 2 Unresolved     │ │ 91.5%            │ │ 100% (Langfuse)  │  │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘  │
│                                                                                        │
│  LIVE SAFETY ALERTS FEED (Socket.IO Real-Time)            PATIENT STATUS OVERVIEW      │
│  ┌──────────────────────────────────────────────────────┐ ┌──────────────────────────┐ │
│  │ 🚨 Sarah Jenkins · Knee Surgery · High Risk          │ │ Sarah J. (T-21d): 94% 🟢 │ │
│  │    "Hit head on floor, feeling dizzy" (2m ago)       │ │ Mark D.  (T+5d):  78% 🟡 │ │
│  │    [Review Escalation ➔]                             │ │ Elena R. (T-14d): 100% 🟢│ │
│  ├──────────────────────────────────────────────────────┤ └──────────────────────────┘ │
│  │ 🔵 David Miller · Pre-op ACL · Low Risk              │ AI ENGINE HEALTH             │
│  │    "Flushed pills in toilet" (15m ago)               │ ┌──────────────────────────┐ │
│  │    [Review Escalation ➔]                             │ │ Model: gemma4:latest     │ │
│  └──────────────────────────────────────────────────────┘ └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Features:
- 4 clean KPI cards.
- Real-time incoming safety alert stream powered by Socket.IO (`new_safety_event`).
- One-click navigation to review and resolve escalations.

---

### 4.2 Screen 2: 4-Tier Clinical Safety Triage Board (`/safety-events`)

The core triage center where clinicians review and resolve Amy's safety escalations.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  CLINICAL SAFETY TRIAGE QUEUE                           [Filter: All ▾] [Status: Open] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  🔴 CRITICAL (0)      │ 🟠 HIGH (1)             │ 🟡 MEDIUM (0)       │ 🔵 LOW (1)     │
├───────────────────────┼─────────────────────────┼─────────────────────┼────────────────┤
│ (No active emergencies)│ 👤 Sarah Jenkins       │ (No active pain)    │ 👤 David Miller│
│                       │ Knee Surgery (T-21d)    │                     │ ACL (T-14d)    │
│                       │ "Hit head on floor..."  │                     │ "Flushed pills"│
│                       │ Category: Acute Trauma  │                     │ Category: Meds │
│                       │ Action: Rest + Call 111 │                     │ Action: Doctor │
│                       │ [Triage & Resolve ➔]    │                     │ [Resolve ➔]    │
└───────────────────────┴─────────────────────────┴─────────────────────┴────────────────┘
```

#### Triage & Resolution Drawer:
- Shows the trigger utterance, detected category (`acute_medical`, `severe_pain`, `clinical_decision`, `mental_health`), and recommended action.
- Action checkboxes: `[x] Spoke with patient`, `[ ] Contacted clinic`, `[x] Notified surgeon`.
- Clinician Notes field (saves audit record).
- Button: **[Mark as Resolved]** &rarr; updates status in SQLite from `open` to `resolved`.

---

### 4.3 Screen 3: Escalated Cases & Audited Conversation Inspector (`/conversations`)

Provides transparent visibility into Coach Amy's messages with clinical access reasoning and Langfuse links.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  ESCALATED CASES & AUDITED CHAT INSPECTOR                                              │
├──────────────────────────────────────┬─────────────────────────────────────────────────┤
│  ESCALATED PATIENT THREADS           │  AUDITED THREAD: Sarah Jenkins (Knee Surgery)   │
│  ┌─────────────────────────────────┐ │  Access Reason: Safety Alert #14 (High Risk)    │
│  │ 🔴 Sarah Jenkins (Active Alert) │ │  ┌───────────────────────────────────────────┐  │
│  │    "Hit head on floor..."       │ │  │ 🧑 Sarah (11:32 AM):                       │  │
│  ├─────────────────────────────────┤ │  │    "I hit my head on the floor, should I   │  │
│  │ 🔵 David Miller (Med Issue)     │ │  │    still do my activities?"                │  │
│  │    "Flushed pills in toilet"    │ │  ├───────────────────────────────────────────┤  │
│  ├─────────────────────────────────┤ │  │ 🤖 Amy AI (11:32 AM) [🛡️ Acute Medical]   │  │
│  │ 🔍 [Search Patient to Audit...] │ │  │    "I'm so sorry you experienced this...   │  │
│  │    (Requires Clinical Reason)   │ │  │    Please stop all physical exercises..."  │  │
│  └─────────────────────────────────┘ │  └───────────────────────────────────────────┘  │
│                                      │                                                 │
│                                      │  AI DECISION METRICS                            │
│                                      │  • LangGraph Node: safety_escalation (HIGH)     │
│                                      │  • Activity Cards: Suppressed (Rest enforced)   │
│                                      │  • Langfuse Trace: [🔗 Open in Langfuse (3000)] │
└──────────────────────────────────────┴─────────────────────────────────────────────────┘
```

#### Key Features:
- Displays escalated threads by default.
- If searching for a non-escalated patient, opens a simple **Clinical Reason for Access** modal (*"Routine Review"*, *"Patient Phone Call"*, *"QA Audit"*).
- Direct link to inspect the exact prompt, latency, and tokens in the local Langfuse dashboard.

---

### 4.4 Screen 4: Lightweight Patient Directory (`/patients`)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  PATIENT DIRECTORY                                     [Search Name...] [Filter: All ▾]│
├───────────────────────┬────────────────────┬──────────┬──────────┬───────────┬─────────┤
│ Patient Name          │ Procedure          │ Days Out │ Adherence│ Risk Level│ Action  │
├───────────────────────┼────────────────────┼──────────┼──────────┼───────────┼─────────┤
│ Sarah Jenkins         │ Knee Surgery       │ T - 21d  │ 94% 🟢   │ 🔴 High   │ [Audit] │
│ Mark Davies           │ Total Hip Repl.    │ T + 5d   │ 78% 🟡   │ 🟢 Safe   │ [Audit] │
│ Elena Rostova         │ ACL Reconstruction │ T - 14d  │ 100% 🟢  │ 🟢 Safe   │ [Audit] │
│ David Miller          │ Meniscus Repair    │ T - 7d   │ 85% 🟢   │ 🔵 Low    │ [Audit] │
└───────────────────────┴────────────────────┴──────────┴──────────┴───────────┴─────────┘
```

#### Key Features:
- Clean list of patients with procedure name, surgery countdown pill (`T - 21d`), daily task adherence, and safety risk status.
- Clicking **[Audit]** navigates to their audited conversation view with clinical justification.

---

## 5. State Management with Zustand

Per global coding standards, shared state is managed using lightweight Zustand stores:

```typescript
// Client/web/src/stores/useSafetyTriageStore.ts
import { create } from 'zustand';

export interface SafetyEventItem {
  id: number;
  patient_id?: number;
  patientName?: string;
  conversation_id: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  trigger: string;
  action: string;
  status: 'open' | 'under_review' | 'resolved';
  created_at: string;
}

interface SafetyTriageState {
  events: SafetyEventItem[];
  selectedEvent: SafetyEventItem | null;
  activeFilter: 'all' | 'critical' | 'high' | 'medium' | 'low';
  setEvents: (events: SafetyEventItem[]) => void;
  addEvent: (event: SafetyEventItem) => void;
  resolveEvent: (id: number) => void;
  setSelectedEvent: (event: SafetyEventItem | null) => void;
  setActiveFilter: (filter: 'all' | 'critical' | 'high' | 'medium' | 'low') => void;
}

export const useSafetyTriageStore = create<SafetyTriageState>((set) => ({
  events: [],
  selectedEvent: null,
  activeFilter: 'all',
  setEvents: (events) => set({ events }),
  addEvent: (event) => set((state) => ({ events: [event, ...state.events] })),
  resolveEvent: (id) =>
    set((state) => ({
      events: state.events.map((e) => (e.id === id ? { ...e, status: 'resolved' } : e)),
    })),
  setSelectedEvent: (selectedEvent) => set({ selectedEvent }),
  setActiveFilter: (activeFilter) => set({ activeFilter }),
}));
```

---

## 6. Backend API Contracts

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/admin/dashboard/stats` | `GET` | Aggregated stats: active patients, open alerts, adherence rate. |
| `/api/admin/safety-events` | `GET` | List of safety events across all patients. |
| `/api/admin/safety-events/{id}/resolve` | `POST` | Mark safety event as resolved with clinician notes. |
| `/api/admin/patients` | `GET` | Lightweight list of patients with procedure & risk status. |
| `/api/admin/conversations/escalated` | `GET` | List of conversations currently flagged with safety alerts. |
| `/api/admin/conversations/{id}/messages`| `GET` | Multi-turn message history with access audit logging. |
| `/api/admin/audit-logs` | `POST` | Record access justification log entry. |

---

## 7. Implementation Plan

- [ ] **Step 1: Backend Admin Endpoints**: Add lightweight FastAPI routes in `Server/routes/admin.py` for stats, safety events, patients, and audit logging.
- [ ] **Step 2: Next.js Layout & Navigation**: Create a sleek sidebar layout with active links (`/dashboard`, `/safety-events`, `/conversations`, `/patients`) and Socket.IO listener.
- [ ] **Step 3: Dashboard Screen (`/dashboard`)**: Build KPI cards and real-time alert feed.
- [ ] **Step 4: Safety Events Screen (`/safety-events`)**: Build 4-tier triage queue and resolution drawer.
- [ ] **Step 5: Conversations Screen (`/conversations`)**: Build escalated case inspector with Langfuse trace links and reason modal.
- [ ] **Step 6: Patients Screen (`/patients`)**: Build patient directory table.
- [ ] **Step 7: Verification**: Test real-time synchronization when patient triggers safety alert on mobile client.
