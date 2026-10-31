import { USE_MOCK, backend, getConfig, purchase, session, type ResultSheet } from './api';
import { setToken } from './services/http';
import { btn, btnOutline, card, esc, input, money, msg, notice } from './ui';
import { getBrand } from './theme';
import type { View } from './views';

const needLogin = () => (session.get() ? null : '/tier1/login');

const bar = () => {
  const s = session.get();
  return !s ? '' : `<div class="flex flex-wrap items-center justify-between gap-3 border-b border-line py-3 print:hidden">
  <p class="text-sm text-muted"><span data-school class="mr-2 font-semibold text-accent">${esc(getBrand().schoolName)}</span>Signed in as <strong class="text-ink">${esc(s.account.name)}</strong></p>
  <nav aria-label="Result portal" class="flex gap-2 text-sm font-semibold"><a class="rounded px-3 py-2 hover:bg-white" href="#/tier1/buy-pin">Buy result PIN</a>
  <a class="rounded px-3 py-2 hover:bg-white" href="#/tier1/result">Check result</a><button class="rounded px-3 py-2 hover:bg-white" data-logout>Log out</button></nav></div>`;
};

/** The receipt's items_summary format is not fixed, so look for any key containing "pin" holding a string or list of strings. */
const findPin = (o: Record<string, unknown>): string | undefined => {
  for (const [k, v] of Object.entries(o)) {
    const x = Array.isArray(v) ? v[0] : v;
    if (/pin/i.test(k) && typeof x === 'string') return x;
  }
};
const items = (o: Record<string, unknown>) => Object.entries(o).map(([k, v]) => `<li><span class="text-muted">${esc(k)}:</span> ${esc(typeof v === 'object' ? JSON.stringify(v) : v)}</li>`).join('');
const stat = (label: string, v: unknown) => (v == null || v === '' ? '' : `<div class="${card}"><dt class="text-sm text-muted">${label}</dt><dd class="text-2xl font-bold">${esc(v)}</dd></div>`);

const sheetHtml = (r: ResultSheet) => `<div class="animate-fade-up mt-8"><div class="flex flex-wrap items-end justify-between gap-4"><div>
<h2 class="text-3xl font-bold">${esc(r.studentName)}</h2><p class="mt-1 text-muted">${esc(r.admissionNumber)} &middot; ${esc(r.session)} &middot; ${esc(r.term)}</p></div>
<button class="${btnOutline} print:hidden" onclick="window.print()">Print result</button></div>
<div class="mt-6 overflow-x-auto" role="region" aria-label="Result table" tabindex="0"><table class="w-full min-w-[44rem] border-collapse text-left">
<caption class="sr-only">Subject scores for ${esc(r.session)} ${esc(r.term)}</caption>
<thead><tr class="border-b-2 border-ink">${['Subject', 'Test 1', 'Test 2', 'Assignment', 'CA', 'Exam', 'Total', 'Grade'].map((h) => `<th scope="col" class="p-3">${h}</th>`).join('')}</tr></thead>
<tbody>${r.results.filter((s) => s.status === 'PUBLISHED').map((s) => `<tr class="border-b border-line"><th scope="row" class="p-3 font-semibold">${esc(s.subjectName ?? s.subjectCode ?? '')}</th>${[s.test1Score, s.test2Score, s.assignmentScore, s.caScore, s.examScore].map((n) => `<td class="p-3">${esc(n)}</td>`).join('')}<td class="p-3 font-semibold">${esc(s.totalScore)}</td><td class="p-3 font-bold text-accent">${esc(s.grade ?? '-')}</td></tr>`).join('')}</tbody></table></div>
<dl class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">${stat('Class position', r.classPosition === 'Verified' ? null : r.classPosition)}${stat('Term average', r.termAverage)}${stat('Strongest subject', r.strongestSubject)}${stat('Weakest subject', r.weakestSubject)}${stat('PIN uses left', r.pinRemainingUses)}</dl></div>`;

export const tier1Views: Record<string, View> = {
  '/tier1/login': {
    title: 'Result Portal login', accent: 'starter',
    html: () => `<section class="mx-auto max-w-md py-14"><div class="${card}"><h1 class="text-3xl font-bold">Result Portal</h1><p data-school class="mt-1 font-semibold text-accent">${esc(getBrand().schoolName)}</p><p class="mt-2 text-muted">Log in to buy a result PIN.</p>
<form id="login" class="mt-6 space-y-5" novalidate>
<div><label for="c" class="font-semibold">Email</label><input id="c" name="code" type="email" autocomplete="username" required class="${input}"></div>
<div><label for="p" class="font-semibold">Password</label><input id="p" name="password" type="password" autocomplete="current-password" required class="${input}"></div>
<p id="err" role="alert" class="min-h-6 text-sm font-semibold text-red-700"></p><button class="${btn} w-full">Log in</button></form>
<p class="mt-4 text-sm text-muted">Parents do not need an account: <a class="font-semibold underline" href="#/tier1/buy-pin">buy a PIN</a>. Already have a PIN? <a class="font-semibold underline" href="#/tier1/result">Check your result</a> with your admission number (for example NNADI482019).</p>
${USE_MOCK ? '<p class="mt-2 text-sm text-muted">Demo mode: parent@example.com / demo123. The result page then uses admission number NNADI482019.</p>' : ''}</div></section>`,
    mount(root) {
      const form = root.querySelector<HTMLFormElement>('#login')!, err = root.querySelector<HTMLElement>('#err')!;
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const d = new FormData(form), code = String(d.get('code') ?? '').trim(), password = String(d.get('password') ?? '');
        if (!code || !password) { err.textContent = 'Enter your email and password.'; return; }
        const b = form.querySelector('button')!; b.disabled = true; err.textContent = '';
        try {
          const { token, account } = await backend.login(code, password);
          setToken(token); session.set({ token, account });
          location.hash = '/tier1/buy-pin';
        } catch (ex) { err.textContent = msg(ex); b.disabled = false; }
      });
    },
  },
  '/tier1/buy-pin': {
    title: 'Buy result PIN', accent: 'starter',
    html: () => `${bar()}<section class="mx-auto max-w-lg py-12"><h1 class="animate-fade-up text-3xl font-bold">Buy a result PIN</h1>
<form id="pay" class="${card} mt-6 space-y-5">
<div><label for="q" class="font-semibold">Number of PINs</label><input id="q" type="number" min="1" max="20" value="1" required class="${input}"></div>
<div><label for="pe" class="font-semibold">Your email (for the receipt)</label><input id="pe" type="email" autocomplete="email" required class="${input}"></div>
<p id="price" class="text-xl font-bold" aria-live="polite"></p><button class="${btn} w-full" disabled>Pay now</button></form>
<div id="status" role="status" aria-live="polite" class="mt-6"></div></section>`,
    mount(root, query) {
      const qty = root.querySelector<HTMLInputElement>('#q')!, email = root.querySelector<HTMLInputElement>('#pe')!;
      const priceEl = root.querySelector<HTMLElement>('#price')!, form = root.querySelector<HTMLFormElement>('#pay')!;
      const pay = form.querySelector('button')!, status = root.querySelector<HTMLElement>('#status')!;
      let price = 0;
      const count = () => Math.min(20, Math.max(1, Math.floor(Number(qty.value) || 1)));
      const show = () => { priceEl.textContent = price ? `${money(price * count())} plus a service fee added at checkout` : ''; };

      const confirm = async (reference: string, tries = 0) => {
        status.innerHTML = '<p class="animate-pulse font-semibold">Confirming your payment...</p>';
        try {
          const v = await backend.verify(reference);
          if (v.status === 'SUCCESS') {
            const r = v.receipt, pin = r ? findPin(r.itemsSummary) : undefined;
            purchase.set({ pin });
            status.innerHTML = `<div class="${card}"><h2 class="text-2xl font-bold text-accent">Payment confirmed</h2>
              ${r ? `<p class="mt-3 text-sm text-muted">Receipt ${esc(r.receiptNumber)} &middot; ${money(r.amountPaid)}</p><ul class="mt-3 space-y-1">${items(r.itemsSummary)}</ul>` : ''}
              <a class="${btn} mt-6" href="#/tier1/result">Check my result</a></div>`;
          } else if (v.status === 'PENDING') {
            if (tries < 8) { status.innerHTML = '<p class="animate-pulse font-semibold">Waiting for your payment to be confirmed...</p>'; setTimeout(() => confirm(reference, tries + 1), 3000); return; }
            status.innerHTML = `<div class="${card}"><p class="font-semibold">Your payment is still pending.</p><button id="again" class="${btnOutline} mt-4">Check again</button></div>`;
            status.querySelector('#again')!.addEventListener('click', () => confirm(reference));
          } else {
            status.innerHTML = notice('Payment not confirmed', `${v.status === 'ABANDONED' ? 'The payment was cancelled.' : 'We could not confirm this payment.'} No PIN was issued. Please try again.`, '/tier1/buy-pin', 'Try again');
          }
        } catch (ex) { status.innerHTML = notice('Could not check payment', msg(ex), '/tier1/buy-pin', 'Back'); }
      };

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        pay.disabled = true; status.innerHTML = '<p class="animate-pulse font-semibold">Starting payment...</p>';
        try {
          const n = count();
          const p = await backend.pay({ amount: price * n, quantity: n, payerEmail: email.value.trim() });
          if (p.authorizationUrl) { location.assign(p.authorizationUrl); return; }
          await confirm(p.reference);
        } catch (ex) { status.textContent = msg(ex); pay.disabled = false; }
      });
      qty.addEventListener('input', show);
      getConfig().then((c) => {
        if (!c.allowPinPurchase) { status.innerHTML = notice('PIN purchase unavailable', 'Online PIN purchasing is currently disabled by this school.', '/tier1/result', 'Check a result'); return; }
        price = c.pinPrice; show();
        if (!query.get('reference') && !query.get('trxref')) pay.disabled = false;
      }).catch((ex) => { status.textContent = msg(ex); });
      const ref = query.get('reference') ?? query.get('trxref'); // returning from the payment gateway
      if (ref) { pay.disabled = true; confirm(ref); }
    },
  },
  '/tier1/result': {
    title: 'Check result', accent: 'starter',
    html: () => `${bar()}<section class="mx-auto max-w-2xl py-12"><h1 class="animate-fade-up text-3xl font-bold">Check your result</h1>
<form id="chk" class="${card} mt-6 grid gap-5 sm:grid-cols-2" novalidate>
<div class="sm:col-span-2"><label for="a" class="font-semibold">Admission number</label><input id="a" name="admissionNumber" required autocomplete="off" autocapitalize="characters" placeholder="e.g. NNADI482019" aria-describedby="ahint" class="${input} uppercase placeholder:normal-case"><p id="ahint" class="mt-1 text-sm text-muted">Usually your surname followed by 6 digits, for example NNADI482019. Ask your school if you do not have it.</p></div>
<div><label for="n" class="font-semibold">Result PIN</label><input id="n" name="pinCode" autocomplete="off" required class="${input} font-mono"></div>
<div><label for="s" class="font-semibold">Session</label><input id="s" name="session" placeholder="2025/2026" required class="${input}"></div>
<div><label for="t" class="font-semibold">Term</label><input id="t" name="term" placeholder="First Term" required class="${input}"></div>
<p id="rerr" role="alert" class="min-h-6 text-sm font-semibold text-red-700 sm:col-span-2"></p>
<button class="${btn} sm:col-span-2">View result</button></form>
<p class="mt-4 text-sm text-muted">No PIN yet? <a class="font-semibold underline" href="#/tier1/buy-pin">Buy a result PIN</a>.</p>
<div id="out" aria-live="polite"></div></section>`,
    mount(root) {
      const form = root.querySelector<HTMLFormElement>('#chk')!, err = root.querySelector<HTMLElement>('#rerr')!, out = root.querySelector<HTMLElement>('#out')!;
      form.querySelector<HTMLInputElement>('#n')!.value = purchase.get()?.pin ?? '';
      getConfig().then((c) => { // fill in the school's current session and term
        const se = form.querySelector<HTMLInputElement>('#s')!, te = form.querySelector<HTMLInputElement>('#t')!;
        if (!se.value) se.value = c.session;
        if (!te.value) te.value = c.term;
      }).catch(() => {});
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const d = new FormData(form), v = (k: string) => String(d.get(k) ?? '').trim();
        const req = { admissionNumber: v('admissionNumber').toUpperCase(),  // stored in capitals, and the server compares exactly
           pinCode: v('pinCode'), session: v('session'), term: v('term') };
        if (Object.values(req).some((x) => !x)) { err.textContent = 'Fill in all four fields.'; return; }
        const b = form.querySelector('button')!; b.disabled = true; err.textContent = ''; out.innerHTML = '<p class="mt-8 animate-pulse font-semibold">Loading your result...</p>';
        try { out.innerHTML = sheetHtml(await backend.checkResult(req)); }   // the server checks the PIN and published status
        catch (ex) { out.innerHTML = ''; err.textContent = msg(ex); }
        b.disabled = false;
      });
    },
  },
};
