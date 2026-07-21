import { useEffect, useState } from 'react';
import { postJson } from '../lib/api';
import { validateQuizAttempt, validateQuizResult } from '../data/validateQuiz';
import type { QuizAttempt, QuizResult } from '../types/quiz';
import type { Book } from '../types/book';
import './QuizView.css';

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; quiz: QuizAttempt };
type SubmitState = { status: 'idle' } | { status: 'submitting' } | { status: 'error'; message: string };

interface QuizViewProps {
  book: Book;
  onSubmitted?: () => void;
}

function optionClassName(questionIndex: number, optionIndex: number, selections: Record<number, number>, result: QuizResult | null) {
  if (!result) {
    return 'quiz-view__option' + (selections[questionIndex] === optionIndex ? ' quiz-view__option--selected' : '');
  }
  const q = result.questions[questionIndex];
  if (optionIndex === q.correctIndex) return 'quiz-view__option quiz-view__option--correct';
  if (optionIndex === q.selectedIndex) return 'quiz-view__option quiz-view__option--incorrect';
  return 'quiz-view__option quiz-view__option--disabled';
}

export function QuizView({ book, onSubmitted }: QuizViewProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  // Selection only until submitted — picking an answer doesn't reveal
  // correctness or send anything to the server until "Submit Quiz".
  const [selections, setSelections] = useState<Record<number, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitState, setSubmitState] = useState<SubmitState>({ status: 'idle' });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    setSelections({});
    setResult(null);
    setSubmitState({ status: 'idle' });
    postJson(`/books/${book.id}/quiz`, {})
      .then((data) => {
        if (!cancelled) setState({ status: 'loaded', quiz: validateQuizAttempt(data) });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load quiz' });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [book.id]);

  if (state.status !== 'loaded') {
    return (
      <div className="quiz-view">
        <div className="quiz-view__reference">{book.name} Quiz</div>
        {state.status === 'loading' && <p role="status">Generating your quiz…</p>}
        {state.status === 'error' && (
          <p role="alert" className="quiz-view__error">
            Couldn't load the quiz: {state.message}
          </p>
        )}
      </div>
    );
  }

  const quiz = state.quiz;
  const allAnswered = quiz.questions.every((_, i) => selections[i] !== undefined);

  function handleSubmit() {
    setSubmitState({ status: 'submitting' });
    const answers = quiz.questions.map((_, i) => selections[i] ?? null);
    postJson(`/quiz-attempts/${quiz.id}/submit`, { answers })
      .then((data) => {
        setResult(validateQuizResult(data));
        setSubmitState({ status: 'idle' });
        onSubmitted?.();
      })
      .catch((err: unknown) => {
        setSubmitState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to submit quiz' });
      });
  }

  return (
    <div className="quiz-view">
      <div className="quiz-view__reference">{book.name} Quiz</div>
      {result && (
        <div className="quiz-view__result-banner" role="status">
          <p className="quiz-view__score">
            You scored {result.score} out of {result.totalQuestions} — +{result.xpEarned} XP
          </p>
          <p className="quiz-view__streak">
            Level {result.progress.level} · {result.progress.currentStreak}-day streak
          </p>
          {result.newBadges.length > 0 && (
            <ul className="quiz-view__new-badges">
              {result.newBadges.map((b) => (
                <li key={b.code} className="quiz-view__new-badge" title={b.description}>
                  New badge: {b.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      <ol className="quiz-view__questions">
        {quiz.questions.map((q, questionIndex) => (
          <li key={questionIndex} className="quiz-view__question">
            <p className="quiz-view__question-text">{q.question}</p>
            <div className="quiz-view__options">
              {q.options.map((option, optionIndex) => (
                <button
                  key={optionIndex}
                  type="button"
                  disabled={!!result}
                  className={optionClassName(questionIndex, optionIndex, selections, result)}
                  aria-pressed={selections[questionIndex] === optionIndex}
                  onClick={() => setSelections((prev) => ({ ...prev, [questionIndex]: optionIndex }))}
                >
                  {option}
                </button>
              ))}
            </div>
            {result && <p className="quiz-view__explanation">{result.questions[questionIndex].explanation}</p>}
          </li>
        ))}
      </ol>
      {!result && (
        <>
          <button
            type="button"
            className="quiz-view__submit"
            disabled={!allAnswered || submitState.status === 'submitting'}
            onClick={handleSubmit}
          >
            {submitState.status === 'submitting' ? 'Submitting…' : 'Submit Quiz'}
          </button>
          {submitState.status === 'error' && (
            <p role="alert" className="quiz-view__error">
              Couldn't submit the quiz: {submitState.message}
            </p>
          )}
        </>
      )}
      <div className="quiz-view__fun-facts">
        <div className="quiz-view__fun-facts-title">Fun Facts</div>
        <ul>
          {quiz.funFacts.map((f, i) => (
            <li key={i}>{f.fact}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
