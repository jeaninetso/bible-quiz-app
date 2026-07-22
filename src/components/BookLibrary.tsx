import { useNavigate } from 'react-router-dom';
import { useBooks } from '../lib/useBooks';
import type { Book } from '../types/book';
import { BookCard } from './BookCard';
import './BookLibrary.css';

function groupByTestament(books: Book[]) {
  return {
    old: books.filter((b) => b.testament === 'old'),
    new: books.filter((b) => b.testament === 'new'),
  };
}

export function BookLibrary() {
  const state = useBooks();
  const navigate = useNavigate();

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

  return (
    <div className="book-library">
      <div className="book-library__section">
        <div className="book-library__section-title">Old Testament</div>
        <div className="book-library__grid">
          {old.map((book) => (
            <BookCard key={book.id} book={book} onSelect={(b) => navigate(`/quiz/${b.id}`)} />
          ))}
        </div>
      </div>
      <div className="book-library__section">
        <div className="book-library__section-title">New Testament</div>
        <div className="book-library__grid">
          {newTestament.map((book) => (
            <BookCard key={book.id} book={book} onSelect={(b) => navigate(`/quiz/${b.id}`)} />
          ))}
        </div>
      </div>
    </div>
  );
}
