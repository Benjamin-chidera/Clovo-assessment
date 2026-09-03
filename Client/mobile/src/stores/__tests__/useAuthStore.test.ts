import { useAuthStore, PRE_OP_USER, POST_OP_USER } from '../useAuthStore';
import { useSocketStore } from '../useSocketStore';

const mockConnect = jest.fn();
const mockDisconnect = jest.fn();

// Mock socket connection
jest.mock('../useSocketStore', () => ({
  useSocketStore: {
    getState: () => ({
      connect: mockConnect,
      disconnect: mockDisconnect,
    }),
  },
}));

describe('useAuthStore - Multi-User Login & Switching', () => {
  beforeEach(() => {
    useAuthStore.setState({
      isAuthenticated: false,
      user: PRE_OP_USER,
      isProfileModalOpen: false,
    });
    jest.clearAllMocks();
  });

  it('MOB-UNIT-AUTH-001: defaults to PRE_OP_USER (Sarah)', () => {
    const state = useAuthStore.getState();
    expect(state.user?.name).toBe('Sarah');
    expect(state.user?.phase).toBe('pre-op');
    expect(state.isAuthenticated).toBe(false);
  });

  it('MOB-UNIT-AUTH-002: login as Sarah connects socket and sets authenticated', () => {
    useAuthStore.getState().login(PRE_OP_USER);

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.name).toBe('Sarah');
    expect(state.user?.id).toBe('patient-sarah');
    expect(state.user?.phase).toBe('pre-op');
    expect(useSocketStore.getState().connect).toHaveBeenCalledWith('patient-sarah');
  });

  it('MOB-UNIT-AUTH-003: login as Jane connects socket with patient-jane and sets post-op phase', () => {
    useAuthStore.getState().login(POST_OP_USER);

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.name).toBe('Jane');
    expect(state.user?.id).toBe('patient-jane');
    expect(state.user?.phase).toBe('post-op');
    expect(useSocketStore.getState().connect).toHaveBeenCalledWith('patient-jane');
  });

  it('MOB-UNIT-AUTH-004: switchUser disconnects old session and connects with new user', () => {
    useAuthStore.getState().login(PRE_OP_USER);
    useAuthStore.getState().switchUser(POST_OP_USER);

    const state = useAuthStore.getState();
    expect(state.user?.name).toBe('Jane');
    expect(state.user?.phase).toBe('post-op');
    expect(useSocketStore.getState().disconnect).toHaveBeenCalled();
    expect(useSocketStore.getState().connect).toHaveBeenCalledWith('patient-jane');
  });

  it('MOB-UNIT-AUTH-005: logout disconnects socket and resets isAuthenticated', () => {
    useAuthStore.getState().login(PRE_OP_USER);
    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(useSocketStore.getState().disconnect).toHaveBeenCalled();
  });
});
