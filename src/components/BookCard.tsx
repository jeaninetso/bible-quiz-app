import type { Book } from '../types/book';

interface BookCardProps {
  book: Book;
  selected: boolean;
  onSelect: (book: Book) => void;
}

export function BookCard({ book, selected, onSelect }: BookCardProps) {
  const classes = [
    'book-card',
    book.isAvailable ? 'book-card--available' : 'book-card--locked',
    selected ? 'book-card--selected' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type="button"
      className={classes}
      disabled={!book.isAvailable}
      aria-pressed={selected}
      onClick={() => onSelect(book)}
    >
      <span className="book-card__name">{book.name}</span>
      <span className="book-card__meta">
        {book.chapterCount} {book.chapterCount === 1 ? 'chapter' : 'chapters'}
      </span>
      <span className={`book-card__badge book-card__badge--${book.isAvailable ? 'available' : 'locked'}`}>
        {book.isAvailable ? 'Ready' : 'Coming soon'}
      </span>
    </button>
  );
}
