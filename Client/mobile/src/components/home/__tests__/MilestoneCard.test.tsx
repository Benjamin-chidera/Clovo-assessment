import React from 'react';
import { MilestoneCard } from '../MilestoneCard';
import { useUserStore } from '@/stores/useUserStore';

jest.mock('@/stores/useUserStore', () => ({
  useUserStore: jest.fn(),
}));

function extractText(node: any): string {
  if (!node) return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(extractText).join(' ');
  if (node.props && node.props.children) return extractText(node.props.children);
  return '';
}

describe('MilestoneCard - Pre-Op vs Post-Op Rendering', () => {
  const Component = (MilestoneCard as any).type || MilestoneCard;

  it('MOB-UNIT-CMP-005: renders pre-op countdown for Sarah without post-op day counter', () => {
    (useUserStore as unknown as jest.Mock).mockReturnValue({
      name: 'Sarah',
      phase: 'pre-op',
      surgeryTitle: 'Your surgery',
      daysAway: 16,
      daysPostOp: undefined,
      procedureName: 'Knee Surgery',
    });

    const tree = Component({});
    const text = extractText(tree);

    expect(text).toContain('16 days away');
    expect(text).toContain('Your surgery');
    expect(text).toContain('Knee Surgery Preparation Pathway');
    expect(text).not.toContain('Post-Op');
  });

  it('MOB-UNIT-CMP-006: renders post-op rehabilitation day counter for Jane', () => {
    (useUserStore as unknown as jest.Mock).mockReturnValue({
      name: 'Jane',
      phase: 'post-op',
      surgeryTitle: 'Day 6 Post-Op',
      daysAway: 0,
      daysPostOp: 6,
      procedureName: 'Knee Replacement',
    });

    const tree = Component({});
    const text = extractText(tree);

    expect(text).toContain('Day 6 Post-Op');
    expect(text).toContain('Post-Op Rehabilitation');
    expect(text).toContain('Knee Replacement Recovery Pathway');
    expect(text).not.toContain('days away');
  });
});
