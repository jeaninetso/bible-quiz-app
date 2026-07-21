import { z } from 'zod';
import type { QuizAttempt, QuizResult } from '../types/quiz';

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

const quizResultSchema = z.object({
  id: z.number(),
  score: z.number(),
  totalQuestions: z.number(),
  questions: z.array(questionResultSchema),
});

export function validateQuizResult(data: unknown): QuizResult {
  return quizResultSchema.parse(data);
}
