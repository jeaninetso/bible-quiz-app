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

const RESULT_RESPONSE = {
  id: 1,
  score: 1,
  totalQuestions: 2,
  questions: [
    {
      question: 'Who was Ruth’s mother-in-law?',
      options: ['Naomi', 'Orpah', 'Rachel', 'Leah'],
      correctIndex: 0,
      explanation: 'Naomi was Ruth’s mother-in-law.',
      selectedIndex: 0,
      isCorrect: true,
    },
    {
      question: 'What was Ruth’s nationality?',
      options: ['Moabite', 'Edomite', 'Ammonite', 'Philistine'],
      correctIndex: 0,
      explanation: 'Ruth was from Moab.',
      selectedIndex: 1,
      isCorrect: false,
    },
  ],
};

function stubQuizAndSubmitFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/submit')) {
        return Promise.resolve(new Response(JSON.stringify(RESULT_RESPONSE), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 }));
    }),
  );
}

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

  it('disables Submit Quiz until every question is answered', async () => {
    stubQuizAndSubmitFetch();
    const user = userEvent.setup();
    render(<QuizView book={RUTH} />);

    await screen.findByRole('button', { name: 'Naomi' });
    const submit = screen.getByRole('button', { name: /submit quiz/i });
    expect(submit).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Naomi' }));
    expect(submit).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Moabite' }));
    expect(submit).toBeEnabled();
  });

  it('submits selected answers and shows scored results with explanations', async () => {
    stubQuizAndSubmitFetch();
    const user = userEvent.setup();
    render(<QuizView book={RUTH} />);

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: 'Edomite' }));
    await user.click(screen.getByRole('button', { name: /submit quiz/i }));

    expect(await screen.findByText(/you scored 1 out of 2/i)).toBeInTheDocument();
    expect(screen.getByText(/naomi was ruth’s mother-in-law/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Naomi' })).toBeDisabled();
  });

  it('shows an error and keeps the quiz answerable when submission fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/submit')) {
          return Promise.resolve(new Response(JSON.stringify({ detail: 'This quiz attempt was already submitted' }), { status: 409 }));
        }
        return Promise.resolve(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 }));
      }),
    );
    const user = userEvent.setup();
    render(<QuizView book={RUTH} />);

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: 'Edomite' }));
    await user.click(screen.getByRole('button', { name: /submit quiz/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/already submitted/i);
    expect(screen.getByRole('button', { name: 'Naomi' })).toBeEnabled();
  });
});
