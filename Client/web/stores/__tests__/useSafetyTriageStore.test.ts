import { describe, it, expect, beforeEach } from 'vitest';
import { useSafetyTriageStore, SafetyEventItem } from '../useSafetyTriageStore';

describe('useSafetyTriageStore', () => {
  beforeEach(() => {
    useSafetyTriageStore.setState({
      events: [],
      selectedEvent: null,
      activeFilter: 'all',
      isConnected: false,
      isLoading: false,
    });
  });

  it('WEB-UNIT-STR-001: initializes with empty events and activeFilter all', () => {
    const state = useSafetyTriageStore.getState();
    expect(state.events).toEqual([]);
    expect(state.activeFilter).toBe('all');
    expect(state.selectedEvent).toBeNull();
    expect(state.isConnected).toBe(false);
  });

  it('WEB-UNIT-STR-002: addEvent appends unique event and prevents duplicates', () => {
    const event1: SafetyEventItem = {
      id: 'evt-1',
      patient_name: 'Sarah',
      conversation_id: 'conv-1',
      risk_level: 'critical',
      trigger: 'Severe chest pain reported',
      action: 'Advised emergency 999 call',
      status: 'open',
      created_at: new Date().toISOString(),
    };

    useSafetyTriageStore.getState().addEvent(event1);
    expect(useSafetyTriageStore.getState().events).toHaveLength(1);

    // Try adding the duplicate event
    useSafetyTriageStore.getState().addEvent(event1);
    expect(useSafetyTriageStore.getState().events).toHaveLength(1);
  });

  it('WEB-UNIT-STR-003: resolveEvent sets status to resolved', () => {
    const event1: SafetyEventItem = {
      id: 'evt-1',
      patient_name: 'Sarah',
      conversation_id: 'conv-1',
      risk_level: 'high',
      trigger: 'Fever of 39C',
      action: 'Contacted surgical triage line',
      status: 'open',
      created_at: new Date().toISOString(),
    };

    useSafetyTriageStore.getState().addEvent(event1);
    useSafetyTriageStore.getState().setSelectedEvent(event1);

    useSafetyTriageStore.getState().resolveEvent('evt-1');

    const state = useSafetyTriageStore.getState();
    expect(state.events[0].status).toBe('resolved');
    expect(state.selectedEvent?.status).toBe('resolved');
  });

  it('WEB-UNIT-STR-004: setActiveFilter updates active filter state', () => {
    useSafetyTriageStore.getState().setActiveFilter('critical');
    expect(useSafetyTriageStore.getState().activeFilter).toBe('critical');
  });
});
