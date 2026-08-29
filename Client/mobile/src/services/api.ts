import axios from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Dynamically resolve the backend API URL across iOS Simulator,
 * Android Emulator, physical devices (via Expo Go / Wi-Fi), and Web.
 */
export function getBackendUrl(): string {
  // 1. Explicit environment variable override
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  // 2. Extract host IP from Expo debugger/bundle URL (for physical devices over LAN)
  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const ip = hostUri.split(':')[0];
    if (ip && ip !== 'localhost' && ip !== '127.0.0.1') {
      return `http://${ip}:8000`;
    }
  }

  // 3. Fallback for Android emulator vs iOS simulator / Web
  return Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
}

export const apiClient = axios.create({
  baseURL: getBackendUrl(),
  timeout: 120000, // 120s (2 minutes) timeout for reliable local LLM (Gemma 4) generation under heavy loads
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor for logging & graceful error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg = error.response?.data?.detail || error.message;
    console.warn(
      `⚠️ [Axios API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`,
      errorMsg
    );
    return Promise.reject(error);
  }
);
