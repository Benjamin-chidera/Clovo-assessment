import { create } from 'zustand';
import { useSocketStore } from '@/stores/useSocketStore';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  avatarUri: string;
  plan: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  isProfileModalOpen: boolean;
  login: () => void;
  logout: () => void;
  openProfileModal: () => void;
  closeProfileModal: () => void;
}

const DEFAULT_USER: AuthUser = {
  id: 'patient-sarah',
  name: 'Sarah',
  email: 'sarah@clovo.app',
  avatarUri: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
  plan: 'Pre-Op Preparation',
};

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: DEFAULT_USER,
  isProfileModalOpen: false,

  login: () => {
    // Initiate Socket.IO connection immediately upon login
    useSocketStore.getState().connect(DEFAULT_USER.id);

    set({
      isAuthenticated: true,
      user: DEFAULT_USER,
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
