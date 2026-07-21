import type { QuestionResult } from '../types/quiz';
import './QuizQuestionReview.css';

interface QuizQuestionReviewProps {
  result: QuestionResult;
}

// Shared between QuizView's post-submit results and QuizHistory's review —
// correct/incorrect is never color-only: each option also gets a text tag
// so the distinction reads without relying on color perception.
export function QuizQuestionReview({ result }: QuizQuestionReviewProps) {
  return (
    <li className="quiz-view__question">
      <p className="quiz-view__question-text">{result.question}</p>
      <div className="quiz-view__options">
        {result.options.map((option, optionIndex) => {
          const isCorrectOption = optionIndex === result.correctIndex;
          const isSelectedOption = optionIndex === result.selectedIndex;
          const className =
            'quiz-view__option' +
            (isCorrectOption
              ? ' quiz-view__option--correct'
              : isSelectedOption
                ? ' quiz-view__option--incorrect'
                : ' quiz-view__option--disabled');
          return (
            <button key={optionIndex} type="button" disabled className={className}>
              {option}
              {isCorrectOption && <span className="quiz-view__option-tag"> — correct answer</span>}
              {isSelectedOption && !isCorrectOption && <span className="quiz-view__option-tag"> — your answer</span>}
            </button>
          );
        })}
      </div>
      <p className="quiz-view__explanation">{result.explanation}</p>
    </li>
  );
}
