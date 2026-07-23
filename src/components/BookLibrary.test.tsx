import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { BookLibrary } from './BookLibrary';
import type { Book } from '../types/book';

const BOOKS: Book[] = [
  {
    id: 1,
    code: 'Gen',
    name: 'Genesis',
    testament: 'old',
    chapterCount: 50,
    isAvailable: true,
    sections: [
      { id: 101, bookId: 1, name: 'Primeval History', isAvailable: true },
      { id: 102, bookId: 1, name: 'Abraham', isAvailable: false },
    ],
  },
  {
    id: 8,
    code: 'Ruth',
    name: 'Ruth',
    testament: 'old',
    chapterCount: 4,
    isAvailable: true,
    sections: [{ id: 201, bookId: 8, name: 'Ruth 1–2', isAvailable: true }],
  },
  { id: 40, code: 'Matt', name: 'Matthew', testament: 'new', chapterCount: 28, isAvailable: false, sections: [] },
];

function stubBooksFetch(books: Book[]) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(books), { status: 200 })));
}

function QuizRouteStub() {
  const { sectionId } = useParams<{ sectionId: string }>();
  return <p>Quiz route for section {sectionId}</p>;
}

function renderWithRouter() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<BookLibrary />} />
        <Route path="/quiz/:sectionId" element={<QuizRouteStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('BookLibrary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders a book with no sections as a single locked "coming soon" card', async () => {
    stubBooksFetch(BOOKS);
    renderWithRouter();

    expect(await screen.findByText('Matthew')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /matthew/i })).toBeDisabled();
  });

  it('renders a book with exactly one section as a single card gated on section availability', async () => {
    stubBooksFetch(BOOKS);
    renderWithRouter();

    expect(await screen.findByText('Ruth')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ruth/i })).toBeEnabled();
  });

  it('renders a book with multiple sections as independently-available pills', async () => {
    stubBooksFetch(BOOKS);
    renderWithRouter();

    expect(await screen.findByText('Genesis')).toBeInTheDocument();
    const available = screen.getByRole('button', { name: /genesis — primeval history/i });
    const locked = screen.getByRole('button', { name: /genesis — abraham/i });
    expect(available).toBeEnabled();
    expect(locked).toBeDisabled();
  });

  it('navigates to the quiz route for the section when an available single-section book is picked', async () => {
    stubBooksFetch(BOOKS);
    const user = userEvent.setup();
    renderWithRouter();

    await user.click(await screen.findByRole('button', { name: /ruth/i }));
    expect(await screen.findByText(/quiz route for section 201/i)).toBeInTheDocument();
  });

  it('navigates to the quiz route for the specific section pill picked', async () => {
    stubBooksFetch(BOOKS);
    const user = userEvent.setup();
    renderWithRouter();

    await user.click(await screen.findByRole('button', { name: /genesis — primeval history/i }));
    expect(await screen.findByText(/quiz route for section 101/i)).toBeInTheDocument();
  });
});
