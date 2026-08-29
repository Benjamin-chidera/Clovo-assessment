import { create } from 'zustand';
import { socketService } from '@/services/socketService';

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
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'coach';
  text: string;
  timestamp: string;
  options?: ActivityCard[];
  selectedOptionId?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  selectedCardId: string | null;
  quickReplies: string[];
  sendMessage: (text: string, sender?: 'user' | 'coach') => void;
  selectActivity: (card: ActivityCard) => void;
  addIncomingMessage: (message: ChatMessage) => void;
}

const INITIAL_ACTIVITY_CARDS: ActivityCard[] = [
  {
    id: 'card-stretch',
    title: 'Gentle Stretching – Release Tension',
    durationMinutes: 10,
    durationLabel: '10 minutes',
    intensity: 'Low',
    imageUri: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&q=80',
    tag: 'Stretching',
  },
  {
    id: 'card-walk',
    title: 'Recovery Walk – Shake Off Soreness',
    durationMinutes: 30,
    durationLabel: '30 minutes',
    intensity: 'Low',
    imageUri: 'https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?auto=format&fit=crop&w=600&q=80',
    tag: 'Outdoor Walk',
  },
  {
    id: 'card-yoga',
    title: 'Yoga for Beginners – Recovery Basics',
    durationMinutes: 20,
    durationLabel: '20 minutes',
    intensity: 'Low',
    imageUri: 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80',
    tag: 'Gentle Yoga',
  },
  {
    id: 'card-surprise',
    title: 'Surprise Me! 🎁',
    subtitle: "Let's See What You Get",
    imageUri: 'https://images.unsplash.com/photo-1513885535751-8b9238bd345a?auto=format&fit=crop&w=600&q=80',
    isSpecial: true,
  },
];

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [
    {
      id: 'msg-1',
      sender: 'user',
      text: "It's a little lower than normal. Let's do it, but nothing intense.",
      timestamp: '9:41 AM',
    },
    {
      id: 'msg-2',
      sender: 'coach',
      text: "Great attitude! Since today's a low-energy day, I've switched up your options to keep things light. Pick what feels best—something to stretch, move, or just reset. 💙",
      timestamp: '9:42 AM',
      options: INITIAL_ACTIVITY_CARDS,
    },
  ],
  selectedCardId: null,
  quickReplies: ['Sounds good! 👍', 'I only have 5 mins ⏱', 'Show more options ✨', 'Gentle stretch sounds great! 🧘‍♀️'],

  addIncomingMessage: (message: ChatMessage) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  sendMessage: (text: string, sender: 'user' | 'coach' = 'user') => {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const newMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender,
      text,
      timestamp: timeString,
    };

    set((state) => ({
      messages: [...state.messages, newMessage],
    }));

    if (sender === 'user') {
      // Emit real-time message through Socket.IO to backend server
      socketService.emit('send_message', {
        text,
        timestamp: timeString,
      });

      // Fallback local response simulation if server is offline
      setTimeout(() => {
        const coachResponse: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'coach',
          text: `Got it, Jen! I've updated your recovery plan accordingly. Take your time and enjoy your routine! 🌟`,
          timestamp: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        };
        set((state) => ({
          messages: [...state.messages, coachResponse],
        }));
      }, 900);
    }
  },

  selectActivity: (card: ActivityCard) => {
    set({ selectedCardId: card.id });

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

    // Emit activity selection through Socket.IO
    socketService.emit('select_activity', {
      activityId: card.id,
      title: card.title,
    });

    setTimeout(() => {
      const coachFeedbackMsg: ChatMessage = {
        id: `msg-feedback-${Date.now() + 1}`,
        sender: 'coach',
        text: `Awesome pick! "${card.title}" is ready. Take a deep breath and start whenever you're ready. I'm cheering you on! 🌟`,
        timestamp: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
      };
      set((state) => ({
        messages: [...state.messages, coachFeedbackMsg],
      }));
    }, 800);
  },
}));
