# Specification: Amy Hands-Free Voice Coaching & Multimodal Interaction

**Document Version**: `1.0.0`  
**Feature Name**: Hands-Free Voice Coaching & Cadence Mode (`VoiceCoach`)  
**Target Platform**: Mobile (iOS & Android via Expo SDK 52 / React Native) & Backend (FastAPI + Socket.IO + LangGraph)  
**Status**: Ready for Implementation / Architecture Defense  

---

## 1. Executive Summary & Clinical Context

### 1.1 The Clinical Problem
During pre- and post-operative recovery, patients face fatigue, joint stiffness, lying down during bed routines, and physical mobility limitations. Asking a patient to type on a small touch keyboard while performing exercises (e.g. *Quad Sets* or *4-7-8 Breathing*) breaks focus, increases cognitive load, and reduces adherence.

### 1.2 The Solution
Introduce a **Voice Communication Mode** triggered via a top-right **Voice Coaching Icon** in the header of the Amy Coach screen. This provides:
1. **Hands-Free Conversational Coaching**: Patients can speak directly to Amy (e.g. *"I'm done with quad sets"*, *"What should I do next?"*, *"I have knee soreness"*).
2. **Real-Time Spoken Cadence & Countdowns**: Amy speaks exercise instructions aloud with live pacing (e.g., counting 4-7-8 breathing seconds aloud).
3. **Seamless Multi-Modal Fallback**: Voice interactions pass through the exact same **6-Node LangGraph Deterministic Safety Pipeline** (`safety_triage` ➔ `intent_classification` ➔ `recommendation_action` ➔ `coaching` ➔ `response_validation`).

---

## 2. UI & Interaction Design Specification

### 2.1 Header Placement & Icon Specification
- **Location**: Right side of [`CoachHeader.tsx`](file:///Users/benjaminchidera/Desktop/Clovo/Client/mobile/src/components/chat/CoachHeader.tsx), directly opposite the back button and aligned with the `Amy - Recovery Coach` title.
- **Icon Visuals & States**:
  1. **Idle / Inactive State**:
     - Circular pill button (`36x36 dp`), subtle background (`#F3F4F6`), border (`#E5E7EB`).
     - Icon: `Ionicons` name `mic-outline` or `volume-high-outline` in Royal Blue (`#3B49DF`).
     - Tooltip / Accessibility Label: *"Enable Voice Mode"*.
  2. **Active Listening State (Recording)**:
     - Background: Soft Indigo Pulse (`#EEF2FF`), border (`#818CF8`).
     - Icon: `mic` (solid) in `#4F46E5` with an animated pulsing ripple effect (scale 1.0 ➔ 1.15).
     - Status subtitle under Amy switches from `• Active` to `🎙️ Listening...` in `#3B49DF`.
  3. **Amy Speaking State (TTS Active)**:
     - Icon: Animated sound wave bars or `volume-high` in Emerald Green (`#10B981`).
     - Status subtitle switches to `🔊 Amy is speaking...` in `#10B981`.

```
┌──────────────────────────────────────────────────────────────────┐
│  [↖]   (Avatar) Amy - Recovery Coach              [ 🎙️ / 🔊 ]    │
│                 • Active / Listening...             (Top-Right)  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Technical Architecture & Data Flow

```
                              [ PATIENT SPEAKS ]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Speech-to-Text (STT)      │
                        │ (On-Device Apple/Android  │
                        │  or Whisper API over WS)  │
                        └─────────────┬─────────────┘
                                      │
                                      ▼ (Transcript: "I just finished quad sets")
                        ┌───────────────────────────┐
                        │    Socket.IO Gateway      │
                        │   event: "user_voice_msg" │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   LangGraph Pipeline      │
                        │ 1. safety_triage          │
                        │ 2. intent_classification  │
                        │ 3. recommendation_action  │
                        │ 4. coaching               │
                        │ 5. response_validation    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼ (Validated Plain-Text Response)
                        ┌───────────────────────────┐
                        │ Text-to-Speech (TTS)      │
                        │ (Expo Speech / ElevenLabs)│
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                      [ AMY SPEAKS ALOUD TO PATIENT ]
```

---

## 4. Component & Store Design

### 4.1 Global Voice Store (`useVoiceStore.ts`)
```typescript
interface VoiceState {
  isVoiceModeEnabled: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  transcript: string;
  voiceVolume: number; // For audio wave visualization (0.0 to 1.0)
  autoReadResponses: boolean; // Automatically speak Amy's replies
  
  toggleVoiceMode: () => void;
  startListening: () => Promise<void>;
  stopListening: () => Promise<void>;
  speakText: (text: string) => Promise<void>;
  stopSpeaking: () => void;
}
```

### 4.2 Header Integration in `CoachHeader.tsx`
```tsx
{/* Top-Right Voice Mode Action Button */}
<TouchableOpacity
  className={`w-9 h-9 rounded-full justify-center items-center ${
    isListening 
      ? 'bg-red-50 border border-red-300' 
      : isVoiceModeEnabled 
      ? 'bg-indigo-50 border border-indigo-200' 
      : 'bg-gray-100 border border-gray-200'
  }`}
  onPress={toggleVoiceMode}
  accessibilityRole="button"
  accessibilityLabel="Toggle hands-free voice coach mode"
>
  <Ionicons
    name={isListening ? 'mic' : isVoiceModeEnabled ? 'volume-high' : 'mic-outline'}
    size={18}
    color={isListening ? '#EF4444' : isVoiceModeEnabled ? '#3B49DF' : '#6B7280'}
  />
</TouchableOpacity>
```

---

## 5. Clinical Safety & SaMD Compliance Rules for Voice

1. **Deterministic Safety Firewall Before TTS**:
   - Voice transcriptions are fed into **Node 1 (`safety_triage`)** before anything else.
   - If an acute red flag is detected (e.g. *"I'm bleeding from the cut"*), Amy **immediately switches tone**, speaks a clear emergency directive, and displays the red emergency banner on screen.
2. **Auditory Fallback & Non-Prescriptive Speech**:
   - All spoken text passes through **Node 6 (`response_validation`)** before TTS audio generation, guaranteeing zero hallucinated dosages or diagnostic claims in spoken audio.
3. **Visual Confirmation Bubble**:
   - Every voice transcription and spoken reply is simultaneously rendered as a message bubble in the chat thread so the patient can visually verify what Amy understood.

---

## 6. Implementation Milestones

| Milestone | Deliverables | Target Timeline |
| :--- | :--- | :--- |
| **M1: UI Header Controls** | Add Voice Icon to `CoachHeader.tsx` with active/listening pill states and haptic feedback. | Immediate |
| **M2: Client-Side Audio TTS** | Implement `expo-speech` in `useVoiceStore` to read Amy's responses aloud with smooth British English voice (`en-GB`). | Sprint 1 |
| **M3: Hands-Free STT Ingestion** | Integrate on-device Speech Recognition (`expo-speech-recognition` / Web Speech API) to pipe speech to text. | Sprint 2 |
| **M4: Streaming Exercise Cadence** | Audio countdown cues for *4-7-8 Breathing* and repetition pacing for *Quad Sets*. | Sprint 3 |
