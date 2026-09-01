import { create } from 'zustand';
import * as Speech from 'expo-speech';
import {
  AudioModule,
  IOSOutputFormat,
  AudioQuality,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
} from 'expo-audio';
import {
  uploadAsync,
  deleteAsync,
  FileSystemUploadType,
} from 'expo-file-system/legacy';
import { Platform } from 'react-native';
import { getBackendUrl } from '@/services/api';

// Web Speech Recognition typing
declare global {
  interface Window {
    webkitSpeechRecognition?: any;
    SpeechRecognition?: any;
  }
}

/**
 * Voice conversation states:
 * - idle: voice mode off, no activity
 * - greeting: Amy is speaking her initial greeting
 * - speaking: Amy is speaking a response
 * - listening: microphone is active, recording user speech with live VAD
 * - processing: user spoke, transcribing + waiting for Amy's response
 */
export type VoicePhase = 'idle' | 'greeting' | 'speaking' | 'listening' | 'processing';

interface VoiceStoreState {
  isVoiceModeEnabled: boolean;
  isSpeaking: boolean;
  isListening: boolean;
  phase: VoicePhase;
  transcript: string;
  lastSpokenText: string | null;

  // Actions
  activateVoiceConversation: (sendMessageFn: (text: string) => void) => void;
  deactivateVoiceConversation: () => void;
  interruptAndListen: () => void;
  speakAndThenListen: (text: string) => void;
  speak: (text: string) => Promise<void>;
  stopSpeaking: () => void;
  startListening: (
    onResult?: (text: string) => void,
    onAutoSend?: (text: string) => void
  ) => void;
  stopListening: () => void;
}

// Whisper-optimized audio preset with real-time metering for VAD
const WHISPER_AUDIO_PRESET = {
  extension: '.wav',
  sampleRate: 16000,
  numberOfChannels: 1,
  bitRate: 128000,
  isMeteringEnabled: true,
  ios: {
    outputFormat: IOSOutputFormat.LINEARPCM,
    audioQuality: AudioQuality.HIGH,
    linearPCMBitDepth: 16,
    linearPCMIsBigEndian: false,
    linearPCMIsFloat: false,
  },
  android: {
    outputFormat: 'mpeg4' as const,
    audioEncoder: 'aac' as const,
  },
  web: {
    mimeType: 'audio/webm',
    bitsPerSecond: 128000,
  },
};

// Voice Activity Detection (VAD) Thresholds
const SPEECH_METERING_THRESHOLD_DB = -36; // dBFS threshold for voice activity
const NATURAL_SILENCE_MS = 1600; // 1.6s of silence after speaking triggers auto-submit
const MIN_SPEECH_DURATION_MS = 350; // minimum duration of speech before silence is evaluated

// Active speech recognition instance (web only)
let webRecognitionInstance: any = null;

// Active audio recorder instance (native iOS/Android via expo-audio)
let activeNativeRecorder: any = null;

// Reference to the sendMessage function for the auto-send loop
let activeSendMessageFn: ((text: string) => void) | null = null;

// Store the onAutoSend callback for native recording completion
let activeOnAutoSend: ((text: string) => void) | null = null;

// Auto-stop safety fallback timer
let safetyFallbackTimer: any = null;

// High-frequency VAD (Voice Activity Detection) polling interval
let vadInterval: any = null;

// Guard flag to prevent concurrent audio transitions
let isTransitioningAudio = false;

/**
 * Clean text for natural speech synthesis
 */
function sanitizeTextForSpeech(rawText: string): string {
  if (!rawText) return '';
  return rawText
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/#{1,6}\s+/g, '')
    .replace(/[`~_]/g, '')
    .replace(/https?:\/\/\S+/g, '')
    .replace(/[\u{1F600}-\u{1F6FF}]/gu, '')
    .replace(/\n+/g, ' ')
    .trim();
}

/**
 * Upload a recorded audio file to the server for OpenAI Whisper transcription.
 */
async function transcribeAudioOnServer(audioUri: string): Promise<string | null> {
  try {
    const serverUrl = getBackendUrl();
    const uploadUrl = `${serverUrl}/api/voice/transcribe`;

    console.log(`🎙️ [VoiceStore] Uploading audio to Whisper: ${uploadUrl}`);

    const mimeType = audioUri.toLowerCase().endsWith('.wav') ? 'audio/wav' : 'audio/m4a';

    const response = await uploadAsync(uploadUrl, audioUri, {
      httpMethod: 'POST',
      uploadType: FileSystemUploadType.MULTIPART,
      fieldName: 'file',
      mimeType,
      headers: {
        Accept: 'application/json',
      },
    });

    if (response.status === 200 && response.body) {
      const data = JSON.parse(response.body);
      const text = data.text?.trim();
      if (text && text.length > 0) {
        console.log(`🎙️ [VoiceStore] Whisper transcribed: "${text}"`);
        return text;
      }
    } else {
      console.warn(`⚠️ [VoiceStore] Whisper server returned status ${response.status}:`, response.body);
    }

    console.log('🔇 [VoiceStore] No speech detected in audio clip');
    return null;
  } catch (error) {
    console.warn('⚠️ [VoiceStore] Transcription upload error:', error);
    return null;
  }
}

export const useVoiceStore = create<VoiceStoreState>((set, get) => ({
  isVoiceModeEnabled: false,
  isSpeaking: false,
  isListening: false,
  phase: 'idle' as VoicePhase,
  transcript: '',
  lastSpokenText: null,

  /**
   * Activate voice conversation mode.
   * Amy speaks her greeting, and automatically begins listening with live silence detection.
   */
  activateVoiceConversation: (sendMessageFn: (text: string) => void) => {
    activeSendMessageFn = sendMessageFn;

    // Clean up any lingering speech or recordings
    get().stopSpeaking();
    if (activeNativeRecorder) {
      try {
        activeNativeRecorder.stop();
      } catch {
        // ignore
      }
      activeNativeRecorder = null;
    }
    if (vadInterval) {
      clearInterval(vadInterval);
      vadInterval = null;
    }

    set({
      isVoiceModeEnabled: true,
      isSpeaking: false,
      isListening: false,
      phase: 'greeting',
      transcript: '',
    });

    const warmGreeting =
      "Hey Sarah! How are you doing today? Ready to continue your recovery session?";

    console.log('🎙️ [VoiceStore] Voice conversation activated — Amy speaking greeting');

    // addIncomingMessage will trigger speakAndThenListen(warmGreeting)
    import('@/stores/useChatStore').then(({ useChatStore }) => {
      const now = new Date();
      const timeString = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      useChatStore.getState().addIncomingMessage({
        id: `coach-voice-greeting-${Date.now()}`,
        sender: 'coach',
        text: warmGreeting,
        timestamp: timeString,
        quickReplies: ["I'm doing well! 😊", "Feeling a bit sore today", "What's on my plan?"],
      });
    }).catch(() => {
      get().speakAndThenListen(warmGreeting);
    });
  },

  /**
   * Deactivate voice conversation mode — stops all audio hardware immediately.
   */
  deactivateVoiceConversation: () => {
    console.log('🎙️ [VoiceStore] Voice conversation deactivated (stopped)');
    activeSendMessageFn = null;
    activeOnAutoSend = null;

    if (safetyFallbackTimer) {
      clearTimeout(safetyFallbackTimer);
      safetyFallbackTimer = null;
    }
    if (vadInterval) {
      clearInterval(vadInterval);
      vadInterval = null;
    }

    // 1. Stop Speech
    try {
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      } else {
        Speech.stop();
      }
    } catch {
      // ignore
    }

    // 2. Stop native audio recording
    if (activeNativeRecorder) {
      const recorder = activeNativeRecorder;
      activeNativeRecorder = null;
      try {
        recorder.stop();
      } catch {
        // ignore
      }
    }

    // 3. Reset Audio Mode to playback
    if (Platform.OS === 'ios' || Platform.OS === 'android') {
      try {
        setAudioModeAsync({
          allowsRecording: false,
          playsInSilentMode: true,
        });
      } catch {
        // ignore
      }
    }

    set({
      isVoiceModeEnabled: false,
      isSpeaking: false,
      isListening: false,
      phase: 'idle',
      transcript: '',
    });
  },

  /**
   * Barge-in / Interruption: Stops Amy immediately and opens the listener.
   */
  interruptAndListen: () => {
    console.log('🎙️ [VoiceStore] Interrupting Amy — opening listener immediately');
    get().stopSpeaking();

    set({ isSpeaking: false, phase: 'listening' });

    setTimeout(() => {
      if (!get().isVoiceModeEnabled) return;
      get().startListening();
    }, 250);
  },

  /**
   * Speak Amy's response aloud, then automatically start listening
   * with Voice Activity Detection (VAD) for natural silence detection.
   */
  speakAndThenListen: (text: string) => {
    const { isVoiceModeEnabled } = get();
    if (!isVoiceModeEnabled || !text) return;

    const cleanText = sanitizeTextForSpeech(text);
    if (!cleanText) {
      set({ phase: 'listening' });
      get().startListening();
      return;
    }

    try {
      // Stop previous utterance
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      } else {
        Speech.stop();
      }

      set({ isSpeaking: true, phase: 'speaking', lastSpokenText: cleanText });

      const onSpeechComplete = () => {
        set({ isSpeaking: false });

        const currentState = get();
        if (currentState.isVoiceModeEnabled) {
          console.log('🎙️ [VoiceStore] Amy finished speaking → auto-activating listener with VAD');
          set({ phase: 'listening' });

          // 400ms buffer allows iOS audio engine to cleanly switch category
          setTimeout(() => {
            if (!get().isVoiceModeEnabled) return;
            get().startListening();
          }, 400);
        }
      };

      // Web Speech Synthesis
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'en-GB';
        utterance.rate = 0.95;
        utterance.pitch = 1.05;

        utterance.onstart = () => set({ isSpeaking: true });
        utterance.onend = () => onSpeechComplete();
        utterance.onerror = () => onSpeechComplete();

        window.speechSynthesis.speak(utterance);
      } else {
        // Native mobile speech via expo-speech
        Speech.speak(cleanText, {
          language: 'en-GB',
          pitch: 1.05,
          rate: 0.95,
          onStart: () => set({ isSpeaking: true }),
          onDone: () => onSpeechComplete(),
          onStopped: () => set({ isSpeaking: false }),
          onError: () => onSpeechComplete(),
        });
      }
    } catch (err) {
      console.warn('⚠️ [VoiceStore Speech Exception]', err);
      set({ isSpeaking: false });
    }
  },

  /**
   * Speak text without auto-listening afterwards.
   */
  speak: async (text: string) => {
    const { isVoiceModeEnabled } = get();
    if (!isVoiceModeEnabled || !text) return;

    const cleanText = sanitizeTextForSpeech(text);
    if (!cleanText) return;

    try {
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      } else {
        Speech.stop();
      }

      set({ isSpeaking: true, lastSpokenText: cleanText });

      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'en-GB';
        utterance.rate = 0.95;
        utterance.pitch = 1.05;
        utterance.onend = () => set({ isSpeaking: false });
        utterance.onerror = () => set({ isSpeaking: false });
        window.speechSynthesis.speak(utterance);
      } else {
        Speech.speak(cleanText, {
          language: 'en-GB',
          pitch: 1.05,
          rate: 0.95,
          onDone: () => set({ isSpeaking: false }),
          onStopped: () => set({ isSpeaking: false }),
          onError: () => set({ isSpeaking: false }),
        });
      }
    } catch (err) {
      console.warn('⚠️ [VoiceStore Speech Exception]', err);
      set({ isSpeaking: false });
    }
  },

  stopSpeaking: () => {
    try {
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      } else {
        Speech.stop();
      }
    } catch {
      // ignore
    }
    set({ isSpeaking: false });
  },

  /**
   * Start listening for user speech with real-time Voice Activity Detection (VAD) & Silence Detection.
   */
  startListening: (
    onResult?: (text: string) => void,
    onAutoSend?: (text: string) => void
  ) => {
    set({ isListening: true, transcript: '' });

    // ── 1. Web: browser SpeechRecognition API ──
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          if (webRecognitionInstance) {
            webRecognitionInstance.abort();
          }

          const recognition = new SpeechRecognition();
          recognition.continuous = false;
          recognition.interimResults = true;
          recognition.lang = 'en-GB';

          let capturedText = '';

          recognition.onresult = (event: any) => {
            // If user speaks while Amy is speaking, halt Amy immediately (Barge-in)
            if (get().isSpeaking) {
              get().stopSpeaking();
            }

            let currentTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
              currentTranscript += event.results[i][0].transcript;
            }
            capturedText = currentTranscript;
            set({ transcript: currentTranscript });
            if (onResult && currentTranscript) {
              onResult(currentTranscript);
            }
          };

          recognition.onerror = (event: any) => {
            console.warn('⚠️ [Speech Recognition Error]', event.error);
            set({ isListening: false });
          };

          // Web Speech automatically detects natural silence when speech ends!
          recognition.onend = () => {
            set({ isListening: false });
            if (capturedText.trim()) {
              console.log(`🎙️ [Web VAD] User finished speaking: "${capturedText.trim()}"`);
              if (onAutoSend) {
                onAutoSend(capturedText.trim());
              } else if (activeSendMessageFn) {
                activeSendMessageFn(capturedText.trim());
              }
            } else if (get().isVoiceModeEnabled) {
              // Smooth resume if no speech
              setTimeout(() => {
                if (get().isVoiceModeEnabled) get().startListening();
              }, 400);
            }
          };

          recognition.start();
          webRecognitionInstance = recognition;
          return;
        } catch (e) {
          console.warn('⚠️ [SpeechRecognition init error]', e);
        }
      }
    }

    // ── 2. Native iOS/Android: expo-audio recording with Real-Time VAD ──
    if (Platform.OS === 'ios' || Platform.OS === 'android') {
      if (onAutoSend) {
        activeOnAutoSend = onAutoSend;
      }

      (async () => {
        if (isTransitioningAudio) return;
        isTransitioningAudio = true;

        try {
          const permissionResult = await requestRecordingPermissionsAsync();
          if (!permissionResult.granted) {
            console.warn('⚠️ [VoiceStore] Microphone permission denied');
            set({ isListening: false, phase: 'idle' });
            isTransitioningAudio = false;
            return;
          }

          // Stop TTS before opening recorder
          Speech.stop();

          await setAudioModeAsync({
            allowsRecording: true,
            playsInSilentMode: true,
          });

          // Create recorder with Linear PCM WAV preset and live audio metering enabled
          const recorder = new AudioModule.AudioRecorder(WHISPER_AUDIO_PRESET);
          await recorder.prepareToRecordAsync();
          recorder.record();
          activeNativeRecorder = recorder;

          console.log('🎙️ [VoiceStore] Native audio recording active with live VAD silence detection');

          // VAD State Tracker
          let hasDetectedSpeech = false;
          let speechStartTime = 0;
          let lastSpeechTime = 0;
          let consecutiveSilenceFrames = 0;

          // Clear any previous interval
          if (vadInterval) {
            clearInterval(vadInterval);
            vadInterval = null;
          }

          // Run high-frequency VAD check every 100ms
          vadInterval = setInterval(() => {
            try {
              if (activeNativeRecorder !== recorder || !get().isListening) {
                if (vadInterval) clearInterval(vadInterval);
                return;
              }

              const status = recorder.getStatus();
              const metering = status?.metering;

              if (typeof metering === 'number' && metering !== -160) {
                const now = Date.now();
                // Check if audio level represents human speech
                const isVoiceActive = metering > SPEECH_METERING_THRESHOLD_DB;

                if (isVoiceActive) {
                  consecutiveSilenceFrames = 0;

                  if (!hasDetectedSpeech) {
                    hasDetectedSpeech = true;
                    speechStartTime = now;
                    console.log(`🎙️ [VAD] User speech detected (${metering.toFixed(1)} dB)`);
                  }
                  lastSpeechTime = now;

                  // Barge-in: If Amy is speaking and user speaks, halt Amy immediately!
                  if (get().isSpeaking) {
                    console.log(`🎙️ [VAD] User spoke over Amy (${metering.toFixed(1)} dB) — halting Amy immediately!`);
                    get().stopSpeaking();
                    set({ isSpeaking: false, phase: 'listening' });
                  }
                } else if (hasDetectedSpeech) {
                  consecutiveSilenceFrames += 1;
                  const silenceDuration = now - lastSpeechTime;
                  const totalSpokenDuration = lastSpeechTime - speechStartTime;

                  // If user spoke for >= 350ms AND has now stopped talking (silence >= 1600ms):
                  if (
                    silenceDuration >= NATURAL_SILENCE_MS &&
                    totalSpokenDuration >= MIN_SPEECH_DURATION_MS &&
                    get().isListening
                  ) {
                    console.log(
                      `🎙️ [VAD] Natural silence detected (${silenceDuration}ms after ${totalSpokenDuration}ms speech) → Auto-submitting to Whisper!`
                    );
                    if (vadInterval) {
                      clearInterval(vadInterval);
                      vadInterval = null;
                    }
                    get().stopListening();
                  }
                }
              }
            } catch {
              // ignore
            }
          }, 100);

          // Safety fallback: if user speaks continuously for 30s, auto-stop to prevent overflow
          if (safetyFallbackTimer) {
            clearTimeout(safetyFallbackTimer);
          }
          safetyFallbackTimer = setTimeout(() => {
            if (activeNativeRecorder === recorder && get().isListening) {
              console.log('🎙️ [VoiceStore] Safety limit reached (30s) — processing speech');
              if (vadInterval) {
                clearInterval(vadInterval);
                vadInterval = null;
              }
              get().stopListening();
            }
          }, 30000);
        } catch (error) {
          console.warn('⚠️ [VoiceStore] Recording start error:', error);
          set({ isListening: false });
        } finally {
          isTransitioningAudio = false;
        }
      })();
      return;
    }

    console.log('🎙️ [VoiceStore] Listening activated (no STT engine available)');
  },

  /**
   * Stop listening / stop recording and upload to Whisper.
   */
  stopListening: () => {
    if (safetyFallbackTimer) {
      clearTimeout(safetyFallbackTimer);
      safetyFallbackTimer = null;
    }
    if (vadInterval) {
      clearInterval(vadInterval);
      vadInterval = null;
    }

    // ── Web ──
    if (webRecognitionInstance) {
      try {
        webRecognitionInstance.stop();
      } catch {
        // ignore
      }
      webRecognitionInstance = null;
    }

    // ── Native ──
    if (activeNativeRecorder) {
      const recorder = activeNativeRecorder;
      activeNativeRecorder = null;
      const savedOnAutoSend = activeOnAutoSend;

      set({ isListening: false });

      (async () => {
        try {
          try {
            await recorder.stop();
          } catch (stopErr) {
            console.warn('⚠️ [VoiceStore] Recorder stop notice:', stopErr);
          }

          // Switch back to playback category for TTS
          try {
            await setAudioModeAsync({
              allowsRecording: false,
              playsInSilentMode: true,
            });
          } catch {
            // ignore
          }

          const uri = recorder.uri;
          if (!uri) {
            console.warn('⚠️ [VoiceStore] No recording URI');
            return;
          }

          console.log(`🎙️ [VoiceStore] Recording captured (${uri}) — uploading to Whisper`);
          set({ phase: 'processing' });

          const transcribedText = await transcribeAudioOnServer(uri);

          if (transcribedText) {
            set({ transcript: transcribedText, phase: 'processing' });
            console.log(`💬 [VoiceStore] Sending patient speech to Amy: "${transcribedText}"`);
            if (activeSendMessageFn) {
              activeSendMessageFn(transcribedText);
            } else if (savedOnAutoSend) {
              savedOnAutoSend(transcribedText);
            } else {
              import('@/stores/useChatStore').then(({ useChatStore }) => {
                useChatStore.getState().sendMessage(transcribedText);
              });
            }
          } else {
            console.log('🔇 [VoiceStore] No speech detected in recording — listening again');
            if (get().isVoiceModeEnabled) {
              set({ phase: 'listening' });
              setTimeout(() => {
                if (get().isVoiceModeEnabled) {
                  get().startListening();
                }
              }, 400);
            }
          }

          // Clean up local temp audio file
          try {
            await deleteAsync(uri, { idempotent: true });
          } catch {
            // ignore
          }
        } catch (error) {
          console.warn('⚠️ [VoiceStore] Recording transcribe error:', error);
          set({ isListening: false });
        }
      })();
      return;
    }

    set({ isListening: false });
  },
}));
