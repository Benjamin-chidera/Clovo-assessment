import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TopNavbar } from '../TopNavbar';
import { useSafetyTriageStore } from '../../stores/useSafetyTriageStore';

describe('TopNavbar', () => {
  beforeEach(() => {
    useSafetyTriageStore.setState({
      events: [],
      selectedEvent: null,
      activeFilter: 'all',
      isConnected: true,
      isLoading: false,
    });
  });

  it('WEB-UNIT-CMP-001: renders title and subtitle correctly', () => {
    render(
      <TopNavbar
        title="Clinical Safety Dashboard"
        subtitle="Real-Time Patient Risk & Symptom Oversight"
      />
    );

    expect(screen.getByText('Clinical Safety Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Real-Time Patient Risk & Symptom Oversight')).toBeInTheDocument();
    expect(screen.getByText('Real-Time Stream')).toBeInTheDocument();
    expect(screen.getByText('All Clear')).toBeInTheDocument();
  });

  it('WEB-UNIT-CMP-002: renders critical alert banner when high risk event is open', () => {
    useSafetyTriageStore.setState({
      events: [
        {
          id: 'alert-1',
          conversation_id: 'c1',
          risk_level: 'critical',
          trigger: 'Severe chest pain reported',
          action: 'Advised immediate 999 call',
          status: 'open',
          created_at: new Date().toISOString(),
        },
      ],
      isConnected: true,
    });

    render(<TopNavbar title="Safety Monitor" />);

    expect(screen.getByText('1 High/Critical Alerts')).toBeInTheDocument();
  });

  it('WEB-UNIT-CMP-003: renders reconnecting indicator when socket is disconnected', () => {
    useSafetyTriageStore.setState({ isConnected: false });

    render(<TopNavbar title="Safety Monitor" />);

    expect(screen.getByText('Reconnecting...')).toBeInTheDocument();
  });
});
