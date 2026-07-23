import { z } from 'zod';
import type { QuizAttempt, QuizResult, MeStats, QuizHistoryGroup, QuizReview } from '../types/quiz';

const questionSchema = z.object({
  question: z.string(),
  options: z.array(z.string()),
});

const funFactSchema = z.object({
  fact: z.string(),
});

const quizAttemptSchema = z.object({
  id: z.number(),
  bookId: z.number(),
  bookName: z.string(),
  sectionId: z.number().nullable(),
  sectionName: z.string().nullable(),
  chapterReference: z.string(),
  questions: z.array(questionSchema),
  funFacts: z.array(funFactSchema),
});

export function validateQuizAttempt(data: unknown): QuizAttempt {
  return quizAttemptSchema.parse(data);
}

const questionResultSchema = z.object({
  question: z.string(),
  options: z.array(z.string()),
  correctIndex: z.number(),
  explanation: z.string(),
  selectedIndex: z.number().nullable(),
  isCorrect: z.boolean(),
});

const badgeSchema = z.object({
  code: z.string(),
  name: z.string(),
  description: z.string(),
});

const earnedBadgeSchema = badgeSchema.extend({
  earnedAt: z.string(),
});

const progressSchema = z.object({
  xp: z.number(),
  level: z.number(),
  currentStreak: z.number(),
  longestStreak: z.number(),
  bestScore: z.number(),
  quizzesCompleted: z.number(),
});

const quizResultSchema = z.object({
  id: z.number(),
  score: z.number(),
  totalQuestions: z.number(),
  questions: z.array(questionResultSchema),
  xpEarned: z.number(),
  progress: progressSchema,
  newBadges: z.array(badgeSchema),
});

export function validateQuizResult(data: unknown): QuizResult {
  return quizResultSchema.parse(data);
}

const meStatsSchema = z.object({
  totalXp: z.number(),
  level: z.number(),
  currentStreak: z.number(),
  longestStreak: z.number(),
  quizzesCompleted: z.number(),
  badges: z.array(earnedBadgeSchema),
});

export function validateMeStats(data: unknown): MeStats {
  return meStatsSchema.parse(data);
}

const quizHistoryAttemptSchema = z.object({
  id: z.number(),
  score: z.number(),
  totalQuestions: z.number(),
  submittedAt: z.string(),
});

const quizHistoryGroupSchema = z.object({
  bookId: z.number(),
  bookName: z.string(),
  sectionId: z.number().nullable(),
  sectionName: z.string().nullable(),
  attemptCount: z.number(),
  mostRecentScore: z.number(),
  mostRecentTotalQuestions: z.number(),
  mostRecentSubmittedAt: z.string(),
  attempts: z.array(quizHistoryAttemptSchema),
});

export function validateQuizHistory(data: unknown): QuizHistoryGroup[] {
  return z.array(quizHistoryGroupSchema).parse(data);
}

const quizReviewSchema = z.object({
  id: z.number(),
  bookName: z.string(),
  sectionId: z.number().nullable(),
  sectionName: z.string().nullable(),
  chapterReference: z.string(),
  score: z.number(),
  totalQuestions: z.number(),
  submittedAt: z.string(),
  questions: z.array(questionResultSchema),
});

export function validateQuizReview(data: unknown): QuizReview {
  return quizReviewSchema.parse(data);
}
