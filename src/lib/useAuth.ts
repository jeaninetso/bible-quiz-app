import { useCallback, useEffect, useState } from 'react';
import { fetchJson, postJson } from './api';
import { validateCurrentUser } from '../data/validateAuth';
import type { CurrentUser } from '../types/auth';

type AuthState =
  | { status: 'loading' }
  | { status: 'anonymous' }
  | { status: 'authenticated'; user: CurrentUser };

export function useAuth() {
  const [state, setState] = useState<AuthState>({ status: 'loading' });

  useEffect(() => {
    fetchJson('/auth/me')
      .then((data) => setState({ status: 'authenticated', user: validateCurrentUser(data) }))
      .catch(() => setState({ status: 'anonymous' }));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await postJson('/auth/login', { username, password });
    setState({ status: 'authenticated', user: validateCurrentUser(data) });
  }, []);

  const logout = useCallback(async () => {
    await postJson('/auth/logout', {});
    setState({ status: 'anonymous' });
  }, []);

  return { ...state, login, logout };
}
