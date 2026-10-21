import { ApiError, api as http, setToken } from './services/http';

export interface Student { code: string; name: string; className: string }
export interface Term { id: string; label: string; price: number }          // price in naira
export interface Payment { reference: string; authorizationUrl?: string }
export interface Verified { status: 'confirmed' | 'pending' | 'failed'; pin?: string }
export interface SubjectResult { subject: string; ca: number; exam: number; total: number; grade: string; remark: string }
export interface Result { student: Student; term: string; subjects: SubjectResult[]; average: number; position: number; outOf: number }

export class PaymentRequired extends Error {}

interface Session { token: string; student: Student; paidTerms: string[]; pending?: { reference: string; termId: string } }
const KEY = 'schoolhub.session';
export const session = {
  get(): Session | null { try { return JSON.parse(sessionStorage.getItem(KEY) ?? 'null'); } catch { return null; } },
  set(s: Session | null) { if (s) sessionStorage.setItem(KEY, JSON.stringify(s)); else sessionStorage.removeItem(KEY); },
};
const saved = session.get();
if (saved) setToken(saved.token);

interface Backend {
  login(code: string, password: string): Promise<{ token: string; student: Student }>;
  terms(): Promise<Term[]>;
  pay(termId: string): Promise<Payment>;
  verify(reference: string): Promise<Verified>;
  result(termId: string): Promise<Result>;
}

// ---- Real backend. The endpoint paths below are assumptions: change them to match your API. ----
const real: Backend = {
  login: (studentCode, password) => http('/auth/login', { method: 'POST', body: JSON.stringify({ studentCode, password }) }),
  terms: () => http('/terms'),
  pay: (termId) => http('/payments/initiate', { method: 'POST', body: JSON.stringify({ termId, callbackUrl: `${location.origin}/#/tier1/buy-pin` }) }),
  verify: (reference) => http(`/payments/verify/${encodeURIComponent(reference)}`),
  async result(termId) {
    try { return await http<Result>(`/results/${encodeURIComponent(termId)}`); }
    catch (e) { if (e instanceof ApiError && (e.status === 402 || e.status === 403)) throw new PaymentRequired(); throw e; }
  },
};

// ---- Demo backend so the UI works with no server. Login: STU001 / demo123 ----
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const grade = (t: number) => (t >= 70 ? 'A' : t >= 60 ? 'B' : t >= 50 ? 'C' : t >= 45 ? 'D' : t >= 40 ? 'E' : 'F');
const remarks: Record<string, string> = { A: 'Excellent', B: 'Very good', C: 'Good', D: 'Fair', E: 'Pass', F: 'Fail' };
const student: Student = { code: 'STU001', name: 'Ada Okafor', className: 'JSS 2A' };
const mock: Backend = {
  async login(code, password) {
    await sleep(500);
    if (code.toUpperCase() !== student.code || password !== 'demo123') throw new Error('Invalid student ID or password.');
    return { token: 'mock-token', student };
  },
  terms: async () => [{ id: '2026-1', label: '2026/2027 First Term', price: 1000 }],
  async pay() { await sleep(400); return { reference: `MOCK-${Date.now()}` }; },
  async verify() { await sleep(1200); return { status: 'confirmed', pin: 'DEMO-4821-7730' }; },
  async result(termId) {
    if (!session.get()?.paidTerms.includes(termId)) throw new PaymentRequired();
    const raw: [string, number, number][] = [['Mathematics', 32, 44], ['English Language', 28, 41], ['Basic Science', 34, 47], ['Social Studies', 30, 38], ['Civic Education', 35, 52], ['Computer Studies', 36, 55]];
    const subjects = raw.map(([subject, ca, exam]) => { const total = ca + exam; const g = grade(total); return { subject, ca, exam, total, grade: g, remark: remarks[g] }; });
    const average = Math.round((subjects.reduce((a, s) => a + s.total, 0) / subjects.length) * 10) / 10;
    return { student, term: '2026/2027 First Term', subjects, average, position: 3, outOf: 38 };
  },
};

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
export const backend: Backend = USE_MOCK ? mock : real;
