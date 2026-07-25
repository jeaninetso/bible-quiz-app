import { useLocation } from 'react-router-dom';
import type { CurrentUser } from '../types/auth';
import { ProtectedHome } from './ProtectedHome';
import { StatsBar } from './StatsBar';
import './AppHeader.css';

interface AppHeaderProps {
  user: CurrentUser;
  onLogout: () => void;
  statsRefreshKey: number;
}

// Sticky so sign-out and stats stay reachable while scrolling a 66-book
// library. Stats only render on the library route itself, same scoping
// StatsBar already had inside LibraryHome — mid-quiz just shows the
// greeting/sign-out row.
export function AppHeader({ user, onLogout, statsRefreshKey }: AppHeaderProps) {
  const location = useLocation();
  const showStats = location.pathname === '/';

  return (
    <header className="app-header">
      <div className="app-header__bar">
        <ProtectedHome user={user} onLogout={onLogout} />
        {showStats && <StatsBar refreshKey={statsRefreshKey} />}
      </div>
    </header>
  );
}
