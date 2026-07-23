import { z } from 'zod';
import type { Book } from '../types/book';

const sectionSchema = z.object({
  id: z.number(),
  bookId: z.number(),
  name: z.string(),
  isAvailable: z.boolean(),
});

const bookSchema = z.object({
  id: z.number(),
  code: z.string(),
  name: z.string(),
  testament: z.union([z.literal('old'), z.literal('new')]),
  chapterCount: z.number(),
  isAvailable: z.boolean(),
  sections: z.array(sectionSchema),
});

export function validateBooks(data: unknown): Book[] {
  return z.array(bookSchema).parse(data);
}
