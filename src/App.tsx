import { useState } from 'react';
import { BookLibrary } from './components/BookLibrary';
import { LoginForm } from './components/LoginForm';
import { ProtectedHome } from './components/ProtectedHome';
import { QuizHistory } from './components/QuizHistory';
import { StatsBar } from './components/StatsBar';
import { useAuth } from './lib/useAuth';
import './App.css';

type Tab = 'library' | 'history';

function App() {
  const auth = useAuth();
  const [statsRefreshKey, setStatsRefreshKey] = useState(0);
  const [activeTab, setActiveTab] = useState<Tab>('library');

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

          <div className="app__tabs" role="tablist">
            <button
              type="button"
              role="tab"
              id="tab-library"
              aria-selected={activeTab === 'library'}
              aria-controls="tabpanel-library"
              className={'app__tab' + (activeTab === 'library' ? ' app__tab--active' : '')}
              onClick={() => setActiveTab('library')}
            >
              Books
            </button>
            <button
              type="button"
              role="tab"
              id="tab-history"
              aria-selected={activeTab === 'history'}
              aria-controls="tabpanel-history"
              className={'app__tab' + (activeTab === 'history' ? ' app__tab--active' : '')}
              onClick={() => setActiveTab('history')}
            >
              History
            </button>
          </div>

          {activeTab === 'library' && (
            <div id="tabpanel-library" role="tabpanel" aria-labelledby="tab-library">
              <BookLibrary onQuizSubmitted={() => setStatsRefreshKey((k) => k + 1)} />
            </div>
          )}
          {activeTab === 'history' && (
            <div id="tabpanel-history" role="tabpanel" aria-labelledby="tab-history">
              <QuizHistory />
            </div>
          )}
        </>
      )}
    </main>
  );
}

export default App;
