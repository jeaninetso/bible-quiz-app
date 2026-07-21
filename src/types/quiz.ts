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

export interface Badge {
  code: string;
  name: string;
  description: string;
}

export interface EarnedBadge extends Badge {
  earnedAt: string;
}

export interface UserBookProgress {
  xp: number;
  level: number;
  currentStreak: number;
  longestStreak: number;
  bestScore: number;
  quizzesCompleted: number;
}

export interface QuizResult {
  id: number;
  score: number;
  totalQuestions: number;
  questions: QuestionResult[];
  xpEarned: number;
  progress: UserBookProgress;
  newBadges: Badge[];
}

export interface MeStats {
  totalXp: number;
  level: number;
  currentStreak: number;
  longestStreak: number;
  quizzesCompleted: number;
  badges: EarnedBadge[];
}

export interface QuizHistoryItem {
  id: number;
  bookId: number;
  bookName: string;
  chapterReference: string;
  score: number;
  totalQuestions: number;
  submittedAt: string;
}

export interface QuizReview {
  id: number;
  bookName: string;
  chapterReference: string;
  score: number;
  totalQuestions: number;
  submittedAt: string;
  questions: QuestionResult[];
}
