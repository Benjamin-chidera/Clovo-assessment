import { io, Socket } from 'socket.io-client';
import { Platform } from 'react-native';

// Default localhost URL based on runtime platform (10.0.2.2 for Android emulator, localhost for iOS/web)
const SERVER_URL =
  Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

class SocketService {
  private socket: Socket | null = null;

  public connect(userId: string): Socket {
    if (this.socket && this.socket.connected) {
      return this.socket;
    }

    this.socket = io(SERVER_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      auth: {
        userId,
      },
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect', () => {
      console.log('✅ [Socket.IO] Connected to Clovo Server. ID:', this.socket?.id);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ [Socket.IO] Disconnected from server. Reason:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.warn('⚠️ [Socket.IO] Connection error:', error.message);
    });

    return this.socket;
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
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    }
  }
}

export const socketService = new SocketService();
