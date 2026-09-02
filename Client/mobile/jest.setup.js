// Mock expo-speech
jest.mock("expo-speech", () => ({
  speak: jest.fn(),
  stop: jest.fn(),
  isSpeakingAsync: jest.fn().mockResolvedValue(false),
}));

// Mock expo-haptics
jest.mock("expo-haptics", () => ({
  notificationAsync: jest.fn(),
  impactAsync: jest.fn(),
  selectionAsync: jest.fn(),
  NotificationFeedbackType: {
    Success: "success",
    Warning: "warning",
    Error: "error",
  },
  ImpactFeedbackStyle: {
    Light: "light",
    Medium: "medium",
    Heavy: "heavy",
  },
}));

// Mock expo-audio
jest.mock("expo-audio", () => ({
  AudioModule: {
    requestRecordingPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
    setAudioModeAsync: jest.fn().mockResolvedValue(true),
  },
  requestRecordingPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
  setAudioModeAsync: jest.fn().mockResolvedValue(true),
  IOSOutputFormat: {
    LINEARPCM: "lpcm",
    MPEG4AAC: "aac",
  },
  AudioQuality: {
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
    MAX: "max",
  },
  RecordingPresets: {
    HIGH_QUALITY: {},
  },
  createAudioRecorder: jest.fn(() => ({
    prepareToRecordAsync: jest.fn().mockResolvedValue({}),
    record: jest.fn(),
    stop: jest.fn().mockResolvedValue({ uri: "file:///mock-audio.m4a" }),
    uri: "file:///mock-audio.m4a",
    currentTime: 2.5,
  })),
}));

// Mock socket.io-client
jest.mock("socket.io-client", () => {
  const mSocket = {
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
    connected: true,
  };
  return jest.fn(() => mSocket);
});

// Mock @expo/vector-icons
jest.mock("@expo/vector-icons", () => ({
  Ionicons: "Ionicons",
}));
