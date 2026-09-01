import { create } from 'zustand';
import { apiService, UserProfileResponse, HomeDataResponse } from '@/services/apiService';
import { useTaskStore, DailyTask, TaskCategory } from '@/stores/useTaskStore';

export interface MilestoneBadge {
  id: string;
  code?: string;
  title: string;
  description?: string;
  iconName: string;
  color: string;
  bgGradient: [string, string];
  unlockedAt?: string;
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
  additionalMilestonesCount: number;
  totalCompletedTasks: number;
  isLoading: boolean;
  setStreakCount: (count: number) => void;
  incrementStreak: () => void;
  updateStats: (stats: { streakCount?: number; milestones?: MilestoneBadge[]; additionalMilestonesCount?: number }) => void;
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

const formatMilestones = (rawMilestones?: any[]): MilestoneBadge[] => {
  if (!rawMilestones || !Array.isArray(rawMilestones) || rawMilestones.length === 0) {
    return [];
  }

  return rawMilestones.map((m) => ({
    id: m.id || m.code || String(Math.random()),
    code: m.code,
    title: m.title || 'Milestone',
    description: m.description,
    iconName: m.icon_name || m.iconName || 'trophy',
    color: m.color || '#4F46E5',
    bgGradient: Array.isArray(m.bg_gradient)
      ? [m.bg_gradient[0] || '#E0E7FF', m.bg_gradient[1] || '#C7D2FE']
      : Array.isArray(m.bgGradient)
      ? m.bgGradient
      : ['#E0E7FF', '#C7D2FE'],
    unlockedAt: m.unlocked_at || m.unlockedAt,
  }));
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
  streakCount: 0,
  completedDays: [],
  badges: [],
  additionalMilestonesCount: 0,
  totalCompletedTasks: 0,
  isLoading: false,


  setStreakCount: (count) => set({ streakCount: count }),

  incrementStreak: () =>
    set((state) => ({
      streakCount: state.streakCount + 1,
      completedDays: [...state.completedDays, state.streakCount + 1],
    })),

  updateStats: (stats) =>
    set((state) => ({
      streakCount: stats.streakCount ?? state.streakCount,
      badges: stats.milestones ? formatMilestones(stats.milestones) : state.badges,
      additionalMilestonesCount: stats.additionalMilestonesCount ?? state.additionalMilestonesCount,
    })),

  /**
   * Fetch actual user profile data from the SQLite database via Axios
   */
  fetchUser: async (userId?: string) => {
    try {
      set({ isLoading: true });
      const user: UserProfileResponse = await apiService.getUser(userId);

      const parsedBadges = formatMilestones(user.milestones);
      const addCount = user.additional_milestones_count ?? Math.max(0, parsedBadges.length - 3);

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
        badges: parsedBadges,
        additionalMilestonesCount: addCount,
        totalCompletedTasks: user.total_completed_tasks ?? parsedBadges.length,
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

      const parsedBadges = formatMilestones(data.milestones);
      const addCount = data.additional_milestones_count ?? Math.max(0, parsedBadges.length - 3);

      set({
        name: data.patient_name || 'Sarah',
        greeting: data.greeting ? data.greeting.split(',')[0] : 'Good morning',
        surgeryTitle: data.surgery_title || 'Your surgery',
        daysAway: data.days_away ?? 21,
        procedureName: data.procedure_name || 'Knee Surgery',
        streakCount: data.streak_count ?? 5,
        badges: parsedBadges,
        additionalMilestonesCount: addCount,
        totalCompletedTasks: data.total_completed_tasks ?? parsedBadges.length,
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

