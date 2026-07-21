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
