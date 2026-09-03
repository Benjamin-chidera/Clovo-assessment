import { create } from 'zustand';
import { useSocketStore } from '@/stores/useSocketStore';
import { useUserStore } from '@/stores/useUserStore';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  avatarUri: string;
  plan: string;
  phase: 'pre-op' | 'post-op';
  procedureName: string;
  stageBadge: string;
}

export const PRE_OP_USER: AuthUser = {
  id: 'patient-sarah',
  name: 'Sarah',
  email: 'sarah@clovo.app',
  avatarUri: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
  plan: 'Pre-Op Preparation',
  phase: 'pre-op',
  procedureName: 'Knee Surgery',
  stageBadge: 'Pre-Op Preparation',
};

export const POST_OP_USER: AuthUser = {
  id: 'patient-jane',
  name: 'Jane',
  email: 'jane@clovo.app',
  avatarUri: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80',
  plan: 'Post-Op Rehabilitation',
  phase: 'post-op',
  procedureName: 'Knee Replacement',
  stageBadge: 'Day 6 Post-Op Rehab',
};

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  isProfileModalOpen: boolean;
  login: (user?: AuthUser) => void;
  switchUser: (user: AuthUser) => void;
  logout: () => void;
  openProfileModal: () => void;
  closeProfileModal: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: PRE_OP_USER,
  isProfileModalOpen: false,

  login: (selectedUser = PRE_OP_USER) => {
    // Initiate Socket.IO connection immediately upon login
    useSocketStore.getState().connect(selectedUser.id);

    // Immediately sync user store to prevent stale UI
    useUserStore.setState({
      id: selectedUser.id,
      name: selectedUser.name,
      email: selectedUser.email,
      avatarUri: selectedUser.avatarUri,
      plan: selectedUser.plan,
      phase: selectedUser.phase,
      procedureName: selectedUser.procedureName,
      surgeryTitle: selectedUser.phase === 'post-op' ? 'Post-Op Rehabilitation' : 'Your surgery',
      daysAway: selectedUser.phase === 'post-op' ? 0 : 21,
      daysPostOp: selectedUser.phase === 'post-op' ? 6 : undefined,
    });

    set({
      isAuthenticated: true,
      user: selectedUser,
      isProfileModalOpen: false,
    });
  },

  switchUser: (selectedUser: AuthUser) => {
    // Reconnect socket to new user session
    useSocketStore.getState().disconnect();
    useSocketStore.getState().connect(selectedUser.id);

    // Immediately sync user store to prevent stale UI
    useUserStore.setState({
      id: selectedUser.id,
      name: selectedUser.name,
      email: selectedUser.email,
      avatarUri: selectedUser.avatarUri,
      plan: selectedUser.plan,
      phase: selectedUser.phase,
      procedureName: selectedUser.procedureName,
      surgeryTitle: selectedUser.phase === 'post-op' ? 'Post-Op Rehabilitation' : 'Your surgery',
      daysAway: selectedUser.phase === 'post-op' ? 0 : 21,
      daysPostOp: selectedUser.phase === 'post-op' ? 6 : undefined,
    });

    set({
      user: selectedUser,
      isAuthenticated: true,
      isProfileModalOpen: false,
    });
  },

  logout: () => {
    // Disconnect and clean up socket session
    useSocketStore.getState().disconnect();

    set({
      isAuthenticated: false,
      isProfileModalOpen: false,
    });
  },

  openProfileModal: () => {
    set({ isProfileModalOpen: true });
  },

  closeProfileModal: () => {
    set({ isProfileModalOpen: false });
  },
}));
