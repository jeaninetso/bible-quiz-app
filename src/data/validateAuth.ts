import { z } from 'zod';
import type { CurrentUser } from '../types/auth';

const currentUserSchema = z.object({
  username: z.string(),
});

export function validateCurrentUser(data: unknown): CurrentUser {
  return currentUserSchema.parse(data);
}
