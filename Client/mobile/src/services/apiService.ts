import { apiClient } from './api';
import { DailyTask, TaskCategory } from '@/stores/useTaskStore';

export interface UserProfileResponse {
  id: string;
  name: string;
  email?: string;
  avatar_uri?: string;
  plan?: string;
  streak_count: number;
  greeting: string;
  surgery_title: string;
  days_away: number;
  procedure_name?: string;
  procedure_date?: string;
}

export interface TaskItemResponse {
  id: string;
  title: string;
  category: TaskCategory;
  duration: string;
  is_completed: boolean;
  category_label: string;
  instruction?: string;
  rationale?: string;
}

export interface PreparationItemResponse {
  id: string;
  title: string;
  is_completed: boolean;
  type: string;
  instruction?: string;
  rationale?: string;
}

export interface HomeDataResponse {
  greeting: string;
  patient_name: string;
  surgery_title: string;
  days_away: number;
  procedure_name?: string;
  procedure_date?: string;
  preparations: PreparationItemResponse[];
}

export const apiService = {
  /**
   * Fetch actual user profile data from the SQLite database via Axios
   */
  async getUser(userId?: string): Promise<UserProfileResponse> {
    const response = await apiClient.get<UserProfileResponse>('/api/user', {
      params: userId ? { patient_id: userId } : undefined,
    });
    return response.data;
  },

  /**
   * Fetch actual preparation tasks from the SQLite database via Axios
   */
  async getTasks(userId?: string): Promise<TaskItemResponse[]> {
    const response = await apiClient.get<TaskItemResponse[]>('/api/tasks', {
      params: userId ? { patient_id: userId } : undefined,
    });
    return response.data;
  },

  /**
   * Toggle task completion status in the database via Axios
   */
  async toggleTask(taskId: string): Promise<any> {
    const response = await apiClient.patch(`/api/tasks/${taskId}/toggle`);
    return response.data;
  },

  /**
   * Fetch aggregated home dashboard data via Axios
   */
  async getHomeData(patientId?: string): Promise<HomeDataResponse> {
    const response = await apiClient.get<HomeDataResponse>('/api/home', {
      params: patientId ? { patient_id: patientId } : undefined,
    });
    return response.data;
  },

  /**
   * Toggle recommendation status via Axios
   */
  async toggleRecommendation(recommendationId: string): Promise<any> {
    const response = await apiClient.patch(`/api/recommendations/${recommendationId}/toggle`);
    return response.data;
  },
};
