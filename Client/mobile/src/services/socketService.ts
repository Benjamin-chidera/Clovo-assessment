import { io, Socket } from 'socket.io-client';
import { getBackendUrl } from '@/services/api';

type MessageListener = (data: any) => void;

class SocketService {
  private socket: Socket | null = null;
  private coachMessageListeners: MessageListener[] = [];
  private taskSyncListeners: MessageListener[] = [];

  /**
   * Track which socket instance has listeners attached to avoid duplicates
   * but ensure we re-attach when the socket instance changes.
   */
  private attachedSocketId: string | null = null;

  public isConnected(): boolean {
    return Boolean(this.socket && this.socket.connected);
  }

  public connect(userId: string): Socket {
    // If already connected with the same socket, just return it
    if (this.socket && this.socket.connected) {
      // Ensure listeners are attached even on early return
      this.ensureListenersAttached();
      return this.socket;
    }

    // Disconnect stale socket before creating a new one
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
      this.attachedSocketId = null;
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

    // Attach all internal event forwarders to this new socket instance
    this.attachedSocketId = null; // Force re-attach
    this.ensureListenersAttached();

    return this.socket;
  }

  /**
   * Attach socket-level event listeners that forward to registered callbacks.
   * Idempotent: only attaches once per socket instance (tracked by an internal key).
   * Must be called after this.socket is set.
   */
  private ensureListenersAttached(): void {
    if (!this.socket) return;

    // Use a stable internal tag to track whether we already attached to this
    // exact socket object. socket.id is undefined until the connect event fires,
    // so we tag the instance ourselves.
    const instanceKey = (this.socket as any)._instanceKey;
    if (!instanceKey) {
      (this.socket as any)._instanceKey = `sock_${Date.now()}`;
    }

    const currentKey = (this.socket as any)._instanceKey;
    if (this.attachedSocketId === currentKey) {
      return; // Already attached to this exact socket instance
    }

    this.attachedSocketId = currentKey;

    this.socket.on('connect', () => {
      console.log('✅ [Socket.IO] Connected to Clovo Server. ID:', this.socket?.id);
    });

    this.socket.on('coach_message', (data: any) => {
      console.log('🤖 [Socket.IO] Received coach_message:', data);
      this.coachMessageListeners.forEach((listener) => listener(data));
    });

    this.socket.on('task_sync', (data: any) => {
      console.log('📋 [Socket.IO] Received task_sync:', data);
      if (data.streakCount !== undefined || data.milestones !== undefined) {
        import('@/stores/useUserStore').then(({ useUserStore }) => {
          useUserStore.getState().updateStats({
            streakCount: data.streakCount,
            milestones: data.milestones,
            additionalMilestonesCount: data.additionalMilestonesCount,
          });
        });
      }
      this.taskSyncListeners.forEach((listener) => listener(data));
    });

    this.socket.on('user_stats_updated', (data: any) => {
      console.log('🌟 [Socket.IO] Received user_stats_updated:', data);
      import('@/stores/useUserStore').then(({ useUserStore }) => {
        useUserStore.getState().updateStats({
          streakCount: data.streakCount,
          milestones: data.milestones,
          additionalMilestonesCount: data.additionalMilestonesCount,
        });
      });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ [Socket.IO] Disconnected from server. Reason:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.warn('⚠️ [Socket.IO] Connection error:', error.message);
    });
  }

  public onCoachMessage(callback: MessageListener): () => void {
    this.coachMessageListeners.push(callback);
    return () => {
      this.coachMessageListeners = this.coachMessageListeners.filter((cb) => cb !== callback);
    };
  }

  public onTaskSync(callback: MessageListener): () => void {
    this.taskSyncListeners.push(callback);
    return () => {
      this.taskSyncListeners = this.taskSyncListeners.filter((cb) => cb !== callback);
    };
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
      this.attachedSocketId = null;
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
