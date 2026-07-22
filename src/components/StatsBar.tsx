import { useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import { validateMeStats } from '../data/validateQuiz';
import type { MeStats } from '../types/quiz';
import { badgeEmoji } from '../lib/badgeEmoji';
import './StatsBar.css';

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'loaded'; stats: MeStats };

interface StatsBarProps {
  // Bump this (e.g. after a quiz submission) to trigger a refetch.
  refreshKey: number;
}

export function StatsBar({ refreshKey }: StatsBarProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });

  useEffect(() => {
    fetchJson('/me/stats')
      .then((data) => setState({ status: 'loaded', stats: validateMeStats(data) }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Failed to load stats' });
      });
  }, [refreshKey]);

  if (state.status === 'loading') {
    return null;
  }
  if (state.status === 'error') {
    return (
      <p role="alert" className="stats-bar__error">
        Couldn't load your stats: {state.message}
      </p>
    );
  }

  const { stats } = state;

  return (
    <div className="stats-bar">
      <div className="stats-bar__metric">
        <span className="stats-bar__value">{stats.totalXp}</span>
        <span className="stats-bar__label">XP</span>
      </div>
      <div className="stats-bar__metric">
        <span className="stats-bar__value">{stats.level}</span>
        <span className="stats-bar__label">Level</span>
      </div>
      <div className="stats-bar__metric">
        <span className="stats-bar__value">{stats.currentStreak}</span>
        <span className="stats-bar__label">Day streak</span>
      </div>
      <div className="stats-bar__metric">
        <span className="stats-bar__value">{stats.quizzesCompleted}</span>
        <span className="stats-bar__label">Quizzes</span>
      </div>
      {stats.badges.length > 0 && (
        <div className="stats-bar__badges">
          {stats.badges.map((b) => (
            <span key={b.code} className="stats-bar__badge" title={b.description}>
              <span aria-hidden="true">{badgeEmoji(b.code)}</span>
              {b.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
