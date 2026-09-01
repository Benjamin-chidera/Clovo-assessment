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

let isSocketListenerAttached = false;

export const useSocketStore = create<SocketState>((set) => ({
  isConnected: false,
  isConnecting: false,
  socketId: null,

  setConnected: (isConnected: boolean, socketId: string | null = null) => {
    set({ isConnected, isConnecting: false, socketId });
  },

  connect: (userId: string) => {
    const socket = socketService.connect(userId);
    set({
      isConnected: socket.connected,
      isConnecting: !socket.connected,
      socketId: socket.id ?? null,
    });

    if (!isSocketListenerAttached) {
      isSocketListenerAttached = true;

      socket.on('connect', () => {
        set({ isConnected: true, isConnecting: false, socketId: socket.id ?? null });
      });

      socket.on('disconnect', () => {
        set({ isConnected: false, isConnecting: false, socketId: null });
      });

      socket.on('connect_error', () => {
        set({ isConnected: false, isConnecting: false });
      });
    }
  },

  disconnect: () => {
    socketService.disconnect();
    isSocketListenerAttached = false;
    set({ isConnected: false, isConnecting: false, socketId: null });
  },
}));
