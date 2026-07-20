import { useEffect, useState } from 'react';
import { fetchJson } from './lib/api';
import './App.css';

type HealthState = 'pending' | 'ok' | 'error';

function App() {
  const [health, setHealth] = useState<HealthState>('pending');

  useEffect(() => {
    let cancelled = false;
    fetchJson('/health')
      .then(() => {
        if (!cancelled) setHealth('ok');
      })
      .catch(() => {
        if (!cancelled) setHealth('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const statusText = {
    pending: 'Checking backend…',
    ok: 'Backend connected',
    error: "Backend unreachable — run `uvicorn app.main:app --reload` in backend/",
  }[health];

  return (
    <main className="app">
      <div className="app__eyebrow">Scripture Quest</div>
      <h1 className="app__title">Grow your Bible knowledge, one book at a time.</h1>
      <p className="app__subtitle">
        Pick a book, take a fresh quiz, learn something new — and watch your streak grow.
      </p>
      <div className="app__status" role="status">
        <span className={`app__status-dot app__status-dot--${health}`} />
        {statusText}
      </div>
    </main>
  );
}

export default App;
