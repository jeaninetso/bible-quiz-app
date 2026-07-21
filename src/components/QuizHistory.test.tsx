import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuizHistory } from './QuizHistory';

const HISTORY_RESPONSE = [
  { id: 2, bookId: 8, bookName: 'Ruth', chapterReference: 'Ruth', score: 3, totalQuestions: 5, submittedAt: '2026-01-11T00:00:00' },
  { id: 1, bookId: 8, bookName: 'Ruth', chapterReference: 'Ruth', score: 5, totalQuestions: 5, submittedAt: '2026-01-10T00:00:00' },
];

const REVIEW_RESPONSE = {
  id: 2,
  bookName: 'Ruth',
  chapterReference: 'Ruth',
  score: 3,
  totalQuestions: 5,
  submittedAt: '2026-01-11T00:00:00',
  questions: [
    {
      question: 'Who was Ruth’s mother-in-law?',
      options: ['Naomi', 'Orpah', 'Rachel', 'Leah'],
      correctIndex: 0,
      explanation: 'Naomi was Ruth’s mother-in-law.',
      selectedIndex: 0,
      isCorrect: true,
    },
  ],
};

function stubHistoryFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (/\/quiz-attempts\/\d+$/.test(url)) {
        return Promise.resolve(new Response(JSON.stringify(REVIEW_RESPONSE), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify(HISTORY_RESPONSE), { status: 200 }));
    }),
  );
}

describe('QuizHistory', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('lists past attempts newest first with score and date', async () => {
    stubHistoryFetch();
    render(<QuizHistory />);

    const items = await screen.findAllByRole('button', { expanded: false });
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent('3 / 5');
    expect(items[1]).toHaveTextContent('5 / 5');
  });

  it('shows an empty state when there is no history yet', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify([]), { status: 200 })));
    render(<QuizHistory />);
    expect(await screen.findByText(/haven't completed a quiz yet/i)).toBeInTheDocument();
  });

  it('shows an error state when the list fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'API returned 500' }), { status: 500 })),
    );
    render(<QuizHistory />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/api returned 500/i);
  });

  it('expands an item to load and show its full review', async () => {
    stubHistoryFetch();
    const user = userEvent.setup();
    render(<QuizHistory />);

    const [firstItem] = await screen.findAllByRole('button', { expanded: false });
    await user.click(firstItem);

    expect(await screen.findByText(/who was ruth’s mother-in-law/i)).toBeInTheDocument();
    expect(firstItem).toHaveAttribute('aria-expanded', 'true');
  });

  it('shows an error when loading a specific review fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (/\/quiz-attempts\/\d+$/.test(url)) {
          return Promise.resolve(new Response(JSON.stringify({ detail: 'API returned 500' }), { status: 500 }));
        }
        return Promise.resolve(new Response(JSON.stringify(HISTORY_RESPONSE), { status: 200 }));
      }),
    );
    const user = userEvent.setup();
    render(<QuizHistory />);

    const [firstItem] = await screen.findAllByRole('button', { expanded: false });
    await user.click(firstItem);

    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't load this attempt/i);
  });

  it('collapses an expanded item on a second click', async () => {
    stubHistoryFetch();
    const user = userEvent.setup();
    render(<QuizHistory />);

    const [firstItem] = await screen.findAllByRole('button', { expanded: false });
    await user.click(firstItem);
    await screen.findByText(/who was ruth’s mother-in-law/i);

    await user.click(firstItem);
    expect(firstItem).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText(/who was ruth’s mother-in-law/i)).not.toBeInTheDocument();
  });
});
