import { create } from 'zustand';
import { socketService } from '@/services/socketService';

export interface SocketState {
  isConnected: boolean;
  isConnecting: boolean;
  socketId: string | null;
  connect: (userId: string) => void;
  disconnect: () => void;
  setConnected: (isConnected: boolean, socketId?: string | null) => void;
}

export const useSocketStore = create<SocketState>((set) => ({
  isConnected: false,
  isConnecting: false,
  socketId: null,

  setConnected: (isConnected: boolean, socketId: string | null = null) => {
    set({ isConnected, isConnecting: false, socketId });
  },

  connect: (userId: string) => {
    set({ isConnecting: true });
    const socket = socketService.connect(userId);

    if (socket.connected) {
      set({ isConnected: true, isConnecting: false, socketId: socket.id ?? null });
    }

    socket.on('connect', () => {
      set({ isConnected: true, isConnecting: false, socketId: socket.id ?? null });
    });

    socket.on('disconnect', () => {
      set({ isConnected: false, isConnecting: false, socketId: null });
    });

    socket.on('connect_error', () => {
      set({ isConnected: false, isConnecting: false });
    });
  },

  disconnect: () => {
    socketService.disconnect();
    set({ isConnected: false, isConnecting: false, socketId: null });
  },
}));
