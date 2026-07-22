import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AchievementScreen } from './AchievementScreen';

const BOOKS = [{ id: 8, code: 'Ruth', name: 'Ruth', testament: 'old', chapterCount: 4, isAvailable: true }];

const BASE_RESULT = {
  id: 1,
  score: 2,
  totalQuestions: 2,
  questions: [],
  xpEarned: 30,
  progress: { xp: 30, level: 2, currentStreak: 3, longestStreak: 3, bestScore: 2, quizzesCompleted: 4 },
  newBadges: [] as { code: string; name: string; description: string }[],
};

function stubBooksFetch() {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(BOOKS), { status: 200 })));
}

function renderAt(state: unknown) {
  render(
    <MemoryRouter initialEntries={[{ pathname: '/quiz/8/achievements', state }]}>
      <Routes>
        <Route path="/" element={<p>Library screen</p>} />
        <Route path="/quiz/:bookId/achievements" element={<AchievementScreen />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('AchievementScreen', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows earned badges with their emoji, name, and description', async () => {
    stubBooksFetch();
    renderAt({ ...BASE_RESULT, newBadges: [{ code: 'first_quiz', name: 'First Steps', description: 'Complete your first quiz' }] });

    expect(await screen.findByText('First Steps')).toBeInTheDocument();
    expect(screen.getByText('Complete your first quiz')).toBeInTheDocument();
    expect(screen.getByText('🌱')).toBeInTheDocument();
    expect(screen.getByText(/ruth quiz complete/i)).toBeInTheDocument();
  });

  it('shows an empty state when no new badge was earned', async () => {
    stubBooksFetch();
    renderAt(BASE_RESULT);

    expect(await screen.findByText(/no new badge this time/i)).toBeInTheDocument();
  });

  it('shows level, streak, and XP stats regardless of badge state', async () => {
    stubBooksFetch();
    renderAt(BASE_RESULT);

    expect(await screen.findByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('+30')).toBeInTheDocument();
  });

  it('navigates back to the library on "Back to Books"', async () => {
    stubBooksFetch();
    const user = userEvent.setup();
    renderAt(BASE_RESULT);

    await user.click(await screen.findByRole('button', { name: /back to books/i }));
    expect(await screen.findByText(/library screen/i)).toBeInTheDocument();
  });

  it('redirects to the library when reached with no result in state', async () => {
    stubBooksFetch();
    renderAt(null);

    expect(await screen.findByText(/library screen/i)).toBeInTheDocument();
  });
});
