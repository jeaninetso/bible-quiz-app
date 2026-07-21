import { useEffect, useState } from 'react';
import { postJson } from '../lib/api';
import { validateQuizAttempt } from '../data/validateQuiz';
import type { QuizAttempt } from '../types/quiz';
import type { Book } from '../types/book';
import './QuizView.css';

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; quiz: QuizAttempt };

interface QuizViewProps {
  book: Book;
}

export function QuizView({ book }: QuizViewProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  // Selection only — scoring/submission arrives in Phase 6. Selecting an
  // answer here doesn't reveal correctness or send anything to the server.
  const [selections, setSelections] = useState<Record<number, number>>({});

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    setSelections({});
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

  return (
    <div className="quiz-view">
      <div className="quiz-view__reference">{book.name} Quiz</div>
      {state.status === 'loading' && <p role="status">Generating your quiz…</p>}
      {state.status === 'error' && (
        <p role="alert" className="quiz-view__error">
          Couldn't load the quiz: {state.message}
        </p>
      )}
      {state.status === 'loaded' && (
        <>
          <ol className="quiz-view__questions">
            {state.quiz.questions.map((q, questionIndex) => (
              <li key={questionIndex} className="quiz-view__question">
                <p className="quiz-view__question-text">{q.question}</p>
                <div className="quiz-view__options">
                  {q.options.map((option, optionIndex) => (
                    <button
                      key={optionIndex}
                      type="button"
                      className={
                        'quiz-view__option' +
                        (selections[questionIndex] === optionIndex ? ' quiz-view__option--selected' : '')
                      }
                      aria-pressed={selections[questionIndex] === optionIndex}
                      onClick={() => setSelections((prev) => ({ ...prev, [questionIndex]: optionIndex }))}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ol>
          <div className="quiz-view__fun-facts">
            <div className="quiz-view__fun-facts-title">Fun Facts</div>
            <ul>
              {state.quiz.funFacts.map((f, i) => (
                <li key={i}>{f.fact}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
