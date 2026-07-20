import { useState } from 'react';
import type { FormEvent } from 'react';
import './LoginForm.css';

interface LoginFormProps {
  onLogin: (username: string, password: string) => Promise<void>;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onLogin(username, password);
    } catch {
      setError('Invalid username or password.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <label htmlFor="username">
        Username
        <input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
      </label>
      <label htmlFor="password">
        Password
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>
      {error && (
        <p className="login-form__error" role="alert">
          {error}
        </p>
      )}
      <button type="submit" disabled={submitting}>
        {submitting ? 'Signing in…' : 'Sign in'}
      </button>
    </form>
  );
}
