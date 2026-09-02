import { useChatStore, ChatMessage } from '../useChatStore';
import { apiClient } from '@/services/api';

jest.mock('@/services/api', () => ({
  apiClient: {
    post: jest.fn().mockResolvedValue({ data: {} }),
    get: jest.fn().mockResolvedValue({ data: [] }),
  },
  getBackendUrl: jest.fn(() => 'http://localhost:8000'),
}));

jest.mock('@/services/socketService', () => ({
  socketService: {
    isConnected: jest.fn(() => true),
    emitMessage: jest.fn(),
    emit: jest.fn(),
    onCoachMessage: jest.fn(() => jest.fn()),
    onTaskSync: jest.fn(() => jest.fn()),
  },
}));

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useChatStore.setState({
      messages: [],
      isLoading: false,
      isTyping: false,
      selectedCardId: null,
      quickReplies: ["What's my plan for today? 📋", "I'm feeling a bit tired today 🥱"],
    });
    jest.clearAllMocks();
  });

  it('MOB-UNIT-STR-001: starts with empty messages and default quick replies', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.isTyping).toBe(false);
    expect(state.quickReplies.length).toBeGreaterThan(0);
  });

  it('MOB-UNIT-STR-002: addIncomingMessage appends coach message to state', () => {
    const msg: ChatMessage = {
      id: 'msg-1',
      sender: 'coach',
      text: 'Good morning Sarah! Ready to move?',
      timestamp: '9:00 AM',
    };

    useChatStore.getState().addIncomingMessage(msg);
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].text).toBe('Good morning Sarah! Ready to move?');
    expect(state.messages[0].sender).toBe('coach');
  });

  it('MOB-UNIT-STR-003: setQuickReplies updates quick replies list', () => {
    const newReplies = ['Yes, ready!', 'Need 5 more minutes'];
    useChatStore.getState().setQuickReplies(newReplies);
    expect(useChatStore.getState().quickReplies).toEqual(newReplies);
  });

  it('MOB-UNIT-STR-004: selectActivity marks card as selected in state', () => {
    const activity = {
      id: 'act-1',
      title: 'Quad Sets',
      imageUri: 'https://example.com/quads.jpg',
    };
    useChatStore.getState().selectActivity(activity);
    expect(useChatStore.getState().selectedCardId).toBe('act-1');
  });
});
