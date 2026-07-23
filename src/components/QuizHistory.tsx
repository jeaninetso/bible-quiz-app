import { useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import { validateQuizHistory, validateQuizReview } from '../data/validateQuiz';
import type { QuizHistoryItem, QuizReview } from '../types/quiz';
import { QuizQuestionReview } from './QuizQuestionReview';
import './QuizHistory.css';

type ListState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; items: QuizHistoryItem[] };
type ReviewState = { status: 'idle' } | { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; review: QuizReview };

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function QuizHistory() {
  const [state, setState] = useState<ListState>({ status: 'loading' });
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [review, setReview] = useState<ReviewState>({ status: 'idle' });

  useEffect(() => {
    fetchJson('/quiz-attempts')
      .then((data) => setState({ status: 'loaded', items: validateQuizHistory(data) }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load quiz history' });
      });
  }, []);

  function toggleExpanded(id: number) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    setReview({ status: 'loading' });
    fetchJson(`/quiz-attempts/${id}`)
      .then((data) => setReview({ status: 'loaded', review: validateQuizReview(data) }))
      .catch((err: unknown) => {
        setReview({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load this attempt' });
      });
  }

  if (state.status === 'loading') {
    return <p role="status">Loading your quiz history…</p>;
  }
  if (state.status === 'error') {
    return (
      <p role="alert" className="quiz-history__error">
        Couldn't load your quiz history: {state.message}
      </p>
    );
  }
  if (state.items.length === 0) {
    return <p className="quiz-history__empty">You haven't completed a quiz yet — pick a book to get started.</p>;
  }

  return (
    <ul className="quiz-history">
      {state.items.map((item) => {
        const isExpanded = expandedId === item.id;
        return (
          <li key={item.id} className="quiz-history__item">
            <button
              type="button"
              className="quiz-history__summary"
              aria-expanded={isExpanded}
              onClick={() => toggleExpanded(item.id)}
            >
              <span className="quiz-history__book">{item.sectionName ?? item.bookName}</span>
              <span className="quiz-history__score">
                {item.score} / {item.totalQuestions}
              </span>
              <span className="quiz-history__date">{formatDate(item.submittedAt)}</span>
            </button>
            {isExpanded && (
              <div className="quiz-history__review">
                {review.status === 'loading' && <p role="status">Loading this attempt…</p>}
                {review.status === 'error' && (
                  <p role="alert" className="quiz-history__error">
                    Couldn't load this attempt: {review.message}
                  </p>
                )}
                {review.status === 'loaded' && review.review.id === item.id && (
                  <ol className="quiz-view__questions">
                    {review.review.questions.map((q, i) => (
                      <QuizQuestionReview key={i} result={q} />
                    ))}
                  </ol>
                )}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
