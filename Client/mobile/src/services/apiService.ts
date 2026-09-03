import { apiClient } from './api';
import { DailyTask, TaskCategory } from '@/stores/useTaskStore';

export interface MilestoneResponse {
  id: string;
  code: string;
  title: string;
  description?: string;
  icon_name: string;
  color: string;
  bg_gradient: [string, string];
  unlocked_at?: string;
}

export interface UserProfileResponse {
  id: string;
  name: string;
  email?: string;
  avatar_uri?: string;
  plan?: string;
  phase?: string;
  streak_count: number;
  greeting: string;
  surgery_title: string;
  days_away: number;
  days_post_op?: number;
  procedure_name?: string;
  procedure_date?: string;
  milestones?: MilestoneResponse[];
  additional_milestones_count?: number;
  total_completed_tasks?: number;
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
  days_post_op?: number;
  phase?: string;
  procedure_name?: string;
  procedure_date?: string;
  streak_count?: number;
  milestones?: MilestoneResponse[];
  additional_milestones_count?: number;
  total_completed_tasks?: number;
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
