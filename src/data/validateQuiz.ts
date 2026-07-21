import { z } from 'zod';
import type { QuizAttempt, QuizResult, MeStats } from '../types/quiz';

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
