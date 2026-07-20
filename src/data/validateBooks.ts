import { z } from 'zod';
import type { Book } from '../types/book';

const bookSchema = z.object({
  id: z.number(),
  code: z.string(),
  name: z.string(),
  testament: z.union([z.literal('old'), z.literal('new')]),
  chapterCount: z.number(),
  isAvailable: z.boolean(),
});

export function validateBooks(data: unknown): Book[] {
  return z.array(bookSchema).parse(data);
}
