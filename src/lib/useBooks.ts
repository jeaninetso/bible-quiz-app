import { useEffect, useState } from 'react';
import { fetchJson } from './api';
import { validateBooks } from '../data/validateBooks';
import type { Book } from '../types/book';

type BooksState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'loaded'; books: Book[] };

export function useBooks() {
  const [state, setState] = useState<BooksState>({ status: 'loading' });

  useEffect(() => {
    fetchJson('/books')
      .then((data) => setState({ status: 'loaded', books: validateBooks(data) }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load books' });
      });
  }, []);

  return state;
}
