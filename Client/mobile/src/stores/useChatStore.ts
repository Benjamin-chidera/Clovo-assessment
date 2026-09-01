import { create } from 'zustand';
import { socketService } from '@/services/socketService';
import { apiClient } from '@/services/api';

export interface ActivityCard {
  id: string;
  title: string;
  subtitle?: string;
  durationMinutes?: number;
  durationLabel?: string;
  intensity?: 'Low' | 'Medium' | 'High';
  imageUri: string;
  isSpecial?: boolean;
  tag?: string;
  isCompleted?: boolean;
  recommendationId?: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'coach';
  text: string;
  timestamp: string;
  options?: ActivityCard[];
  selectedOptionId?: string;
  isSafetyAlert?: boolean;
  riskLevel?: 'critical' | 'high' | 'medium' | 'low';
  quickReplies?: string[];
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isTyping: boolean;
  selectedCardId: string | null;
  quickReplies: string[];
  fetchMessages: (patientId?: number) => Promise<void>;
  sendMessage: (text: string, patientId?: number) => Promise<void>;
  selectActivity: (card: ActivityCard) => void;
  addIncomingMessage: (message: ChatMessage) => void;
  setQuickReplies: (replies: string[]) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  isTyping: false,
  selectedCardId: null,
  quickReplies: [
    "What's my plan for today? 📋",
    "I'm feeling a bit tired today 🥱",
    "Why do I need to prepare? 💡",
    "Surprise me! 🎁",
  ],

  setQuickReplies: (replies: string[]) => {
    if (replies && replies.length > 0) {
      set({ quickReplies: replies });
    }
  },

  fetchMessages: async (patientId?: number) => {
    try {
      set({ isLoading: true });
      const url = patientId
        ? `/api/conversations/messages?patient_id=${patientId}`
        : '/api/conversations/messages';
      const response = await apiClient.get<ChatMessage[]>(url);
      if (response.data && Array.isArray(response.data)) {
        console.log(`📥 [Chat Store] Loaded ${response.data.length} messages from SQLite database`);
        set({ messages: response.data, isLoading: false });
      }
    } catch (error) {
      console.warn('⚠️ [Chat Store] Error fetching conversation history from backend:', error);
      set({ isLoading: false });
    }
  },

  addIncomingMessage: (message: ChatMessage) => {
    set((state) => {
      // Update contextual quick replies if message came with new dynamic suggestions
      const updatedQuickReplies =
        message.quickReplies && message.quickReplies.length > 0
          ? message.quickReplies
          : state.quickReplies;

      // Prevent duplicate messages by id or exact match
      if (state.messages.some((m) => m.id === message.id)) {
        return {
          quickReplies: updatedQuickReplies,
          isTyping: false,
        };
      }

      // If voice mode is active and message is from coach, speak the response aloud
      // and automatically resume listening for the next user turn
      if (message.sender === 'coach' && message.text) {
        import('@/stores/useVoiceStore').then(({ useVoiceStore }) => {
          const voiceState = useVoiceStore.getState();
          if (voiceState.isVoiceModeEnabled) {
            voiceState.speakAndThenListen(message.text);
          }
        }).catch(() => {});
      }

      return {
        messages: [...state.messages, message],
        quickReplies: updatedQuickReplies,
        isTyping: false,
      };
    });
  },

  sendMessage: async (text: string, patientId?: number) => {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const userMsgId = `msg-user-${Date.now()}`;

    // Voice session trigger: don't show any user message in the chat
    // thread — just send to server and show typing indicator
    const isVoiceTrigger = text.trim() === '[VOICE_SESSION_START]';

    console.log(`💬 [Mobile Chat] Sending: "${text}"`);

    if (isVoiceTrigger) {
      // Only show typing indicator, no user message bubble
      set({ isTyping: true });
    } else {
      const newMessage: ChatMessage = {
        id: userMsgId,
        sender: 'user',
        text,
        timestamp: timeString,
      };

      // 1. Immediately show user message in the thread & show typing indicator
      set((state) => ({
        messages: [...state.messages, newMessage],
        isTyping: true,
      }));
    }

    // 2. Primary Transport: Emit over Socket.IO if connected
    if (socketService.isConnected()) {
      socketService.emit('send_message', {
        text,
        timestamp: timeString,
      });
      return;
    }

    // 3. Fallback Transport: Send via HTTP REST only if Socket.IO is disconnected
    try {
      const response = await apiClient.post<ChatMessage>('/api/conversations/messages', {
        text,
        patient_id: patientId || 1,
      });

      if (response.data && response.data.text) {
        console.log(`✨ [Mobile Chat] Received Amy reply: "${response.data.text.slice(0, 60)}..."`);
        get().addIncomingMessage(response.data);
      }
    } catch (error) {
      console.warn('⚠️ [Chat Store] REST send error:', error);
      set({ isTyping: false });
    }
  },

  selectActivity: (card: ActivityCard) => {
    set({ selectedCardId: card.id, isTyping: true });

    const timeString = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const userSelectionMsg: ChatMessage = {
      id: `msg-select-${Date.now()}`,
      sender: 'user',
      text: `Selected: ${card.title}`,
      timestamp: timeString,
    };

    set((state) => ({
      messages: [...state.messages, userSelectionMsg],
    }));

    if (socketService.isConnected()) {
      // Emit activity selection through Socket.IO
      socketService.emit('select_activity', {
        activityId: card.id,
        title: card.title,
      });
    } else {
      get().sendMessage(`Selected: ${card.title}`);
    }
  },
}));

// Listen to incoming Coach messages from Socket.IO
socketService.onCoachMessage((data: any) => {
  if (data && data.text) {
    const msg: ChatMessage = {
      id: data.id || `coach-${Date.now()}`,
      sender: 'coach',
      text: data.text,
      timestamp: data.timestamp || new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
      isSafetyAlert: data.isSafetyAlert,
      riskLevel: data.riskLevel,
      options: data.options,
      quickReplies: data.quickReplies,
    };
    useChatStore.getState().addIncomingMessage(msg);
  }
});
