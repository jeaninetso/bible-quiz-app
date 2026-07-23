import type { Book, Section } from '../types/book';

export function findSectionWithBook(
  books: Book[],
  sectionId: string | undefined,
): { book: Book; section: Section } | undefined {
  for (const book of books) {
    const section = book.sections.find((s) => String(s.id) === sectionId);
    if (section) return { book, section };
  }
  return undefined;
}
