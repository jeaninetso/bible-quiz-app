export interface Question {
  question: string;
  options: string[];
}

export interface FunFact {
  fact: string;
}

export interface QuizAttempt {
  id: number;
  bookId: number;
  bookName: string;
  chapterReference: string;
  questions: Question[];
  funFacts: FunFact[];
}

export interface QuestionResult {
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  selectedIndex: number | null;
  isCorrect: boolean;
}

export interface QuizResult {
  id: number;
  score: number;
  totalQuestions: number;
  questions: QuestionResult[];
}
