import type { Book } from '../types/book';

interface BookCardProps {
  book: Book;
  onSelectSection: (sectionId: number) => void;
}

export function BookCard({ book, onSelectSection }: BookCardProps) {
  const chapters = `${book.chapterCount} ${book.chapterCount === 1 ? 'chapter' : 'chapters'}`;

  // No sections seeded yet — render exactly like the pre-Section "coming
  // soon" card. This covers the ~64 books that haven't been split yet.
  if (book.sections.length === 0) {
    return (
      <button type="button" className="book-card book-card--locked" disabled>
        <span className="book-card__name">{book.name}</span>
        <span className="book-card__meta">{chapters}</span>
        <span className="book-card__badge book-card__badge--locked">Coming soon</span>
      </button>
    );
  }

  // Exactly one section — same single-card shape as today, just routed
  // through the section (and gated on the section's own availability).
  if (book.sections.length === 1) {
    const section = book.sections[0];
    const classes = ['book-card', section.isAvailable ? 'book-card--available' : 'book-card--locked']
      .filter(Boolean)
      .join(' ');
    return (
      <button
        type="button"
        className={classes}
        disabled={!section.isAvailable}
        onClick={() => onSelectSection(section.id)}
      >
        <span className="book-card__name">{book.name}</span>
        <span className="book-card__meta">{chapters}</span>
        <span className={`book-card__badge book-card__badge--${section.isAvailable ? 'available' : 'locked'}`}>
          {section.isAvailable ? 'Ready' : 'Coming soon'}
        </span>
      </button>
    );
  }

  // Multiple sections — the book itself isn't a click target; each section
  // is its own independently-available pill.
  return (
    <div className="book-card book-card--multi">
      <span className="book-card__name">{book.name}</span>
      <span className="book-card__meta">{chapters}</span>
      <div className="book-card__sections">
        {book.sections.map((section) => (
          <button
            key={section.id}
            type="button"
            className={
              'book-card__section-pill' +
              (section.isAvailable ? ' book-card__section-pill--available' : ' book-card__section-pill--locked')
            }
            disabled={!section.isAvailable}
            aria-label={`${book.name} — ${section.name}`}
            onClick={() => onSelectSection(section.id)}
          >
            {section.name}
          </button>
        ))}
      </div>
    </div>
  );
}
