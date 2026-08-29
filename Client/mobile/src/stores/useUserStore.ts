import { create } from 'zustand';
import { apiService, UserProfileResponse, HomeDataResponse } from '@/services/apiService';
import { useTaskStore, DailyTask, TaskCategory } from '@/stores/useTaskStore';

export interface MilestoneBadge {
  id: string;
  title: string;
  iconName: string;
  color: string;
  bgGradient: [string, string];
}

export interface UserState {
  id: string;
  name: string;
  email: string;
  avatarUri: string;
  plan: string;
  greeting: string;
  surgeryTitle: string;
  daysAway: number;
  procedureName: string;
  streakCount: number;
  completedDays: number[];
  badges: MilestoneBadge[];
  isLoading: boolean;
  setStreakCount: (count: number) => void;
  incrementStreak: () => void;
  fetchUser: (userId?: string) => Promise<void>;
  fetchHomeData: (patientId?: string) => Promise<void>;
}

const mapTypeToCategory = (type: string): TaskCategory => {
  switch (type.toLowerCase()) {
    case 'walking':
    case 'walk':
      return 'walking';
    case 'mindfulness':
    case 'mindset':
      return 'mindset';
    case 'nutrition':
    case 'hydration':
      return 'nutrition';
    default:
      return 'recovery';
  }
};

const mapCategoryToLabel = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'walking':
      return 'Movement';
    case 'mindfulness':
      return 'Mindset';
    case 'nutrition':
      return 'Nutrition';
    default:
      return 'Daily Prep';
  }
};

export const useUserStore = create<UserState>((set) => ({
  id: 'patient-sarah',
  name: 'Sarah',
  email: 'sarah@clovo.app',
  avatarUri: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
  plan: 'Pre-Op Preparation',
  greeting: 'Good morning',
  surgeryTitle: 'Your surgery',
  daysAway: 21,
  procedureName: 'Knee Surgery',
  streakCount: 5,
  completedDays: [1, 2, 3, 4, 5],
  isLoading: false,
  badges: [
    {
      id: 'yoga',
      title: 'Yoga Milestone',
      iconName: 'fitness',
      color: '#4F46E5',
      bgGradient: ['#E0E7FF', '#C7D2FE'],
    },
    {
      id: 'run',
      title: '5K Completed',
      iconName: 'walk',
      color: '#EC4899',
      bgGradient: ['#FCE7F3', '#FBCFE8'],
    },
    {
      id: 'core',
      title: 'Core Strength',
      iconName: 'barbell',
      color: '#10B981',
      bgGradient: ['#D1FAE5', '#A7F3D0'],
    },
  ],

  setStreakCount: (count) => set({ streakCount: count }),

  incrementStreak: () =>
    set((state) => ({
      streakCount: state.streakCount + 1,
      completedDays: [...state.completedDays, state.streakCount + 1],
    })),

  /**
   * Fetch actual user profile data from the SQLite database via Axios
   */
  fetchUser: async (userId?: string) => {
    try {
      set({ isLoading: true });
      const user: UserProfileResponse = await apiService.getUser(userId);

      set({
        id: user.id || 'patient-sarah',
        name: user.name || 'Sarah',
        email: user.email || 'sarah@clovo.app',
        avatarUri: user.avatar_uri || 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
        plan: user.plan || 'Pre-Op Preparation',
        streakCount: user.streak_count ?? 5,
        greeting: user.greeting ? user.greeting.split(',')[0] : 'Good morning',
        surgeryTitle: user.surgery_title || 'Your surgery',
        daysAway: user.days_away ?? 21,
        procedureName: user.procedure_name || 'Knee Surgery',
        isLoading: false,
      });
    } catch (error) {
      console.warn('⚠️ [useUserStore] Failed to fetch user from database via Axios:', error);
      set({ isLoading: false });
    }
  },

  /**
   * Fetch aggregated home dashboard data from backend via Axios
   */
  fetchHomeData: async (patientId?: string) => {
    try {
      set({ isLoading: true });
      const data: HomeDataResponse = await apiService.getHomeData(patientId);

      set({
        name: data.patient_name || 'Sarah',
        greeting: data.greeting ? data.greeting.split(',')[0] : 'Good morning',
        surgeryTitle: data.surgery_title || 'Your surgery',
        daysAway: data.days_away ?? 21,
        procedureName: data.procedure_name || 'Knee Surgery',
        isLoading: false,
      });

      if (data.preparations && Array.isArray(data.preparations)) {
        const mappedTasks: DailyTask[] = data.preparations.map((prep) => ({
          id: prep.id,
          title: prep.title,
          category: mapTypeToCategory(prep.type),
          duration: prep.type === 'walking' ? '15 mins' : prep.type === 'mindfulness' ? '10 mins' : 'Daily',
          isCompleted: prep.is_completed,
          categoryLabel: mapCategoryToLabel(prep.type),
        }));

        useTaskStore.getState().setTasks(mappedTasks);
      }
    } catch (error) {
      console.warn('⚠️ [useUserStore] Failed to fetch home data from backend via Axios:', error);
      set({ isLoading: false });
    }
  },
}));
