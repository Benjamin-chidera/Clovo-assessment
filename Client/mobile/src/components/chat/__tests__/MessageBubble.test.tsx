import React from 'react';
import { MessageBubble } from '../MessageBubble';
import { ChatMessage } from '@/stores/useChatStore';

// Mock RecoveryActivityCards
jest.mock('../RecoveryActivityCards', () => ({
  RecoveryActivityCards: () => null,
}));

function extractText(node: any): string {
  if (!node) return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(extractText).join(' ');
  if (node.props && node.props.children) return extractText(node.props.children);
  return '';
}

describe('MessageBubble', () => {
  const Component = (MessageBubble as any).type || MessageBubble;

  it('MOB-UNIT-CMP-001: renders user message bubble with user text and timestamp', () => {
    const userMsg: ChatMessage = {
      id: 'm1',
      sender: 'user',
      text: 'I completed my leg raises today',
      timestamp: '10:30 AM',
    };

    const tree = Component({ message: userMsg });
    const text = extractText(tree);
    expect(text).toContain('I completed my leg raises today');
    expect(text).toContain('10:30 AM');
  });

  it('MOB-UNIT-CMP-002: renders coach message bubble with supportive text', () => {
    const coachMsg: ChatMessage = {
      id: 'm2',
      sender: 'coach',
      text: 'Great effort Sarah! You are on a 5-day streak.',
      timestamp: '10:31 AM',
    };

    const tree = Component({ message: coachMsg });
    const text = extractText(tree);
    expect(text).toContain('Great effort Sarah! You are on a 5-day streak.');
  });

  it('MOB-UNIT-CMP-003: renders safety alert header when isSafetyAlert is true', () => {
    const alertMsg: ChatMessage = {
      id: 'm3',
      sender: 'coach',
      text: 'Please stop all exercises immediately and call 999.',
      timestamp: '10:32 AM',
      isSafetyAlert: true,
      riskLevel: 'critical',
    };

    const tree = Component({ message: alertMsg });
    const text = extractText(tree);
    expect(text).toContain('Urgent Medical Alert');
    expect(text).toContain('Please stop all exercises immediately and call 999.');
  });

  it('MOB-UNIT-CMP-004: renders clinical flag for moderate safety alerts', () => {
    const flagMsg: ChatMessage = {
      id: 'm4',
      sender: 'coach',
      text: 'I noted your knee swelling. Take a rest and ice the joint.',
      timestamp: '10:35 AM',
      isSafetyAlert: true,
      riskLevel: 'medium',
    };

    const tree = Component({ message: flagMsg });
    const text = extractText(tree);
    expect(text).toContain('Clinical Safety Flag');
    expect(text).toContain('I noted your knee swelling. Take a rest and ice the joint.');
  });
});
