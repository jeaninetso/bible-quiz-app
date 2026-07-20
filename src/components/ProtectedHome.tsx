import type { CurrentUser } from '../types/auth';
import './ProtectedHome.css';

interface ProtectedHomeProps {
  user: CurrentUser;
  onLogout: () => void;
}

export function ProtectedHome({ user, onLogout }: ProtectedHomeProps) {
  return (
    <div className="protected-home">
      <p className="protected-home__greeting">
        Welcome back, <strong>{user.username}</strong>.
      </p>
      <button type="button" onClick={onLogout}>
        Sign out
      </button>
    </div>
  );
}
