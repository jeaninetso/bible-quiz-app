import { useState } from 'react';
import { BookLibrary } from './components/BookLibrary';
import { LoginForm } from './components/LoginForm';
import { ProtectedHome } from './components/ProtectedHome';
import { StatsBar } from './components/StatsBar';
import { useAuth } from './lib/useAuth';
import './App.css';

function App() {
  const auth = useAuth();
  const [statsRefreshKey, setStatsRefreshKey] = useState(0);

  return (
    <main className="app">
      <div className="app__eyebrow">Scripture Quest</div>
      <h1 className="app__title">Grow your Bible knowledge, one book at a time.</h1>
      <p className="app__subtitle">
        Pick a book, take a fresh quiz, learn something new — and watch your streak grow.
      </p>

      {auth.status === 'loading' && <p role="status">Loading…</p>}
      {auth.status === 'anonymous' && <LoginForm onLogin={auth.login} />}
      {auth.status === 'authenticated' && (
        <>
          <ProtectedHome user={auth.user} onLogout={auth.logout} />
          <StatsBar refreshKey={statsRefreshKey} />
          <BookLibrary onQuizSubmitted={() => setStatsRefreshKey((k) => k + 1)} />
        </>
      )}
    </main>
  );
}

export default App;
