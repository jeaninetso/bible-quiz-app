import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { QuizFlow } from './QuizFlow';

const BOOKS = [
  {
    id: 8,
    code: 'Ruth',
    name: 'Ruth',
    testament: 'old',
    chapterCount: 4,
    isAvailable: true,
    sections: [{ id: 201, bookId: 8, name: 'Ruth 1–2', isAvailable: true }],
  },
];

const QUIZ_RESPONSE = {
  id: 1,
  bookId: 8,
  bookName: 'Ruth',
  sectionId: 201,
  sectionName: 'Ruth 1–2',
  chapterReference: 'Ruth 1-2',
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
  xpEarned: 30,
  progress: { xp: 30, level: 1, currentStreak: 1, longestStreak: 1, bestScore: 1, quizzesCompleted: 1 },
  newBadges: [{ code: 'first_quiz', name: 'First Steps', description: 'Complete your first quiz' }],
};

function stubQuizFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/books')) return Promise.resolve(new Response(JSON.stringify(BOOKS), { status: 200 }));
      return Promise.resolve(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 }));
    }),
  );
}

function stubQuizAndSubmitFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/books')) return Promise.resolve(new Response(JSON.stringify(BOOKS), { status: 200 }));
      if (url.includes('/submit')) return Promise.resolve(new Response(JSON.stringify(RESULT_RESPONSE), { status: 200 }));
      return Promise.resolve(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 }));
    }),
  );
}

function AchievementsRouteStub() {
  const location = useLocation();
  return <p>Achievements screen, newBadges: {(location.state as typeof RESULT_RESPONSE)?.newBadges.length}</p>;
}

function renderQuizFlow(onSubmitted?: () => void) {
  render(
    <MemoryRouter initialEntries={['/quiz/201']}>
      <Routes>
        <Route path="/quiz/:sectionId" element={<QuizFlow onSubmitted={onSubmitted} />} />
        <Route path="/quiz/:sectionId/achievements" element={<AchievementsRouteStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('QuizFlow', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows only the first question, one at a time', async () => {
    stubQuizFetch();
    renderQuizFlow();

    expect(await screen.findByText(/who was ruth’s mother-in-law/i)).toBeInTheDocument();
    expect(screen.queryByText(/what was ruth’s nationality/i)).not.toBeInTheDocument();
    expect(screen.getByText(/question 1 of 2/i)).toBeInTheDocument();
  });

  it('never receives correct-answer data in the response', async () => {
    stubQuizFetch();
    renderQuizFlow();

    await screen.findByText(/who was ruth’s mother-in-law/i);
    expect(JSON.stringify(QUIZ_RESPONSE)).not.toMatch(/correct/i);
  });

  it('advances to the next question only once the current one is answered', async () => {
    stubQuizFetch();
    const user = userEvent.setup();
    renderQuizFlow();

    await screen.findByText(/who was ruth’s mother-in-law/i);
    const next = screen.getByRole('button', { name: /next/i });
    expect(next).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Naomi' }));
    expect(next).toBeEnabled();

    await user.click(next);
    expect(await screen.findByText(/what was ruth’s nationality/i)).toBeInTheDocument();
    expect(screen.getByText(/question 2 of 2/i)).toBeInTheDocument();
  });

  it('shows Submit Quiz only on the last question, disabled until answered', async () => {
    stubQuizFetch();
    const user = userEvent.setup();
    renderQuizFlow();

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: /next/i }));

    await screen.findByText(/what was ruth’s nationality/i);
    const submit = screen.getByRole('button', { name: /submit quiz/i });
    expect(submit).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Moabite' }));
    expect(submit).toBeEnabled();
  });

  it('going Back returns to the previous question and keeps the prior selection', async () => {
    stubQuizFetch();
    const user = userEvent.setup();
    renderQuizFlow();

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: /next/i }));
    await screen.findByText(/what was ruth’s nationality/i);

    await user.click(screen.getByRole('button', { name: /back/i }));
    expect(await screen.findByText(/who was ruth’s mother-in-law/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Naomi' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows an error state when the quiz fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/books')) return Promise.resolve(new Response(JSON.stringify(BOOKS), { status: 200 }));
        return Promise.resolve(new Response(JSON.stringify({ detail: 'Claude API request failed' }), { status: 502 }));
      }),
    );
    renderQuizFlow();
    expect(await screen.findByRole('alert')).toHaveTextContent(/claude api request failed/i);
  });

  it('submits answers and shows the summary stage with Review/Continue actions', async () => {
    stubQuizAndSubmitFetch();
    const user = userEvent.setup();
    renderQuizFlow();

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: /next/i }));
    await user.click(await screen.findByRole('button', { name: 'Edomite' }));
    await user.click(screen.getByRole('button', { name: /submit quiz/i }));

    expect(await screen.findByText(/1 \/ 2/)).toBeInTheDocument();
    expect(screen.getByText(/\+30 xp/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /review my answers/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument();
  });

  it('Review My Answers shows the full breakdown with correct/incorrect tags', async () => {
    stubQuizAndSubmitFetch();
    const user = userEvent.setup();
    renderQuizFlow();

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: /next/i }));
    await user.click(await screen.findByRole('button', { name: 'Edomite' }));
    await user.click(screen.getByRole('button', { name: /submit quiz/i }));

    await user.click(await screen.findByRole('button', { name: /review my answers/i }));
    expect(screen.getByText(/naomi was ruth’s mother-in-law/i)).toBeInTheDocument();
    expect(screen.getAllByText(/correct answer/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /back to results/i })).toBeInTheDocument();
  });

  it('Continue navigates to the achievements screen with the result and calls onSubmitted', async () => {
    stubQuizAndSubmitFetch();
    const onSubmitted = vi.fn();
    const user = userEvent.setup();
    renderQuizFlow(onSubmitted);

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: /next/i }));
    await user.click(await screen.findByRole('button', { name: 'Edomite' }));
    await user.click(screen.getByRole('button', { name: /submit quiz/i }));

    await user.click(await screen.findByRole('button', { name: /^continue$/i }));
    expect(await screen.findByText(/achievements screen, newbadges: 1/i)).toBeInTheDocument();
    expect(onSubmitted).toHaveBeenCalledTimes(1);
  });

  it('shows an error and keeps the quiz answerable when submission fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/books')) return Promise.resolve(new Response(JSON.stringify(BOOKS), { status: 200 }));
        if (url.includes('/submit')) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: 'This quiz attempt was already submitted' }), { status: 409 }),
          );
        }
        return Promise.resolve(new Response(JSON.stringify(QUIZ_RESPONSE), { status: 200 }));
      }),
    );
    const user = userEvent.setup();
    renderQuizFlow();

    await user.click(await screen.findByRole('button', { name: 'Naomi' }));
    await user.click(screen.getByRole('button', { name: /next/i }));
    await user.click(await screen.findByRole('button', { name: 'Edomite' }));
    await user.click(screen.getByRole('button', { name: /submit quiz/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/already submitted/i);
    expect(screen.getByRole('button', { name: 'Edomite' })).toBeEnabled();
  });
});
