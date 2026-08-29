import { io, Socket } from 'socket.io-client';
import { getBackendUrl } from '@/services/api';

type MessageListener = (data: any) => void;

class SocketService {
  private socket: Socket | null = null;
  private coachMessageListeners: MessageListener[] = [];

  public isConnected(): boolean {
    return Boolean(this.socket && this.socket.connected);
  }

  public connect(userId: string): Socket {
    if (this.socket && this.socket.connected) {
      return this.socket;
    }

    const serverUrl = getBackendUrl();
    console.log('🔌 [Socket.IO] Connecting to:', serverUrl);

    this.socket = io(serverUrl, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      auth: {
        userId,
      },
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      timeout: 20000,
    });

    this.socket.on('connect', () => {
      console.log('✅ [Socket.IO] Connected to Clovo Server. ID:', this.socket?.id);
    });

    this.socket.on('coach_message', (data: any) => {
      console.log('🤖 [Socket.IO] Received coach_message:', data);
      this.coachMessageListeners.forEach((listener) => listener(data));
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ [Socket.IO] Disconnected from server. Reason:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.warn('⚠️ [Socket.IO] Connection error:', error.message);
    });

    return this.socket;
  }

  public onCoachMessage(callback: MessageListener): () => void {
    this.coachMessageListeners.push(callback);
    return () => {
      this.coachMessageListeners = this.coachMessageListeners.filter((cb) => cb !== callback);
    };
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  public getSocket(): Socket | null {
    return this.socket;
  }

  public emit(event: string, data: any): void {
    if (!this.socket || !this.socket.connected) {
      this.connect('1');
    }
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export const socketService = new SocketService();
