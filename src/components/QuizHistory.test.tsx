import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuizHistory } from './QuizHistory';

const GROUPS_RESPONSE = [
  {
    bookId: 8,
    bookName: 'Ruth',
    sectionId: 201,
    sectionName: 'Ruth 1–2',
    attemptCount: 2,
    mostRecentScore: 3,
    mostRecentTotalQuestions: 5,
    mostRecentSubmittedAt: '2026-01-11T00:00:00',
    attempts: [
      { id: 2, score: 3, totalQuestions: 5, submittedAt: '2026-01-11T00:00:00' },
      { id: 1, score: 5, totalQuestions: 5, submittedAt: '2026-01-10T00:00:00' },
    ],
  },
  {
    bookId: 1,
    bookName: 'Genesis',
    sectionId: 101,
    sectionName: 'Abraham',
    attemptCount: 1,
    mostRecentScore: 5,
    mostRecentTotalQuestions: 5,
    mostRecentSubmittedAt: '2026-01-09T00:00:00',
    attempts: [{ id: 3, score: 5, totalQuestions: 5, submittedAt: '2026-01-09T00:00:00' }],
  },
];

function reviewFor(attemptId: number) {
  return {
    id: attemptId,
    bookName: 'Ruth',
    sectionId: 201,
    sectionName: 'Ruth 1–2',
    chapterReference: 'Ruth 1-2',
    score: 3,
    totalQuestions: 5,
    submittedAt: '2026-01-11T00:00:00',
    questions: [
      {
        question: `Question for attempt ${attemptId}?`,
        options: ['Naomi', 'Orpah', 'Rachel', 'Leah'],
        correctIndex: 0,
        explanation: 'Naomi was Ruth’s mother-in-law.',
        selectedIndex: 0,
        isCorrect: true,
      },
    ],
  };
}

function stubHistoryFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      const match = url.match(/\/quiz-attempts\/(\d+)$/);
      if (match) {
        return Promise.resolve(new Response(JSON.stringify(reviewFor(Number(match[1]))), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify(GROUPS_RESPONSE), { status: 200 }));
    }),
  );
}

describe('QuizHistory', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('lists groups newest first with most-recent score, date, and a retake count badge', async () => {
    stubHistoryFetch();
    render(<QuizHistory />);

    const items = await screen.findAllByRole('button', { expanded: false });
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent('Ruth — Ruth 1–2');
    expect(items[0]).toHaveTextContent('2×');
    expect(items[0]).toHaveTextContent('3 / 5');
    expect(items[1]).toHaveTextContent('Genesis — Abraham');
    expect(items[1]).not.toHaveTextContent('×');
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

  it('expands a group taken only once directly to its review, with no intermediate attempts list', async () => {
    stubHistoryFetch();
    const user = userEvent.setup();
    render(<QuizHistory />);

    const genesisGroup = await screen.findByRole('button', { name: /genesis — abraham/i });
    await user.click(genesisGroup);

    expect(await screen.findByText(/question for attempt 3/i)).toBeInTheDocument();
    expect(genesisGroup).toHaveAttribute('aria-expanded', 'true');
  });

  it('expands a retaken group to a list of individual attempts, each independently reviewable', async () => {
    stubHistoryFetch();
    const user = userEvent.setup();
    render(<QuizHistory />);

    const ruthGroup = await screen.findByRole('button', { name: /ruth — ruth 1–2/i });
    await user.click(ruthGroup);

    const attemptRows = await screen.findAllByRole('button', { expanded: false });
    // Both individual attempt rows should now be visible alongside the (now-expanded) group header.
    expect(attemptRows.some((r) => r.textContent?.includes('3 / 5'))).toBe(true);
    expect(attemptRows.some((r) => r.textContent?.includes('5 / 5'))).toBe(true);
    // No review shown yet — picking an attempt is a separate click.
    expect(screen.queryByText(/question for attempt/i)).not.toBeInTheDocument();

    const olderAttempt = attemptRows.find((r) => r.textContent?.includes('5 / 5'))!;
    await user.click(olderAttempt);
    expect(await screen.findByText(/question for attempt 1/i)).toBeInTheDocument();
  });

  it('shows an error when loading a specific review fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (/\/quiz-attempts\/\d+$/.test(url)) {
          return Promise.resolve(new Response(JSON.stringify({ detail: 'API returned 500' }), { status: 500 }));
        }
        return Promise.resolve(new Response(JSON.stringify(GROUPS_RESPONSE), { status: 200 }));
      }),
    );
    const user = userEvent.setup();
    render(<QuizHistory />);

    const genesisGroup = await screen.findByRole('button', { name: /genesis — abraham/i });
    await user.click(genesisGroup);

    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't load this attempt/i);
  });

  it('collapses an expanded single-attempt group on a second click', async () => {
    stubHistoryFetch();
    const user = userEvent.setup();
    render(<QuizHistory />);

    const genesisGroup = await screen.findByRole('button', { name: /genesis — abraham/i });
    await user.click(genesisGroup);
    await screen.findByText(/question for attempt 3/i);

    await user.click(genesisGroup);
    expect(genesisGroup).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText(/question for attempt 3/i)).not.toBeInTheDocument();
  });
});
