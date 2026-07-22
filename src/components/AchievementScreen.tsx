import { Navigate, useLocation, useNavigate, useParams } from 'react-router-dom';
import type { QuizResult } from '../types/quiz';
import { useBooks } from '../lib/useBooks';
import { badgeEmoji } from '../lib/badgeEmoji';
import './AchievementScreen.css';

export function AchievementScreen() {
  const { bookId } = useParams<{ bookId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const booksState = useBooks();

  const result = location.state as QuizResult | null;
  if (!result) {
    // This screen only makes sense right after a submission — a direct nav
    // or a refresh has nothing to show, so send them back to the library.
    return <Navigate to="/" replace />;
  }

  const book = booksState.status === 'loaded' ? booksState.books.find((b) => String(b.id) === bookId) : undefined;

  return (
    <div className="achieve">
      <p className="achieve__result">{book ? `${book.name} Quiz Complete` : 'Quiz Complete'}</p>

      {result.newBadges.length > 0 ? (
        <div className="achieve__badges">
          {result.newBadges.map((badge) => (
            <div key={badge.code} className="achieve__badge">
              <div className="achieve__badge-ring">
                <span className="achieve__badge-emoji">{badgeEmoji(badge.code)}</span>
              </div>
              <p className="achieve__badge-name">{badge.name}</p>
              <p className="achieve__badge-description">{badge.description}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="achieve__empty">
          <p className="achieve__empty-title">No new badge this time</p>
          <p className="achieve__empty-line">Keep your streak going — the next one's closer than you think.</p>
        </div>
      )}

      <div className="achieve__stats">
        <div className="achieve__stat">
          <span className="achieve__stat-value">{result.progress.level}</span>
          <span className="achieve__stat-label">Level</span>
        </div>
        <div className="achieve__stat">
          <span className="achieve__stat-value">{result.progress.currentStreak}</span>
          <span className="achieve__stat-label">Day streak</span>
        </div>
        <div className="achieve__stat">
          <span className="achieve__stat-value">+{result.xpEarned}</span>
          <span className="achieve__stat-label">XP earned</span>
        </div>
      </div>

      <button type="button" className="btn btn-ghost" onClick={() => navigate('/')}>
        Back to Books
      </button>
    </div>
  );
}
