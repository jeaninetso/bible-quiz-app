import { useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import { validateBooks } from '../data/validateBooks';
import type { Book } from '../types/book';
import { BookCard } from './BookCard';
import { QuizView } from './QuizView';
import './BookLibrary.css';

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; books: Book[] };

function groupByTestament(books: Book[]) {
  return {
    old: books.filter((b) => b.testament === 'old'),
    new: books.filter((b) => b.testament === 'new'),
  };
}

export function BookLibrary() {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    fetchJson('/books')
      .then((data) => setState({ status: 'loaded', books: validateBooks(data) }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load books' });
      });
  }, []);

  if (state.status === 'loading') {
    return <p role="status">Loading the library…</p>;
  }
  if (state.status === 'error') {
    return (
      <p role="alert" className="book-library__error">
        Couldn't load books: {state.message}
      </p>
    );
  }

  const { old, new: newTestament } = groupByTestament(state.books);
  const selectedBook = state.books.find((b) => b.id === selectedId) ?? null;

  return (
    <div className="book-library">
      <div className="book-library__section">
        <div className="book-library__section-title">Old Testament</div>
        <div className="book-library__grid">
          {old.map((book) => (
            <BookCard key={book.id} book={book} selected={book.id === selectedId} onSelect={(b) => setSelectedId(b.id)} />
          ))}
        </div>
      </div>
      <div className="book-library__section">
        <div className="book-library__section-title">New Testament</div>
        <div className="book-library__grid">
          {newTestament.map((book) => (
            <BookCard key={book.id} book={book} selected={book.id === selectedId} onSelect={(b) => setSelectedId(b.id)} />
          ))}
        </div>
      </div>
      {selectedBook && <QuizView book={selectedBook} />}
    </div>
  );
}
