import { useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import { validatePassage } from '../data/validatePassage';
import type { Passage } from '../types/passage';
import type { Book } from '../types/book';
import './PassagePreview.css';

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; passage: Passage };

interface PassagePreviewProps {
  book: Book;
}

export function PassagePreview({ book }: PassagePreviewProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    fetchJson(`/books/${book.id}/passage`)
      .then((data) => {
        if (!cancelled) setState({ status: 'loaded', passage: validatePassage(data) });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load passage' });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [book.id]);

  return (
    <div className="passage-preview">
      <div className="passage-preview__reference">{book.name} (ESV)</div>
      {state.status === 'loading' && <p role="status">Fetching from the ESV API…</p>}
      {state.status === 'error' && (
        <p role="alert" className="passage-preview__error">
          Couldn't load the passage: {state.message}
        </p>
      )}
      {state.status === 'loaded' && <p className="passage-preview__text">{state.passage.text}</p>}
    </div>
  );
}
