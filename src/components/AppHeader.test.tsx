import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppHeader } from './AppHeader';

const STATS_RESPONSE = {
  totalXp: 130,
  level: 2,
  currentStreak: 3,
  longestStreak: 5,
  quizzesCompleted: 4,
  badges: [],
};

describe('AppHeader', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows the greeting, sign-out, and stats on the library route', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(STATS_RESPONSE), { status: 200 })));

    render(
      <MemoryRouter initialEntries={['/']}>
        <AppHeader user={{ username: 'jeanine' }} onLogout={vi.fn()} statsRefreshKey={0} />
      </MemoryRouter>,
    );

    expect(screen.getByText(/welcome back/i)).toHaveTextContent('jeanine');
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    expect(await screen.findByText('130')).toBeInTheDocument();
  });

  it('hides stats but keeps the greeting and sign-out mid-quiz', () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(STATS_RESPONSE), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    render(
      <MemoryRouter initialEntries={['/quiz/201']}>
        <AppHeader user={{ username: 'jeanine' }} onLogout={vi.fn()} statsRefreshKey={0} />
      </MemoryRouter>,
    );

    expect(screen.getByText(/welcome back/i)).toHaveTextContent('jeanine');
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    expect(screen.queryByText('XP')).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
