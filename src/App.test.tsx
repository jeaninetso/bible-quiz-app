import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

const EMPTY_STATS = { totalXp: 0, level: 1, currentStreak: 0, longestStreak: 0, quizzesCompleted: 0, badges: [] };

function stubAuthenticatedFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/auth/me')) {
        return Promise.resolve(new Response(JSON.stringify({ username: 'jeanine' }), { status: 200 }));
      }
      if (url.includes('/me/stats')) {
        return Promise.resolve(new Response(JSON.stringify(EMPTY_STATS), { status: 200 }));
      }
      if (url.includes('/quiz-attempts')) {
        return Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));
      }
      if (url.includes('/books')) {
        return Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ detail: 'not found' }), { status: 404 }));
    }),
  );
}

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the hub title, then falls back to a login form when unauthenticated', async () => {
    // Real network calls are flaky/slow in a test environment — stub fetch so
    // /auth/me deterministically behaves like "no session cookie yet".
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Not authenticated' }), { status: 401 })),
    );

    render(<App />);
    expect(screen.getByText(/grow your bible knowledge/i)).toBeInTheDocument();
    expect(await screen.findByLabelText(/username/i)).toBeInTheDocument();
  });

  it('switches between the Books and History tabs when authenticated', async () => {
    stubAuthenticatedFetch();
    const user = userEvent.setup();
    render(<App />);

    const libraryTab = await screen.findByRole('tab', { name: /books/i });
    const historyTab = screen.getByRole('tab', { name: /history/i });
    expect(libraryTab).toHaveAttribute('aria-selected', 'true');
    expect(historyTab).toHaveAttribute('aria-selected', 'false');

    await user.click(historyTab);
    expect(historyTab).toHaveAttribute('aria-selected', 'true');
    expect(libraryTab).toHaveAttribute('aria-selected', 'false');
    expect(await screen.findByText(/haven't completed a quiz yet/i)).toBeInTheDocument();
  });
});
