import { describe, it, expect, beforeEach } from 'vitest';
import { useAuditStore } from '../useAuditStore';

describe('useAuditStore', () => {
  beforeEach(() => {
    useAuditStore.setState({
      isAccessModalOpen: false,
      pendingConversationId: null,
      pendingPatientName: null,
      onAccessGrantedCallback: null,
    });
  });

  it('WEB-UNIT-STR-005: opens and closes access justification modal', () => {
    const onGrantedMock = (reason: string) => {};

    useAuditStore.getState().openAccessModal('conv-123', 'Sarah', onGrantedMock);

    let state = useAuditStore.getState();
    expect(state.isAccessModalOpen).toBe(true);
    expect(state.pendingConversationId).toBe('conv-123');
    expect(state.pendingPatientName).toBe('Sarah');

    useAuditStore.getState().closeAccessModal();

    state = useAuditStore.getState();
    expect(state.isAccessModalOpen).toBe(false);
    expect(state.pendingConversationId).toBeNull();
  });
});
