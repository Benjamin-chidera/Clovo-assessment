import { useUserStore } from '../useUserStore';

describe('useUserStore', () => {
  beforeEach(() => {
    useUserStore.setState({
      id: '1',
      name: 'Sarah',
      email: 'sarah@clovo.app',
      avatarUri: '',
      plan: 'Pre-Op Preparation',
      greeting: 'Good morning, Sarah',
      surgeryTitle: 'Your surgery',
      daysAway: 14,
      procedureName: 'Knee Surgery',
      streakCount: 5,
      completedDays: [],
      badges: [],
      additionalMilestonesCount: 0,
      totalCompletedTasks: 12,
      isLoading: false,
    });
  });

  it('MOB-UNIT-STR-008: increments streak count correctly', () => {
    useUserStore.getState().incrementStreak();
    expect(useUserStore.getState().streakCount).toBe(6);
  });

  it('MOB-UNIT-STR-009: setStreakCount updates streak count', () => {
    useUserStore.getState().setStreakCount(10);
    expect(useUserStore.getState().streakCount).toBe(10);
  });

  it('MOB-UNIT-STR-010: updateStats refreshes streak and badges', () => {
    const badge = {
      id: 'm1',
      title: 'First Step',
      iconName: 'trophy',
      color: '#10B981',
      bgGradient: ['#D1FAE5', '#A7F3D0'] as [string, string],
    };
    useUserStore.getState().updateStats({
      streakCount: 8,
      milestones: [badge],
      additionalMilestonesCount: 2,
    });

    const state = useUserStore.getState();
    expect(state.streakCount).toBe(8);
    expect(state.badges).toHaveLength(1);
    expect(state.additionalMilestonesCount).toBe(2);
  });
});
