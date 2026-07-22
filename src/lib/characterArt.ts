import daniel from '../assets/characters/daniel-character-nobg.png';
import david from '../assets/characters/david-character-nobg.png';
import esther from '../assets/characters/esther-character-nobg.png';
import jonah from '../assets/characters/jonah-character-nobg.png';
import moses from '../assets/characters/moses-character-nobg.png';
import noah from '../assets/characters/noah-character-nobg.png';
import ruth from '../assets/characters/ruth-character-nobg.png';

// Keyed by Book.code (backend/scripts/seed_books.py). Books without an
// entry here just render without character art.
const CHARACTER_ART: Record<string, string> = {
  Gen: noah,
  Exod: moses,
  Ruth: ruth,
  '1Sam': david,
  Esth: esther,
  Dan: daniel,
  Jonah: jonah,
};

export function characterArt(code: string): string | undefined {
  return CHARACTER_ART[code];
}
