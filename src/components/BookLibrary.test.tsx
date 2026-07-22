import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { BookLibrary } from './BookLibrary';
import type { Book } from '../types/book';

const BOOKS: Book[] = [
  { id: 1, code: 'Gen', name: 'Genesis', testament: 'old', chapterCount: 50, isAvailable: false },
  { id: 8, code: 'Ruth', name: 'Ruth', testament: 'old', chapterCount: 4, isAvailable: true },
  { id: 40, code: 'Matt', name: 'Matthew', testament: 'new', chapterCount: 28, isAvailable: false },
];

function stubBooksFetch(books: Book[]) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(books), { status: 200 })));
}

function QuizRouteStub() {
  const { bookId } = useParams<{ bookId: string }>();
  return <p>Quiz route for book {bookId}</p>;
}

function renderWithRouter() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<BookLibrary />} />
        <Route path="/quiz/:bookId" element={<QuizRouteStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('BookLibrary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('groups books by testament and marks only available ones as clickable', async () => {
    stubBooksFetch(BOOKS);
    renderWithRouter();

    expect(await screen.findByText('Ruth')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /genesis/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /matthew/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /ruth/i })).toBeEnabled();
  });

  it('navigates to the quiz route when an available book is picked', async () => {
    stubBooksFetch(BOOKS);
    const user = userEvent.setup();
    renderWithRouter();

    await user.click(await screen.findByRole('button', { name: /ruth/i }));
    expect(await screen.findByText(/quiz route for book 8/i)).toBeInTheDocument();
  });
});
