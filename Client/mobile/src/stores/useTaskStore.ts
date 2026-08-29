import { create } from 'zustand';
import { apiService, TaskItemResponse } from '@/services/apiService';
import { socketService } from '@/services/socketService';

export type TaskCategory = 'walking' | 'recovery' | 'mindset' | 'hydration' | 'nutrition';

export interface DailyTask {
  id: string;
  title: string;
  category: TaskCategory;
  duration: string;
  isCompleted: boolean;
  categoryLabel: string;
  instruction?: string;
  rationale?: string;
}

export interface TaskState {
  tasks: DailyTask[];
  isLoading: boolean;
  setTasks: (tasks: DailyTask[]) => void;
  fetchTasks: (userId?: string) => Promise<void>;
  toggleTask: (id: string) => void;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  isLoading: false,

  setTasks: (tasks: DailyTask[]) => set({ tasks }),

  /**
   * Fetch actual task list from the SQLite database via Axios
   */
  fetchTasks: async (userId?: string) => {
    try {
      set({ isLoading: true });
      const rawTasks: TaskItemResponse[] = await apiService.getTasks(userId);

      if (rawTasks && Array.isArray(rawTasks)) {
        const mapped: DailyTask[] = rawTasks.map((t) => ({
          id: t.id,
          title: t.title,
          category: t.category,
          duration: t.duration || 'Daily',
          isCompleted: t.is_completed,
          categoryLabel: t.category_label || 'Daily Prep',
          instruction: t.instruction,
          rationale: t.rationale,
        }));
        set({ tasks: mapped, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.warn('⚠️ [useTaskStore] Failed to fetch tasks from database via Axios:', error);
      set({ isLoading: false });
    }
  },

  /**
   * Toggle task completion status optimistically and persist via Axios & Socket.IO
   */
  toggleTask: (id: string) => {
    const currentTask = get().tasks.find((t) => t.id === id);
    const newCompleted = currentTask ? !currentTask.isCompleted : true;

    // 1. Optimistic local state update
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === id ? { ...task, isCompleted: newCompleted } : task
      ),
    }));

    // 2. Synchronize in real-time via Socket.IO
    socketService.emit('task_toggle', {
      taskId: id,
      isCompleted: newCompleted,
    });

    // 3. Persist change to database via Axios PATCH request
    apiService.toggleTask(id).catch((err) => {
      console.warn('⚠️ [useTaskStore] Failed to persist task toggle via Axios:', err);
    });
  },
}));
