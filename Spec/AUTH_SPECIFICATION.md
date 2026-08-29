# Clovo Mobile App — Authentication & Session Specification

## 1. Overview & Goal
This specification defines a streamlined, seamless authentication flow for the Clovo mobile application. The experience emphasizes instant entry, clear session feedback, and accessible profile actions:

1. **Login Screen (`/login` or `/(auth)/login`)**: Minimalist, clean brand-aligned screen featuring a primary **Login** action button that authenticates the user and transitions smoothly into the main app experience (`Home` screen).
2. **Home Screen Profile Switcher & Logout Modal**: Tapping the existing `swap-horizontal` button on the top-right of the Home Screen hero banner opens an elevated Profile / Account Action Sheet modal containing user details, switch profile options, and a clear **Log Out** button.
3. **Session Termination**: Tapping **Log Out** clears session state and resets navigation back to the Login screen.

---

## 2. Navigation & Route Architecture

```
App Auth & Navigation Hierarchy
├── (auth)
│   └── login.tsx (Minimalist Login View with Brand Header & One-Tap Login CTA)
└── (tabs)
    ├── _layout.tsx (Protected Tab Navigator with auth state gating)
    ├── index.tsx (Home Tab with swap-horizontal trigger & Profile/Logout Modal)
    └── chat.tsx (Coach Chat Tab)
```

### 2.1 Route Protection & Transition Matrix
| Source Route | Trigger / Condition | Target Route | Transition Animation |
| :--- | :--- | :--- | :--- |
| `/(auth)/login` | Press "Log In" Button | `/(tabs)/index` | Smooth Crossfade / Slide Up |
| `/(tabs)/index` | Press `swap-horizontal` | Profile Action Sheet Modal | Slide up from bottom (iOS Sheet) |
| Profile Modal | Press "Log Out" Button | `/(auth)/login` | Instant Reset / Replace Route |

---

## 3. UI & Component Specifications

### 3.1 Login Screen (`/(auth)/login`)

#### A. Layout & Visual Elements
- **Background**: Modern soft lavender surface (`#F8F9FD`) with subtle brand decorative accents.
- **Brand Hero Area**:
  - Clovo Logo / Starburst Icon (`#3B49DF` Royal Blue with soft glow).
  - App Name: **CLOVO** (`28pt`, Bold, Letter Spacing `2px`).
  - Subtitle: *"Personalized Wellness & Recovery Coaching"*.
- **Primary Action (Log In)**:
  - Full-width royal blue button (`#3B49DF`) with capsule corner radius (`9999px`).
  - Label: **"Log In"** (`17pt`, Bold, White text).
  - Tap interaction: Scale down `0.97` + Light Haptic feedback (`Haptics.impactAsync(ImpactFeedbackStyle.Light)`).
  - On tap: Sets `isAuthenticated: true` in `useAuthStore` and redirects to `/(tabs)`.

---

### 3.2 Home Screen Profile & Logout Modal

#### A. Trigger
- **Location**: Top-right corner of the Home Screen `HeroBanner` component.
- **Icon**: `swap-horizontal` (Ionicons) inside a translucent glassmorphic circle.
- **Action**: Opens the `ProfileModal` state in `useAuthStore` or local modal controller.

#### B. Modal / Bottom Sheet Design
- **Container**: iOS-style rounded bottom sheet / centered card with backdrop overlay (`rgba(0, 0, 0, 0.45)`).
- **Header**:
  - User Avatar (e.g. portrait photo for "Jen").
  - User Name: **Jen** (`20pt`, Semi-Bold).
  - User Email / Status: `jen@clovo.app · Active Member`.
- **Action Items**:
  - **Switch Account / Profile**: Option to switch between family/wellness profiles.
  - **Preferences / Settings**: Quick link to notification & coaching preferences.
  - **Log Out Button**:
    - Prominent red/destructive or styled secondary button (`#EF4444` / `#DC2626` accent).
    - Left icon: `log-out-outline` (Ionicons).
    - Label: **"Log Out"**.
- **Close Action**: Backdrop tap or "Cancel" / "Dismiss" pill button.

---

## 4. State Management Architecture (Zustand)

Authentication state is managed globally using Zustand in `src/stores/useAuthStore.ts`:

### 4.1 `useAuthStore` Interface
```typescript
export interface AuthUser {
  id: string;
  name: string;
  email: string;
  avatarUri: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  isProfileModalOpen: boolean;
  
  // Actions
  login: () => void;
  logout: () => void;
  openProfileModal: () => void;
  closeProfileModal: () => void;
}
```

### 4.2 State Reducers & Logic
- `login()`: Sets `isAuthenticated: true`, loads default user profile (`Jen`), closes modals, and triggers router redirect to `/`.
- `logout()`: Sets `isAuthenticated: false`, resets active chat selections if needed, closes modal, and redirects to `/login`.
- `openProfileModal()` / `closeProfileModal()`: Controls visibility of the profile action sheet.

---

## 5. Security & Session Guidelines

1. **Session Clearing**: Upon logging out, any temporary in-memory tokens or cached sensitive states are cleared.
2. **Safe Navigation Guard**: Unauthenticated users are redirected to `/(auth)/login` if attempting to access protected routes.
3. **Accessibility**: All interactive buttons provide explicit `accessibilityRole="button"` and meaningful `accessibilityLabel` attributes.

---

## 6. Implementation Checklist

- [ ] **Auth Store (`useAuthStore.ts`)**: Implement Zustand store for authentication state and modal toggles.
- [ ] **Login Screen (`src/app/login.tsx`)**: Build the brand login screen with one-tap Log In CTA.
- [ ] **Profile & Logout Modal (`src/components/home/ProfileModal.tsx`)**: Create the popup modal with user details and Log Out action.
- [ ] **Wire `HeroBanner` Trigger**: Connect the `swap-horizontal` button to open the Profile Modal.
- [ ] **Protected Route Navigation**: Configure root layout redirection based on `isAuthenticated`.
