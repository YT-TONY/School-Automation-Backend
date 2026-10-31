import { ApiError, api as http, setToken } from './services/http';
import type { Branding } from './theme';

// Types mirror the backend schemas (app/schemas/*.py). snake_case is converted to camelCase by services/http.ts.
export type ResultStatus = 'DRAFT' | 'SUBMITTED_BY_TEACHER' | 'COMPILED_BY_CLASS_TEACHER' | 'APPROVED_BY_VP' | 'PUBLISHED';
export type PaymentStatus = 'PENDING' | 'SUCCESS' | 'FAILED' | 'ABANDONED';
export interface Account { id: string; email: string; name: string; role: string }
export interface PayRequest { amount: number; quantity: number; payerEmail: string; studentId?: string }
export interface Payment { authorizationUrl: string; accessCode: string; reference: string; totalCharged: number; platformMarkup: number }
export interface Receipt { receiptNumber: string; payerName: string; payerEmail: string; amountPaid: number; itemsSummary: Record<string, unknown>; issuedAt: string }
export interface Verified { reference: string; status: PaymentStatus; amountTotal: number; paymentType: string; receipt?: Receipt | null }
export interface ScoreDetail {
  subjectName?: string | null; subjectCode?: string | null;
  test1Score: number; test2Score: number; assignmentScore: number; caScore: number; examScore: number; totalScore: number;
  grade?: string | null; status: ResultStatus;
}
export interface ResultSheet {
  studentName: string; admissionNumber: string; session: string; term: string;
  pinRemainingUses?: number | null; classPosition?: string | null; termAverage?: number | null;
  strongestSubject?: string | null; weakestSubject?: string | null; results: ScoreDetail[];
}
export interface SchoolConfig { branding: Branding; session: string; term: string; pinPrice: number; allowPinPurchase: boolean }
export interface CheckRequest { admissionNumber: string; pinCode: string; session: string; term: string }

interface Session { token: string; account: Account }
const KEY = 'schoolhub.session';
export const session = {
  get(): Session | null {
    try {
      const s = JSON.parse(sessionStorage.getItem(KEY) ?? 'null');
      if (s?.token && s?.account) return s;
      if (s) sessionStorage.removeItem(KEY);   // a login saved by an older version of the site: discard it
    } catch { /* fall through */ }
    return null;
  },
  set(s: Session | null) { if (s) sessionStorage.setItem(KEY, JSON.stringify(s)); else sessionStorage.removeItem(KEY); },
};
// The bought PIN is kept separately, because parents can buy a PIN without logging in
export const purchase = {
  get(): { pin?: string } | null { try { return JSON.parse(sessionStorage.getItem('schoolhub.purchase') ?? 'null'); } catch { return null; } },
  set(v: { pin?: string } | null) { if (v) sessionStorage.setItem('schoolhub.purchase', JSON.stringify(v)); else sessionStorage.removeItem('schoolhub.purchase'); },
};
const saved = session.get();
if (saved) setToken(saved.token);

interface Backend {
  config(): Promise<SchoolConfig>;                   // GET /schools/config
  login(email: string, password: string): Promise<{ token: string; account: Account }>;
  pay(r: PayRequest): Promise<Payment>;
  verify(reference: string): Promise<Verified>;
  checkResult(r: CheckRequest): Promise<ResultSheet>;
}

// ---- Real backend. Request/response shapes follow your schemas; the URL paths are assumptions to adjust. ----
const post = <T>(path: string, body: unknown) => http<T>(path, { method: 'POST', body: JSON.stringify(body) });
const real: Backend = {
  async config() {
    const c = await http<{ name: string; branding?: { primaryColor?: string }; settings?: { currentSession?: string; currentTerm?: string; pinPriceAmount?: number; allowParentPinPurchase?: boolean } }>('/schools/config');
    return {
      branding: { schoolName: c.name, primaryColor: c.branding?.primaryColor ?? '' },
      session: c.settings?.currentSession ?? '', term: c.settings?.currentTerm ?? '',
      pinPrice: c.settings?.pinPriceAmount ?? 1500,      // 1500 is the backend's own default
      allowPinPurchase: c.settings?.allowParentPinPurchase ?? true,
    };
  },
  async login(email, password) {   // POST /auth/login is an OAuth2 form: fields "username" (the email) and "password"
    const t = await http<{ accessToken: string; userId: string; email: string; role: string }>('/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ username: email, password }),
    });
    setToken(t.accessToken);   // needed so /auth/me is sent with the token
    const me = await http<{ fullName?: string }>('/auth/me').catch(() => ({}) as { fullName?: string });
    return { token: t.accessToken, account: { id: t.userId, email: t.email, name: me.fullName ?? t.email, role: t.role } };
  },
  pay: (r) => post('/payments/initialize', { paymentType: 'ONLINE_PIN', ...r }),   // PaymentInitializeRequest
  async verify(reference) {   // there is no verify route: the receipt exists only after the webhook has fulfilled the payment
    try {
      const r = await http<Receipt>(`/payments/receipts/${encodeURIComponent(reference)}`);
      return { reference, status: 'SUCCESS', amountTotal: r.amountPaid, paymentType: 'ONLINE_PIN', receipt: r };
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return { reference, status: 'PENDING', amountTotal: 0, paymentType: 'ONLINE_PIN' };
      throw e;
    }
  },
  checkResult: (r) => post('/results/verify-and-view', r),   // CheckResultRequest -> StudentResultSheet
};

// ---- Demo backend so the UI works with no server. Login STU001 / demo123, PIN DEMO-4821-7730 ----
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const grade = (t: number) => (t >= 70 ? 'A' : t >= 60 ? 'B' : t >= 50 ? 'C' : t >= 45 ? 'D' : t >= 40 ? 'E' : 'F');
const student = { admissionNumber: 'NNADI482019', fullName: 'Ada Nnadi' };
const mock: Backend = {
  config: async () => ({ branding: { schoolName: 'Greenfield Academy', primaryColor: '#0e7a5a' }, session: '2025/2026', term: 'First Term', pinPrice: 1000, allowPinPurchase: true }), // change the colour here to test
  async login(email, password) {
    await sleep(500);
    if (email.toLowerCase() !== 'parent@example.com' || password !== 'demo123') throw new Error('Incorrect email or password.');
    return { token: 'mock-token', account: { id: 'mock-user', email, name: 'Ada Nnadi', role: 'STUDENT' } };
  },
  async pay(r) { await sleep(400); return { authorizationUrl: '', accessCode: 'mock', reference: `MOCK-${Date.now()}`, totalCharged: r.amount + 500, platformMarkup: 500 }; },
  async verify(reference) {
    await sleep(1200);
    return { reference, status: 'SUCCESS', amountTotal: 1500, paymentType: 'ONLINE_PIN',
      receipt: { receiptNumber: 'RCT-000123', payerName: student.fullName, payerEmail: 'parent@example.com', amountPaid: 1500, itemsSummary: { item: 'Result PIN', quantity: 1, pins: ['DEMO-4821-7730'] }, issuedAt: new Date().toISOString() } };
  },
  async checkResult(r) {
    await sleep(600);
    if (r.admissionNumber.toUpperCase() !== student.admissionNumber || r.pinCode !== 'DEMO-4821-7730') throw new Error('Invalid admission number or PIN.');
    const raw: [string, number, number, number, number][] = [['Mathematics', 10, 11, 11, 44], ['English Language', 9, 9, 10, 41], ['Basic Science', 12, 11, 11, 47], ['Civic Education', 12, 12, 11, 52]];
    const results: ScoreDetail[] = raw.map(([subjectName, t1, t2, asg, exam]) => {
      const ca = t1 + t2 + asg, total = ca + exam;
      return { subjectName, test1Score: t1, test2Score: t2, assignmentScore: asg, caScore: ca, examScore: exam, totalScore: total, grade: grade(total), status: 'PUBLISHED' };
    });
    return { studentName: student.fullName, admissionNumber: student.admissionNumber, session: r.session, term: r.term, pinRemainingUses: 4,
      classPosition: '3rd', termAverage: Math.round((results.reduce((a, x) => a + x.totalScore, 0) / results.length) * 10) / 10, strongestSubject: 'Civic Education', weakestSubject: 'Social Studies', results };
  },
};

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
export const backend: Backend = USE_MOCK ? mock : real;

// One shared request for the school's public config (branding, current session/term, PIN price)
let cfg: Promise<SchoolConfig> | undefined;
export const getConfig = () => (cfg ??= backend.config().catch((e) => { cfg = undefined; throw e; }));
