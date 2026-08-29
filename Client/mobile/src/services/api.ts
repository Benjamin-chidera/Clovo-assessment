import axios from 'axios';
import { Platform } from 'react-native';

const BASE_URL =
  Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
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
