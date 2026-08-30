import { create } from 'zustand';

export interface SafetyEventItem {
  id: string;
  patient_id?: number;
  patient_name?: string;
  procedure?: string;
  conversation_id: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  trigger: string;
  action: string;
  status: 'open' | 'reviewed' | 'resolved';
  created_at: string;
}

interface SafetyTriageState {
  events: SafetyEventItem[];
  selectedEvent: SafetyEventItem | null;
  activeFilter: 'all' | 'critical' | 'high' | 'medium' | 'low';
  isConnected: boolean;
  isLoading: boolean;
  setEvents: (events: SafetyEventItem[]) => void;
  addEvent: (event: SafetyEventItem) => void;
  resolveEvent: (id: string) => void;
  setSelectedEvent: (event: SafetyEventItem | null) => void;
  setActiveFilter: (filter: 'all' | 'critical' | 'high' | 'medium' | 'low') => void;
  setIsConnected: (connected: boolean) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useSafetyTriageStore = create<SafetyTriageState>((set) => ({
  events: [],
  selectedEvent: null,
  activeFilter: 'all',
  isConnected: false,
  isLoading: false,

  setEvents: (events) => set({ events }),

  addEvent: (event) =>
    set((state) => {
      // Prevent duplicates
      const exists = state.events.some((e) => e.id === event.id);
      if (exists) return state;
      return { events: [event, ...state.events] };
    }),

  resolveEvent: (id) =>
    set((state) => ({
      events: state.events.map((e) =>
        e.id === id ? { ...e, status: 'resolved' as const } : e
      ),
      selectedEvent:
        state.selectedEvent?.id === id
          ? { ...state.selectedEvent, status: 'resolved' as const }
          : state.selectedEvent,
    })),

  setSelectedEvent: (selectedEvent) => set({ selectedEvent }),
  setActiveFilter: (activeFilter) => set({ activeFilter }),
  setIsConnected: (isConnected) => set({ isConnected }),
  setIsLoading: (isLoading) => set({ isLoading }),
}));
