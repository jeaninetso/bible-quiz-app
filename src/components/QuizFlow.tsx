import { useEffect, useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { postJson } from '../lib/api';
import { validateQuizAttempt, validateQuizResult } from '../data/validateQuiz';
import type { QuizAttempt, QuizResult } from '../types/quiz';
import { useBooks } from '../lib/useBooks';
import { QuizQuestionReview } from './QuizQuestionReview';
import './QuizFlow.css';

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; quiz: QuizAttempt };
type SubmitState = { status: 'idle' } | { status: 'submitting' } | { status: 'error'; message: string };
type Stage = 'answering' | 'summary' | 'review';

interface QuizFlowProps {
  onSubmitted?: () => void;
}

export function QuizFlow({ onSubmitted }: QuizFlowProps) {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const booksState = useBooks();

  const [state, setState] = useState<LoadState>({ status: 'loading' });
  // Selection only until submitted — picking an answer doesn't reveal
  // correctness or send anything to the server until "Submit Quiz".
  const [selections, setSelections] = useState<Record<number, number>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [stage, setStage] = useState<Stage>('answering');
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitState, setSubmitState] = useState<SubmitState>({ status: 'idle' });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    setSelections({});
    setCurrentIndex(0);
    setStage('answering');
    setResult(null);
    setSubmitState({ status: 'idle' });
    postJson(`/books/${bookId}/quiz`, {})
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
  }, [bookId]);

  const [showExitConfirm, setShowExitConfirm] = useState(false);

  const book = booksState.status === 'loaded' ? booksState.books.find((b) => String(b.id) === bookId) : undefined;
  if (booksState.status === 'loaded' && (!book || !book.isAvailable)) {
    return <Navigate to="/" replace />;
  }

  const exitButton = (
    <button type="button" className="btn btn-ghost quiz-flow__exit" onClick={() => setShowExitConfirm(true)}>
      Exit Quiz
    </button>
  );

  const exitModal = showExitConfirm && (
    <div className="quiz-flow__modal-overlay" role="presentation" onClick={() => setShowExitConfirm(false)}>
      <div
        className="quiz-flow__modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="exit-quiz-title"
        onClick={(e) => e.stopPropagation()}
      >
        <p id="exit-quiz-title" className="quiz-flow__modal-title">
          Exit this quiz?
        </p>
        <p className="quiz-flow__modal-body">Your progress on this attempt won't be saved.</p>
        <div className="quiz-flow__modal-actions">
          <button type="button" className="btn btn-ghost" onClick={() => setShowExitConfirm(false)}>
            Keep Going
          </button>
          <button type="button" className="btn btn-primary" onClick={() => navigate('/')}>
            Exit Quiz
          </button>
        </div>
      </div>
    </div>
  );

  if (state.status !== 'loaded') {
    return (
      <div className="quiz-flow">
        <div className="quiz-flow__header">
          <div className="quiz-flow__reference">{book ? `${book.name} Quiz` : ''}</div>
          {exitButton}
        </div>
        {state.status === 'loading' && (
          <div className="quiz-flow__loading" role="status">
            <span className="quiz-flow__loading-icon" aria-hidden="true">
              📖
            </span>
            <p className="quiz-flow__loading-text">
              Generating your quiz
              <span className="quiz-flow__loading-dots" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
            </p>
          </div>
        )}
        {state.status === 'error' && (
          <p role="alert" className="quiz-flow__error">
            Couldn't load the quiz: {state.message}
          </p>
        )}
        {exitModal}
      </div>
    );
  }

  const quiz = state.quiz;
  const totalQuestions = quiz.questions.length;
  const question = quiz.questions[currentIndex];
  const isLastQuestion = currentIndex === totalQuestions - 1;
  const currentAnswered = selections[currentIndex] !== undefined;

  function handleSubmit() {
    setSubmitState({ status: 'submitting' });
    const answers = quiz.questions.map((_, i) => selections[i] ?? null);
    postJson(`/quiz-attempts/${quiz.id}/submit`, { answers })
      .then((data) => {
        setResult(validateQuizResult(data));
        setSubmitState({ status: 'idle' });
        setStage('summary');
      })
      .catch((err: unknown) => {
        setSubmitState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to submit quiz' });
      });
  }

  function handleContinue() {
    onSubmitted?.();
    navigate(`/quiz/${bookId}/achievements`, { state: result });
  }

  if (stage === 'answering') {
    return (
      <div className="quiz-flow">
        <div className="quiz-flow__header">
          <div className="quiz-flow__reference">{quiz.bookName} Quiz</div>
          {exitButton}
        </div>
        <div className="quiz-flow__progress">
          <div className="quiz-flow__dots">
            {quiz.questions.map((_, i) => (
              <span
                key={i}
                className={
                  'quiz-flow__dot' +
                  (i === currentIndex ? ' quiz-flow__dot--current' : selections[i] !== undefined ? ' quiz-flow__dot--done' : '')
                }
              />
            ))}
          </div>
          <span className="quiz-flow__progress-label">
            Question {currentIndex + 1} of {totalQuestions}
          </span>
        </div>

        <div className="quiz-view__question">
          <p className="quiz-view__question-text">{question.question}</p>
          <div className="quiz-view__options">
            {question.options.map((option, optionIndex) => (
              <button
                key={optionIndex}
                type="button"
                className={
                  'quiz-view__option' + (selections[currentIndex] === optionIndex ? ' quiz-view__option--selected' : '')
                }
                aria-pressed={selections[currentIndex] === optionIndex}
                onClick={() => setSelections((prev) => ({ ...prev, [currentIndex]: optionIndex }))}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="quiz-flow__nav">
          <button
            type="button"
            className="btn btn-ghost"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((i) => i - 1)}
          >
            Back
          </button>
          {isLastQuestion ? (
            <button
              type="button"
              className="btn btn-primary"
              disabled={!currentAnswered || submitState.status === 'submitting'}
              onClick={handleSubmit}
            >
              {submitState.status === 'submitting' ? 'Submitting…' : 'Submit Quiz'}
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-primary"
              disabled={!currentAnswered}
              onClick={() => setCurrentIndex((i) => i + 1)}
            >
              Next
            </button>
          )}
        </div>
        {submitState.status === 'error' && (
          <p role="alert" className="quiz-flow__error">
            Couldn't submit the quiz: {submitState.message}
          </p>
        )}
        {exitModal}
      </div>
    );
  }

  // stage is 'summary' or 'review' past this point — result is always set once submitted.
  const finalResult = result!;
  const passed = finalResult.score > finalResult.totalQuestions / 2;

  if (stage === 'review') {
    return (
      <div className="quiz-flow">
        <div className="quiz-flow__header">
          <div className="quiz-flow__reference">{quiz.bookName} Quiz</div>
          {exitButton}
        </div>
        <div className="quiz-flow__review-top-actions">
          <button type="button" className="btn btn-ghost" onClick={() => setStage('summary')}>
            ← Back to Results
          </button>
          <button type="button" className="btn btn-primary" onClick={handleContinue}>
            Continue
          </button>
        </div>
        <ol className="quiz-view__questions">
          {finalResult.questions.map((q, i) => (
            <QuizQuestionReview key={i} result={q} />
          ))}
        </ol>
        {exitModal}
      </div>
    );
  }

  return (
    <div className="quiz-flow">
      <div className="quiz-flow__header">
        <div className="quiz-flow__reference">{quiz.bookName} Quiz</div>
        {exitButton}
      </div>
      <div className={'quiz-flow__summary-banner' + (passed ? ' quiz-flow__summary-banner--pass' : ' quiz-flow__summary-banner--fail')}>
        <p className="quiz-flow__summary-score">
          {finalResult.score} / {finalResult.totalQuestions}
        </p>
        <p className="quiz-flow__summary-line">
          {passed ? 'You passed' : 'Not quite this time'} — +{finalResult.xpEarned} XP earned
        </p>
        <p className="quiz-flow__summary-line">
          Level {finalResult.progress.level} · {finalResult.progress.currentStreak}-day streak
        </p>
      </div>
      <div className="quiz-flow__summary-actions">
        <button type="button" className="btn btn-ghost" onClick={() => setStage('review')}>
          Review My Answers
        </button>
        <button type="button" className="btn btn-primary" onClick={handleContinue}>
          Continue
        </button>
      </div>
      {quiz.funFacts.length > 0 && (
        <div className="quiz-view__fun-facts">
          <div className="quiz-view__fun-facts-title">Fun Facts</div>
          <ul>
            {quiz.funFacts.map((f, i) => (
              <li key={i}>{f.fact}</li>
            ))}
          </ul>
        </div>
      )}
      {exitModal}
    </div>
  );
}
