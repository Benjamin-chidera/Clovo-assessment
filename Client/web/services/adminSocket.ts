import { io, Socket } from 'socket.io-client';
import { useSafetyTriageStore, SafetyEventItem } from '../stores/useSafetyTriageStore';

const SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AdminSocketService {
  private socket: Socket | null = null;

  connect() {
    if (this.socket?.connected) return;

    this.socket = io(SERVER_URL, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
    });

    this.socket.on('connect', () => {
      console.log('✅ [Admin Socket] Connected to Clovo Server at', SERVER_URL);
      useSafetyTriageStore.getState().setIsConnected(true);
    });

    this.socket.on('disconnect', () => {
      console.log('❌ [Admin Socket] Disconnected from Clovo Server');
      useSafetyTriageStore.getState().setIsConnected(false);
    });

    this.socket.on('new_safety_event', (data: SafetyEventItem) => {
      console.log('🚨 [Admin Socket] Live Safety Alert Received:', data);
      useSafetyTriageStore.getState().addEvent(data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      useSafetyTriageStore.getState().setIsConnected(false);
    }
  }
}

export const adminSocket = new AdminSocketService();
