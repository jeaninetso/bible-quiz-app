import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatsBar } from './StatsBar';

const STATS_RESPONSE = {
  totalXp: 130,
  level: 2,
  currentStreak: 3,
  longestStreak: 5,
  quizzesCompleted: 4,
  badges: [
    { code: 'first_quiz', name: 'First Steps', description: 'Complete your first quiz', earnedAt: '2026-01-10T00:00:00' },
  ],
};

describe('StatsBar', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders XP, level, streak, quiz count, and badges', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(STATS_RESPONSE), { status: 200 })));
    render(<StatsBar refreshKey={0} />);

    expect(await screen.findByText('130')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('First Steps')).toBeInTheDocument();
  });

  it('shows an error state when the fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'API returned 500' }), { status: 500 })),
    );
    render(<StatsBar refreshKey={0} />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/api returned 500/i);
  });

  it('refetches when refreshKey changes', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(STATS_RESPONSE), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    const { rerender } = render(<StatsBar refreshKey={0} />);
    await screen.findByText('130');
    expect(fetchMock).toHaveBeenCalledTimes(1);

    rerender(<StatsBar refreshKey={1} />);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
