import { z } from 'zod';
import type { Passage } from '../types/passage';

const passageSchema = z.object({
  reference: z.string(),
  text: z.string(),
});

export function validatePassage(data: unknown): Passage {
  return passageSchema.parse(data);
}
