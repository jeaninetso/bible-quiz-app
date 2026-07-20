export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body?.detail === 'string' ? body.detail : `API returned ${res.status}`;
  } catch {
    return `API returned ${res.status}`;
  }
}

export async function fetchJson(path: string): Promise<unknown> {
  const res = await fetch(`${API_URL}${path}`, { credentials: 'include' });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res));
  }
  return res.json();
}

export async function postJson(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res));
  }
  return res.json();
}
