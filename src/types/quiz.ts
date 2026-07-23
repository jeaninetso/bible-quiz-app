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
  sectionId: number | null;
  sectionName: string | null;
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

export interface QuizHistoryAttempt {
  id: number;
  score: number;
  totalQuestions: number;
  submittedAt: string;
}

export interface QuizHistoryGroup {
  bookId: number;
  bookName: string;
  sectionId: number | null;
  sectionName: string | null;
  attemptCount: number;
  mostRecentScore: number;
  mostRecentTotalQuestions: number;
  mostRecentSubmittedAt: string;
  attempts: QuizHistoryAttempt[];
}

export interface QuizReview {
  id: number;
  bookName: string;
  sectionId: number | null;
  sectionName: string | null;
  chapterReference: string;
  score: number;
  totalQuestions: number;
  submittedAt: string;
  questions: QuestionResult[];
}
