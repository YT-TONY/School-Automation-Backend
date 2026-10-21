import { PaymentRequired, USE_MOCK, backend, session, type Result, type Term } from './api';
import { setToken } from './services/http';
import { publicViews } from './public';

export interface View {
  title: string;
  accent?: 'starter' | 'enterprise';
  guard?: () => string | null;
  html: () => string;
  mount?: (root: HTMLElement, query: URLSearchParams) => void;
}

const esc = (v: unknown) => String(v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string));
const money = (n: number) => new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', maximumFractionDigits: 0 }).format(n);
const msg = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong. Please try again.');

const btn = 'inline-flex items-center justify-center rounded-md border-2 border-accent bg-accent px-5 py-3 font-semibold text-white transition hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50';
const btnOutline = 'inline-flex items-center justify-center rounded-md border-2 border-accent px-5 py-3 font-semibold text-accent transition hover:bg-white active:scale-95';
const input = 'mt-1 w-full rounded-md border border-line bg-white px-3 py-3 transition focus:border-accent';
const card = 'rounded-lg border border-line bg-white p-6 transition duration-200 hover:-translate-y-1 hover:shadow-lg animate-fade-up';
const delay = (i: number) => `style="animation-delay:${i * 80}ms"`;

const section = (title: string, lead: string, body: string) => `
<section class="py-14 md:py-20"><h1 class="animate-fade-up text-4xl font-bold md:text-5xl">${title}</h1>
<p class="animate-fade-up mt-4 max-w-prose text-lg text-muted" ${delay(1)}>${lead}</p><div class="mt-10">${body}</div></section>`;

const cards = (items: { t: string; d: string; tag?: string }[]) =>
  `<ul class="grid gap-6 md:grid-cols-3">${items.map((c, i) => `<li class="${card}" ${delay(i + 2)}>
    ${c.tag ? `<span class="rounded-full bg-paper px-3 py-1 text-xs font-semibold text-accent">${c.tag}</span>` : ''}
    <h3 class="mt-3 text-xl font-bold">${c.t}</h3><p class="mt-2 text-muted">${c.d}</p></li>`).join('')}</ul>`;

const notice = (title: string, text: string, href: string, label: string) =>
  `<div class="${card}" role="alert"><h2 class="text-2xl font-bold">${esc(title)}</h2><p class="mt-2 text-muted">${esc(text)}</p><a class="${btn} mt-6" href="#${href}">${esc(label)}</a></div>`;

const tier1Bar = () => `<div class="flex flex-wrap items-center justify-between gap-3 border-b border-line py-3 print:hidden">
  <p class="text-sm text-muted">Signed in as <strong class="text-ink">${esc(session.get()?.student.name ?? '')}</strong></p>
  <nav aria-label="Result portal" class="flex gap-2 text-sm font-semibold"><a class="rounded px-3 py-2 hover:bg-white" href="#/tier1/buy-pin">Buy result PIN</a>
  <a class="rounded px-3 py-2 hover:bg-white" href="#/tier1/result">My result</a><button class="rounded px-3 py-2 hover:bg-white" data-logout>Log out</button></nav></div>`;

const needLogin = () => (session.get() ? null : '/tier1/login');

const resultHtml = (r: Result) => `
<div class="animate-fade-up"><div class="flex flex-wrap items-end justify-between gap-4"><div>
<h1 class="text-3xl font-bold md:text-4xl">${esc(r.student.name)}</h1>
<p class="mt-1 text-muted">${esc(r.student.code)} &middot; ${esc(r.student.className)} &middot; ${esc(r.term)}</p></div>
<button class="${btnOutline} print:hidden" onclick="window.print()">Print result</button></div>
<div class="mt-6 overflow-x-auto" role="region" aria-label="Result table" tabindex="0"><table class="w-full min-w-[34rem] border-collapse text-left">
<caption class="sr-only">Subject scores for ${esc(r.term)}</caption>
<thead><tr class="border-b-2 border-ink">${['Subject', 'CA', 'Exam', 'Total', 'Grade', 'Remark'].map((h) => `<th scope="col" class="p-3">${h}</th>`).join('')}</tr></thead>
<tbody>${r.subjects.map((s) => `<tr class="border-b border-line"><th scope="row" class="p-3 font-semibold">${esc(s.subject)}</th><td class="p-3">${esc(s.ca)}</td><td class="p-3">${esc(s.exam)}</td><td class="p-3 font-semibold">${esc(s.total)}</td><td class="p-3 font-bold text-accent">${esc(s.grade)}</td><td class="p-3">${esc(s.remark)}</td></tr>`).join('')}</tbody></table></div>
<dl class="mt-6 grid gap-4 sm:grid-cols-2"><div class="${card}"><dt class="text-sm text-muted">Average</dt><dd class="text-3xl font-bold">${esc(r.average)}</dd></div>
<div class="${card}"><dt class="text-sm text-muted">Position</dt><dd class="text-3xl font-bold">${esc(r.position)} <span class="text-lg font-normal text-muted">of ${esc(r.outOf)}</span></dd></div></dl></div>`;

export const views: Record<string, View> = {
  ...publicViews,
  '/tier2': {
    title: 'Tier 2: Complete School OS', accent: 'enterprise',
    html: () => section('Tier 2: Complete School OS', 'Full school operations, billing and messaging.', `
<div class="${card} max-w-xl"><h2 class="text-2xl font-bold text-accent">Details coming soon</h2><p class="mt-2 text-muted">We will share what Tier 2 includes and how to get started later. Contact us if you want to be told first.</p><a class="${btn} mt-6" href="#/contact">Contact us</a></div>`),
  },
  '/tier1/login': {
    title: 'Result Portal login', accent: 'starter',
    html: () => `<section class="mx-auto max-w-md py-14"><div class="${card}"><h1 class="text-3xl font-bold">Result Portal</h1><p class="mt-2 text-muted">Log in to buy a result PIN and view your result.</p>
<form id="login" class="mt-6 space-y-5" novalidate>
<div><label for="c" class="font-semibold">Student ID</label><input id="c" name="code" autocomplete="username" required class="${input}"></div>
<div><label for="p" class="font-semibold">Password</label><input id="p" name="password" type="password" autocomplete="current-password" required class="${input}"></div>
<p id="err" role="alert" class="min-h-6 text-sm font-semibold text-red-700"></p><button class="${btn} w-full">Log in</button></form>
${USE_MOCK ? '<p class="mt-4 text-sm text-muted">Demo mode: STU001 / demo123</p>' : ''}</div></section>`,
    mount(root) {
      const form = root.querySelector<HTMLFormElement>('#login')!;
      const err = root.querySelector<HTMLElement>('#err')!;
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const d = new FormData(form);
        const code = String(d.get('code') ?? '').trim(), password = String(d.get('password') ?? '');
        if (!code || !password) { err.textContent = 'Enter your student ID and password.'; return; }
        const b = form.querySelector('button')!;
        b.disabled = true; err.textContent = '';
        try {
          const { token, student } = await backend.login(code, password);
          setToken(token); session.set({ token, student, paidTerms: [] });
          location.hash = '/tier1/buy-pin';
        } catch (ex) { err.textContent = msg(ex); b.disabled = false; }
      });
    },
  },
  '/tier1/buy-pin': {
    title: 'Buy result PIN', accent: 'starter', guard: needLogin,
    html: () => `${tier1Bar()}<section class="mx-auto max-w-lg py-12"><h1 class="animate-fade-up text-3xl font-bold">Buy a result PIN</h1>
<form id="pay" class="${card} mt-6 space-y-5"><div><label for="t" class="font-semibold">Term</label><select id="t" class="${input}" disabled><option>Loading terms...</option></select></div>
<p id="price" class="text-2xl font-bold" aria-live="polite"></p><button class="${btn} w-full" disabled>Pay now</button></form>
<div id="status" role="status" aria-live="polite" class="mt-6"></div></section>`,
    mount(root, query) {
      const sel = root.querySelector<HTMLSelectElement>('#t')!, price = root.querySelector<HTMLElement>('#price')!;
      const form = root.querySelector<HTMLFormElement>('#pay')!, pay = form.querySelector('button')!;
      const status = root.querySelector<HTMLElement>('#status')!;
      let terms: Term[] = [];
      const showPrice = () => { const t = terms.find((x) => x.id === sel.value); price.textContent = t ? money(t.price) : ''; };

      const confirm = async (reference: string) => {
        status.innerHTML = '<p class="animate-pulse font-semibold">Confirming your payment...</p>';
        try {
          const v = await backend.verify(reference);
          const s = session.get()!;
          if (v.status === 'confirmed' && s.pending?.reference === reference) {
            session.set({ ...s, paidTerms: [...new Set([...s.paidTerms, s.pending.termId])], pending: undefined });
            status.innerHTML = `<div class="${card}"><h2 class="text-2xl font-bold text-accent">Payment confirmed</h2>${v.pin ? `<p class="mt-3 text-muted">Your result PIN</p><p class="font-mono text-2xl font-bold tracking-widest">${esc(v.pin)}</p>` : ''}
              <a class="${btn} mt-6" href="#/tier1/result?term=${encodeURIComponent(s.pending.termId)}">View my result</a></div>`;
          } else if (v.status === 'pending') {
            status.innerHTML = `<div class="${card}"><p class="font-semibold">Your payment is still pending.</p><button id="again" class="${btnOutline} mt-4">Check again</button></div>`;
            status.querySelector('#again')!.addEventListener('click', () => confirm(reference));
          } else {
            status.innerHTML = notice('Payment not confirmed', 'We could not confirm this payment. You have not been charged for a PIN. Please try again.', '/tier1/buy-pin', 'Try again');
          }
        } catch (ex) { status.innerHTML = notice('Could not check payment', msg(ex), '/tier1/buy-pin', 'Back'); }
      };

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        pay.disabled = true; status.innerHTML = '<p class="animate-pulse font-semibold">Starting payment...</p>';
        try {
          const p = await backend.pay(sel.value);
          session.set({ ...session.get()!, pending: { reference: p.reference, termId: sel.value } });
          if (p.authorizationUrl) { location.assign(p.authorizationUrl); return; }
          await confirm(p.reference);
        } catch (ex) { status.textContent = msg(ex); pay.disabled = false; }
      });
      sel.addEventListener('change', showPrice);

      backend.terms().then((list) => {
        terms = list;
        sel.innerHTML = list.map((t) => `<option value="${esc(t.id)}">${esc(t.label)}</option>`).join('');
        sel.disabled = !list.length; pay.disabled = !list.length; showPrice();
      }).catch((ex) => { status.textContent = msg(ex); });

      const ref = query.get('reference') ?? query.get('trxref'); // returning from the payment gateway
      if (ref) { pay.disabled = true; confirm(ref); }
    },
  },
  '/tier1/result': {
    title: 'My result', accent: 'starter', guard: needLogin,
    html: () => `${tier1Bar()}<section class="py-10"><div id="out" aria-live="polite"><p class="animate-pulse font-semibold">Loading your result...</p></div></section>`,
    async mount(root, query) {
      const out = root.querySelector<HTMLElement>('#out')!;
      try {
        const termId = query.get('term') ?? session.get()?.paidTerms.at(-1) ?? (await backend.terms())[0]?.id;
        if (!termId) throw new Error('No terms are available yet.');
        out.innerHTML = resultHtml(await backend.result(termId));   // the server decides whether payment is confirmed
      } catch (ex) {
        out.innerHTML = ex instanceof PaymentRequired
          ? notice('Payment not confirmed', 'Buy a result PIN to view this result.', '/tier1/buy-pin', 'Buy result PIN')
          : notice('Could not load your result', msg(ex), '/tier1/buy-pin', 'Back');
      }
    },
  },
  '/404': { title: 'Page not found', html: () => section('Page not found', 'That page does not exist.', `<a class="${btn}" href="#/">Go home</a>`) },
};
