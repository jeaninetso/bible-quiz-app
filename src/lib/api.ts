export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function fetchJson(path: string): Promise<unknown> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API returned ${res.status} for ${path}`);
  }
  return res.json();
}
