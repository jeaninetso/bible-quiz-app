import { useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import { validateQuizHistory, validateQuizReview } from '../data/validateQuiz';
import type { QuizHistoryGroup, QuizReview } from '../types/quiz';
import { QuizQuestionReview } from './QuizQuestionReview';
import './QuizHistory.css';

type ListState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; groups: QuizHistoryGroup[] };
type ReviewState = { status: 'idle' } | { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; review: QuizReview };

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function groupLabel(group: QuizHistoryGroup): string {
  return group.sectionName ? `${group.bookName} — ${group.sectionName}` : group.bookName;
}

function groupKey(group: QuizHistoryGroup): string {
  return `${group.bookId}:${group.sectionId ?? 'none'}`;
}

export function QuizHistory() {
  const [state, setState] = useState<ListState>({ status: 'loading' });
  const [expandedGroupKey, setExpandedGroupKey] = useState<string | null>(null);
  const [expandedAttemptId, setExpandedAttemptId] = useState<number | null>(null);
  const [review, setReview] = useState<ReviewState>({ status: 'idle' });

  useEffect(() => {
    fetchJson('/quiz-attempts')
      .then((data) => setState({ status: 'loaded', groups: validateQuizHistory(data) }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load quiz history' });
      });
  }, []);

  function loadAttemptReview(attemptId: number) {
    setExpandedAttemptId(attemptId);
    setReview({ status: 'loading' });
    fetchJson(`/quiz-attempts/${attemptId}`)
      .then((data) => setReview({ status: 'loaded', review: validateQuizReview(data) }))
      .catch((err: unknown) => {
        setReview({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load this attempt' });
      });
  }

  function toggleGroup(group: QuizHistoryGroup) {
    const key = groupKey(group);
    if (expandedGroupKey === key) {
      setExpandedGroupKey(null);
      setExpandedAttemptId(null);
      return;
    }
    setExpandedGroupKey(key);
    // A section taken only once skips straight to its review — the extra
    // "pick which attempt" list only earns its keep once there's a choice.
    if (group.attempts.length === 1) {
      loadAttemptReview(group.attempts[0].id);
    } else {
      setExpandedAttemptId(null);
      setReview({ status: 'idle' });
    }
  }

  function toggleAttempt(attemptId: number) {
    if (expandedAttemptId === attemptId) {
      setExpandedAttemptId(null);
      return;
    }
    loadAttemptReview(attemptId);
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
  if (state.groups.length === 0) {
    return <p className="quiz-history__empty">You haven't completed a quiz yet — pick a book to get started.</p>;
  }

  return (
    <ul className="quiz-history">
      {state.groups.map((group) => {
        const key = groupKey(group);
        const isGroupExpanded = expandedGroupKey === key;
        const showAttemptsList = isGroupExpanded && group.attempts.length > 1;

        return (
          <li key={key} className="quiz-history__item">
            <button
              type="button"
              className="quiz-history__summary"
              aria-expanded={isGroupExpanded}
              onClick={() => toggleGroup(group)}
            >
              <span className="quiz-history__book">{groupLabel(group)}</span>
              {group.attemptCount > 1 && <span className="quiz-history__count">{group.attemptCount}×</span>}
              <span className="quiz-history__score">
                {group.mostRecentScore} / {group.mostRecentTotalQuestions}
              </span>
              <span className="quiz-history__date">{formatDate(group.mostRecentSubmittedAt)}</span>
            </button>

            {showAttemptsList && (
              <ul className="quiz-history__attempts">
                {group.attempts.map((attempt) => {
                  const isAttemptExpanded = expandedAttemptId === attempt.id;
                  return (
                    <li key={attempt.id} className="quiz-history__attempt">
                      <button
                        type="button"
                        className="quiz-history__attempt-summary"
                        aria-expanded={isAttemptExpanded}
                        onClick={() => toggleAttempt(attempt.id)}
                      >
                        <span className="quiz-history__score">
                          {attempt.score} / {attempt.totalQuestions}
                        </span>
                        <span className="quiz-history__date">{formatDate(attempt.submittedAt)}</span>
                      </button>
                      {isAttemptExpanded && (
                        <div className="quiz-history__review">
                          {review.status === 'loading' && <p role="status">Loading this attempt…</p>}
                          {review.status === 'error' && (
                            <p role="alert" className="quiz-history__error">
                              Couldn't load this attempt: {review.message}
                            </p>
                          )}
                          {review.status === 'loaded' && review.review.id === attempt.id && (
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
            )}

            {isGroupExpanded && group.attempts.length === 1 && (
              <div className="quiz-history__review">
                {review.status === 'loading' && <p role="status">Loading this attempt…</p>}
                {review.status === 'error' && (
                  <p role="alert" className="quiz-history__error">
                    Couldn't load this attempt: {review.message}
                  </p>
                )}
                {review.status === 'loaded' && review.review.id === group.attempts[0].id && (
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
