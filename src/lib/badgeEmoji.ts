// Maps each badge catalog code (backend/scripts/seed_badges.py) to a display
// emoji. Falls back to a generic star for any badge added without a frontend
// update, so the UI never breaks on an unmapped code.
const BADGE_EMOJI: Record<string, string> = {
  first_quiz: '🌱',
  perfect_score: '💯',
  streak_3: '🔥',
  streak_7: '⚡',
  quiz_master_10: '🏆',
};

export function badgeEmoji(code: string): string {
  return BADGE_EMOJI[code] ?? '⭐';
}
