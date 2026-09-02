import { useVoiceStore } from '../useVoiceStore';
import * as Speech from 'expo-speech';

describe('useVoiceStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useVoiceStore.setState({
      isVoiceModeEnabled: false,
      isSpeaking: false,
      isListening: false,
      phase: 'idle',
      transcript: '',
      lastSpokenText: null,
    });
  });

  it('MOB-UNIT-STR-005: starts in idle state with voice disabled', () => {
    const state = useVoiceStore.getState();
    expect(state.phase).toBe('idle');
    expect(state.isVoiceModeEnabled).toBe(false);
    expect(state.isSpeaking).toBe(false);
    expect(state.isListening).toBe(false);
  });

  it('MOB-UNIT-STR-006: deactivateVoiceConversation halts speech and resets to idle', () => {
    // Set active state
    useVoiceStore.setState({
      isVoiceModeEnabled: true,
      phase: 'speaking',
      isSpeaking: true,
    });

    useVoiceStore.getState().deactivateVoiceConversation();

    const state = useVoiceStore.getState();
    expect(state.phase).toBe('idle');
    expect(state.isVoiceModeEnabled).toBe(false);
    expect(state.isSpeaking).toBe(false);
    expect(Speech.stop).toHaveBeenCalled();
  });

  it('MOB-UNIT-STR-007: stopSpeaking stops expo-speech and clears speaking flag', () => {
    useVoiceStore.setState({ isSpeaking: true });
    useVoiceStore.getState().stopSpeaking();

    expect(Speech.stop).toHaveBeenCalled();
    expect(useVoiceStore.getState().isSpeaking).toBe(false);
  });
});
