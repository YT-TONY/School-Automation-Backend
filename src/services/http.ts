const BASE = import.meta.env.VITE_API_URL as string;

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

let token: string | null = null;
export const setToken = (t: string | null) => { token = t; };

// The school is read from the subdomain, e.g. greenfield.yourapp.com -> "greenfield"
const tenant = location.hostname.split('.')[0];

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant': tenant,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.code ?? 'unknown', body.message ?? res.statusText);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
