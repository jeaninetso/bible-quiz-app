import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuizView } from './QuizView';
import type { Book } from '../types/book';

const RUTH: Book = { id: 8, code: 'Ruth', name: 'Ruth', testament: 'old', chapterCount: 4, isAvailable: true };

const QUIZ_RESPONSE = {
  id: 1,
  bookId: 8,
  bookName: 'Ruth',
  chapterReference: 'Ruth',
  questions: [
    { question: 'Who was Ruth’s mother-in-law?', options: ['Naomi', 'Orpah', 'Rachel', 'Leah'] },
    { question: 'What was Ruth’s nationality?', options: ['Moabite', 'Edomite', 'Ammonite', 'Philistine'] },
  ],
  funFacts: [{ fact: 'Ruth is an ancestor of King David.' }],
};

describe('QuizView', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders generated questions, options, and fun facts', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 })));
    render(<QuizView book={RUTH} />);

    expect(await screen.findByText(/who was ruth’s mother-in-law/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Naomi' })).toBeInTheDocument();
    expect(screen.getByText(/ancestor of king david/i)).toBeInTheDocument();
  });

  it('never receives correct-answer data in the response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 })));
    render(<QuizView book={RUTH} />);

    await screen.findByText(/who was ruth’s mother-in-law/i);
    expect(JSON.stringify(QUIZ_RESPONSE)).not.toMatch(/correct/i);
  });

  it('lets the user select an option without revealing correctness', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 })));
    const user = userEvent.setup();
    render(<QuizView book={RUTH} />);

    const option = await screen.findByRole('button', { name: 'Naomi' });
    await user.click(option);
    expect(option).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows an error state when the fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Claude API request failed' }), { status: 502 })),
    );
    render(<QuizView book={RUTH} />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/claude api request failed/i);
  });
});
