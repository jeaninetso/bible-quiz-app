import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

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
});
