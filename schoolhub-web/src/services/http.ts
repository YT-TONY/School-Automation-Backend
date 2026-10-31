const BASE = import.meta.env.VITE_API_URL as string;

// Backends often send snake_case (e.g. test1_score); the frontend uses camelCase (test1Score)
const camel = (v: unknown): unknown =>
  Array.isArray(v) ? v.map(camel)
  : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k.replace(/_([a-z0-9])/g, (_m, c: string) => c.toUpperCase()), camel(x)]))
  : v;

// Requests: the frontend uses camelCase, FastAPI-style schemas expect snake_case. Set to false if your API takes camelCase.
const SNAKE_REQUESTS = true;
const snake = (v: unknown): unknown =>
  Array.isArray(v) ? v.map(snake)
  : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`), snake(x)]))
  : v;

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

let token: string | null = null;
export const setToken = (t: string | null) => { token = t; };

// The school is read from the subdomain, e.g. greenfield.yourapp.com -> "greenfield"
const tenant = (import.meta.env.VITE_TENANT_ID as string | undefined) || location.hostname.split('.')[0];

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    body: SNAKE_REQUESTS && typeof init.body === 'string' ? JSON.stringify(snake(JSON.parse(init.body))) : init.body,
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': tenant,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : undefined;
    throw new ApiError(res.status, body.code ?? 'unknown', body.message ?? detail ?? res.statusText);
  }
  return res.status === 204 ? (undefined as T) : (camel(await res.json()) as T);
}
