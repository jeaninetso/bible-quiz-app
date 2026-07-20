import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PassagePreview } from './PassagePreview';
import type { Book } from '../types/book';

const RUTH: Book = { id: 8, code: 'Ruth', name: 'Ruth', testament: 'old', chapterCount: 4, isAvailable: true };

describe('PassagePreview', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the fetched ESV text', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ reference: 'Ruth', text: '[1] In the days...' }), { status: 200 })),
    );
    render(<PassagePreview book={RUTH} />);
    expect(await screen.findByText(/in the days/i)).toBeInTheDocument();
  });

  it('shows an error state when the fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'ESV API returned 401' }), { status: 502 })),
    );
    render(<PassagePreview book={RUTH} />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/esv api returned 401/i);
  });
});
