# Clovo Mobile App — UI/UX & Functional Specification

## 1. Overview & Vision
**Clovo** is a personalized wellness and recovery coaching mobile application designed to guide users through daily wellness check-ins, adaptive recovery routines, and goal tracking.

The application features a modern, clean, and engaging iOS-native interface centered around a streamlined **2-Tab Architecture**:
1. **Home Screen (`/` or `/(tabs)/index`)**: Daily dashboard featuring milestone achievements, streak tracking, personalized greetings, daily tasks, and direct check-in prompts.
2. **Chat Screen (`/(tabs)/chat`)**: Interactive AI recovery coaching thread with **Amy** (Recovery Coach), supporting conversation bubbles, status indicators, and rich interactive recovery activity cards.

---

## 2. Navigation & Information Architecture

### 2.1 Tab Navigation (2 Tabs)
The bottom navigation bar persists across both primary screens with custom floating elevated styling:

| Tab | Route | Icon | Purpose |
| :--- | :--- | :--- | :--- |
| **Home** | `/(tabs)/index` | Outlined/Filled Home icon | Daily overview, streaks, hero banner, pending tasks |
| **Coach Chat** | `/(tabs)/chat` | Clovo Brand Starburst / Chat icon | Direct conversational check-in and interactive recovery cards |

```
App Navigation Hierarchy
├── (tabs)
│   ├── index.tsx (Home Tab)
│   │   ├── Hero Photo Banner & Header
│   │   ├── User Greeting & Achievement Stack
│   │   ├── Streak Indicator Pill
│   │   ├── "Check in with Amy" Primary CTA Button
│   │   ├── Milestone Streak Card
│   │   └── Pending Daily Tasks List / Carousels
│   └── chat.tsx (Coach Chat Tab)
│       ├── Coach Header (Avatar, Name, Active Badge, Back Button)
│       ├── Chat Message Thread (User & Coach Bubbles)
│       ├── Interactive Recovery Activity Cards
│       └── Chat Input Bar & Send Button
```

---

## 3. Design System & Theme Tokens

### 3.1 Color Palette
- **Primary / Brand Accent**: `#3B49DF` (Vibrant Royal Blue / Indigo)
- **Primary Dark / Pressed**: `#2B38C6`
- **Primary Light / Background Tint**: `#EEF2FF`
- **Streak Accent**: `#FF6B00` / `#F97316` (Vibrant Flame Orange)
- **Surface Background**: `#F8F9FD` (Off-white / Soft lavender background)
- **Card Background**: `#FFFFFF` (Pure White with subtle elevation `#0000000A`)
- **Dark Texture Card**: `#2C2C2E` / `#1C1C1E` (Charcoal dark card with subtle sheen)
- **Text Primary**: `#111827` (Deep Slate / Black)
- **Text Secondary**: `#6B7280` (Muted Neutral Gray)
- **Text On-Primary**: `#FFFFFF` (Crisp White)
- **Online / Active Indicator**: `#34D399` / `#10B981` (Emerald Green)
- **Border / Divider**: `#E5E7EB` (Subtle 1px border)

### 3.2 Typography Hierarchy
- **Header Greeting**: `34pt`, Bold, Tracking `-0.5px` (`Jen`)
- **Section Headers**: `20pt`, Semi-Bold (`Pending Daily Tasks`)
- **Card Titles / Activity Names**: `16pt`, Semi-Bold (`Gentle Stretching – Release Tension`)
- **Body / Chat Messages**: `15pt`, Regular, Line Height `22pt`
- **Subtext / Meta Chips**: `13pt`, Medium (`10 minutes · Low`)
- **Badges & Pills**: `12pt`, Semi-Bold, Letter Spacing `0.2px`

### 3.3 Radii & Elevation
- **Card Corner Radius**: `24px` (Rounded modern cards)
- **Pill / Button Corner Radius**: `9999px` (Full rounded capsules)
- **Input Corner Radius**: `24px`
- **Hero Image Corner Radius**: `32px` (Bottom curved corners)
- **Card Shadow**: `box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.04)`

---

## 4. Screen Specifications

### 4.1 Home Screen (`/(tabs)/index`)

#### A. Hero Banner Header
- **Visual**: Top card containing high-quality warm lifestyle/family landscape imagery.
- **Top Bar Overlay**:
  - Translucent glassmorphic button on top right (`⇄` / settings switch icon) for switching profiles or quick settings.
  - Safe area inset padding for iOS dynamic island / status bar.
- **Corner Style**: Rounded bottom edge seamlessly transitioning into the page.

#### B. Greeting & Streak Section
- **Greeting Text**: "Good morning," in soft brand indigo (`#434190`) + User Name **"Jen"** in `34pt` bold typography.
- **Activity / Milestone Stack (Top Right)**:
  - Horizontal overlapping circular milestone badges:
    - Yoga milestone avatar
    - 5K run achievement avatar
    - Core strength badge
    - `+3` additional achievements counter badge
- **Streak Pill**:
  - Blue capsule badge: `🔥 5 day streak` with vibrant flame icon.

#### C. Primary Action ("Check in with Amy")
- **Prompt**: "Let’s make today a good one—start your check-in now!"
- **Primary CTA Button**:
  - Full-width vibrant royal blue button (`#3B49DF`).
  - Left icon: White circular badge with diagonal arrow `↗`.
  - Label: **"Check in with Amy"**.
  - Interaction: Direct smooth navigation to the Chat tab with pre-loaded check-in context.

#### D. Milestone Announcement Card
- **Background**: Dark charcoal textured glass card with subtle line patterning.
- **Content**: `"Jen, you've just hit a 5 day streak! That's incredible—keep going! 🔥"`.
- **Action**: Right-aligned circular chevron button `>` to view streak breakdown and badges.

#### E. Pending Daily Tasks Section
- **Heading**: `"Pending Daily Tasks"`.
- **List / Card Items**:
  - Morning Hydration Check-in (Completed / Pending).
  - 10-Minute Recovery Movement.
  - Evening Mindset Reflection.
- **Visual**: Rounded white cards with progress check circles and duration tags.

---

### 4.2 Chat Screen — Recovery Coach Amy (`/(tabs)/chat`)

#### A. Coach Header Navigation Bar
- **Back / Dismiss Action**: Left circular button with `↖` arrow.
- **Coach Profile Avatar**: Circular portrait of Amy with green `• Active` status badge.
- **Coach Title**: **Amy - Recovery Coach** (Bold `16pt`).
- **Status Indicator**: `Active` in emerald green (switches to `🎙️ Listening...` or `🔊 Speaking...` during voice mode).
- **Top-Right Voice Action Button**: Circular action button on the far right (`36x36 dp`) with `Ionicons` `mic-outline` / `volume-high` for hands-free voice coaching mode.


#### B. Message Thread Area
- **Timestamp Labels**: Centered subtle timestamps (e.g. `9:41 AM`).
- **User Message Bubble**:
  - Right-aligned.
  - Background: Royal Blue (`#3B49DF`).
  - Text: White (`#FFFFFF`).
  - Sample: *"It’s a little lower than normal. Let’s do it, but nothing intense."*
- **Coach Message Bubble**:
  - Left-aligned.
  - Background: White Card (`#FFFFFF`) with subtle shadow.
  - Text: Slate (`#1F2937`).
  - Sample: *"Great attitude! Since today's a low-energy day, I've switched up your options to keep things light. Pick what feels best—something to stretch, move, or just reset. 💙"*

#### C. Interactive Recovery Recommendation Cards
Interactive selectable cards presented dynamically in the chat flow:

1. **Gentle Stretching – Release Tension**
   - Thumbnail: Stretching photo.
   - Meta: `⏱ 10 minutes · 💪 Low`.
2. **Recovery Walk – Shake Off Soreness**
   - Thumbnail: Outdoor nature path walking photo.
   - Meta: `⏱ 30 minutes · 💪 Low`.
3. **Yoga for Beginners – Recovery Basics**
   - Thumbnail: Yoga mat & gentle posing.
   - Meta: `⏱ 20 minutes · 💪 Low`.
4. **Surprise Me! 🎁**
   - Thumbnail: Pink gift box with golden ribbon.
   - Subtext: *"Let’s See What You Get"*.

- **Card Tap Interaction**:
  - Tapping a card highlights it with a blue selection border.
  - Triggers confirmation action or opens routine guided timer view.
  - Sends automated confirmation message into the chat thread.

#### D. Bottom Chat Input Bar
- **Input Container**: Full-width rounded white pill container.
- **Placeholder**: `"Type your message..."`.
- **Send Button**: Right circular royal blue button with arrow icon (`➤`).
- **Quick Reply Chips**: Horizontal scrollable chips for fast feedback (e.g. *"Sounds good!"*, *"I only have 5 mins"*, *"Show more options"*).

---

### 4.3 Custom 2-Tab Bar Component

- **Layout**: Floating bar with safe area padding.
- **Tab 1 (Home)**:
  - Active: Vibrant filled circular blue pill with white home icon.
  - Inactive: Clean minimalist outline home icon.
- **Tab 2 (Coach / Chat)**:
  - Elevated center badge / starburst logo button.
  - Active: Vibrant blue icon with glow effect.
  - Inactive: Outline chat / starburst icon.

---

## 5. State Management & Data Architecture (Zustand)

All shared application state will be structured in modular Zustand stores conforming to project standards:

### 5.1 `useUserStore`
```typescript
interface UserProfile {
  name: string;
  greeting: string;
  streakCount: number;
  completedDays: number[];
  badges: Array<{ id: string; title: string; icon: string }>;
}
```

### 5.2 `useChatStore`
```typescript
interface Message {
  id: string;
  sender: 'user' | 'coach';
  text: string;
  timestamp: string;
  options?: ActivityCard[];
}

interface ActivityCard {
  id: string;
  title: string;
  subtitle?: string;
  durationMinutes: number;
  intensity: 'Low' | 'Medium' | 'High';
  imageUri: string;
  isSpecial?: boolean;
}
```

### 5.3 `useTaskStore`
```typescript
interface DailyTask {
  id: string;
  title: string;
  category: 'hydration' | 'recovery' | 'mindset';
  duration: string;
  isCompleted: boolean;
}
```

---

## 6. Micro-Interactions & Animation Guidelines
1. **Button Taps**: Subtle scale down (`scale: 0.97`) with light haptic feedback (`Haptics.impactAsync(ImpactFeedbackStyle.Light)`).
2. **Activity Card Selection**: Smooth scale & border color interpolation to primary blue.
3. **Chat Message Entry**: Staggered fade-in & slide-up transition (`entering={FadeInDown.springify()}`).
4. **Streak Badge Flame**: Gentle pulse animation on mount.

---

## 7. Deliverables & Implementation Checklist
- [ ] **Tab Navigation Structure**: Configure Expo Router `_layout.tsx` and custom 2-tab navigation bar.
- [ ] **Design Tokens & Assets**: Extract and bundle images (hero family photo, coach Amy avatar, exercise cards, badges).
- [ ] **Home Screen Components**:
  - [ ] Hero Banner with blur/glassmorphic action button
  - [ ] Greeting & Badges Stack
  - [ ] Streak Pill & Dark Milestone Banner
  - [ ] Primary "Check in with Amy" CTA
  - [ ] Pending Daily Tasks List
- [ ] **Chat Screen Components**:
  - [ ] Coach Top Header with Active status indicator
  - [ ] Chat ScrollView with user & coach message bubbles
  - [ ] Rich Recovery Activity Selection Cards
  - [ ] Fixed Bottom Input Bar & Send Action
- [ ] **State & Interaction Hooks**: Zustand stores with mock data and interactive state transitions.
