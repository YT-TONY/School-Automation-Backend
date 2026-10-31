import type { View } from './views';
import { navLinks, site } from './config';

const btn = 'inline-flex items-center justify-center rounded-md border-2 border-accent bg-accent px-5 py-3 font-semibold text-white transition hover:opacity-90 active:scale-95';
const btnLight = 'inline-flex items-center justify-center rounded-md bg-white px-5 py-3 font-semibold text-deep transition hover:opacity-90 active:scale-95';
const input = 'mt-1 w-full rounded-md border border-line bg-white px-3 py-3 transition focus:border-starter';

/** Scroll-reveal hook: main.ts adds "is-in" when the element enters the viewport. */
const rv = (i = 0, dir = '') => `data-reveal="${dir}" style="--d:${i * 90}ms"`;

const tile = (cls: string, title: string, text: string, href: string, i: number) => `
<a href="#${href}" ${rv(i, 'left')} class="block rounded-lg p-6 text-white transition duration-300 hover:-translate-y-1 hover:shadow-xl ${cls}">
  <span class="block font-display text-2xl font-bold leading-snug">${title}</span>
  <span class="mt-2 block text-sm">${text}</span>
  <span class="mt-4 inline-block text-sm font-semibold underline underline-offset-4">Go<span class="sr-only"> to ${title}</span></span>
</a>`;

const sidebar = () => `
<aside class="space-y-5 lg:sticky lg:top-24 lg:self-start">
  ${tile('bg-deep', 'Open the Result Portal', 'Log in, buy a result PIN and view results.', '/tier1/login', 0)}
  ${tile('bg-starter', 'Talk to us about your school', 'Tell us what you need and we will reply.', '/contact', 1)}
  <nav aria-label="Quick links" ${rv(2, 'left')} class="rounded-lg border border-line bg-white p-6">
    <h2 class="font-display text-lg font-bold">Quick links</h2>
    <ul class="mt-3 space-y-2 text-sm">${[...navLinks, { label: 'Result Portal', path: '/tier1/login' }].map((l) => `<li><a class="underline-offset-4 hover:underline" href="#${l.path}">${l.label}</a></li>`).join('')}</ul>
  </nav>
</aside>`;

/** Banner + sidebar + white content card, the shared layout of every public page. */
const frame = (title: string, lead: string, body: string, actions = '') => `
<section class="relative left-1/2 w-screen -translate-x-1/2 bg-deep text-white" style="background-image:repeating-linear-gradient(135deg,rgba(255,255,255,.04) 0 2px,transparent 2px 14px)">
  <div class="mx-auto max-w-6xl px-5 pb-24 pt-14 md:pb-28 md:pt-20">
    <h1 class="animate-fade-up max-w-3xl font-display text-4xl font-bold leading-tight md:text-6xl">${title}</h1>
    <p class="animate-fade-up mt-4 max-w-prose text-lg" style="animation-delay:100ms">${lead}</p>
    ${actions ? `<div class="animate-fade-up mt-8 flex flex-wrap gap-3" style="animation-delay:200ms">${actions}</div>` : ''}
  </div>
</section>
<div class="relative -mt-14 grid gap-8 lg:grid-cols-[17rem_1fr]">
  ${sidebar()}
  <article class="order-first rounded-lg border border-line bg-white p-6 shadow-sm md:p-10 lg:order-none">${body}</article>
</div>`;

const block = (i: number, h: string, p: string, items: string[] = []) => `
<section ${rv(i)} class="mb-10 last:mb-0"><h2 class="border-b border-line pb-2 font-display text-2xl font-bold">${h}</h2>
  <p class="mt-3 max-w-prose text-muted">${p}</p>
  ${items.length ? `<ul class="mt-3 list-disc space-y-1 pl-5 text-muted">${items.map((x) => `<li>${x}</li>`).join('')}</ul>` : ''}
</section>`;

const row = (i: number, tag: string, t: string, d: string) => `
<li ${rv(i)} class="rounded-md border border-line p-4 transition hover:border-starter hover:shadow-md">
  <p class="text-xs font-semibold text-starter">${tag}</p><h3 class="mt-1 font-display text-lg font-bold">${t}</h3><p class="mt-1 text-sm text-muted">${d}</p>
</li>`;

export const publicViews: Record<string, View> = {
  '/': {
    title: 'Home',
    html: () => frame('School results and operations, made simple',
      `${site.name} helps schools compile accurate results, sell result PINs and, as you grow, run the whole school from one system.`, `
${block(0, 'Automated results', 'Scores, grading scales and approvals are handled in one workflow, so results are consistent every term.', ['Grading scales set by your school', 'Teacher, class teacher and principal approval', 'Report cards with averages and positions'])}
${block(1, 'Protected access', 'Parents and students see a result only after logging in and paying for a valid result PIN.', ['Payment is confirmed before a result is shown', 'Each PIN belongs to one student'])}
${block(2, 'Room to grow', 'Start with results. Add fees, transport and parent messaging with Tier 2 when you are ready.')}
<section ${rv()} class="mt-10"><h2 class="border-b border-line pb-2 font-display text-2xl font-bold">Checking a result takes four steps</h2>
<ol class="mt-5 grid gap-4 sm:grid-cols-2">${['Log in', 'Buy a result PIN', 'Payment is confirmed', 'View your result'].map((s, i) => row(i, `Step ${i + 1}`, s, '')).join('')}</ol></section>`,
      `<a class="${btnLight}" href="#/tier1/login">Open the Result Portal</a><a class="inline-flex items-center rounded-md border-2 border-white px-5 py-3 font-semibold transition hover:bg-white/10 active:scale-95" href="#/services">Explore services</a>`),
  },
  '/about': {
    title: 'About us',
    html: () => frame('About us', `${site.name} builds software that helps schools process results accurately with less paperwork.`, `
${block(0, 'Who we are', 'We started with the part schools feel most each term: turning teachers\' scores into published, trustworthy results. The same platform now extends to student records, fees, transport and parent messaging.')}
${block(1, 'What we believe', 'Good school software should be dependable for staff and easy for parents.', ['Accuracy: grading rules are applied the same way every time', 'Accessibility: pages work on phones, with a keyboard and with screen readers', 'Security: results go only to verified users who have paid for access'])}
${block(2, 'Where we are going', 'Tier 2, the Complete School OS, will bring full school management, fee paywalls, transport and WhatsApp messaging. Details will be shared soon.')}`),
  },
  '/services': {
    title: 'Services',
    html: () => frame('Services', 'Choose the tier that fits your school today.', `
<ul class="space-y-4">${[
  ['Tier 1', 'Result processing', 'Dynamic grading, multi-stage approval and publishing by the principal.'],
  ['Tier 1', 'Result PIN sales', 'Generate, batch, price and sell result PINs to parents.'],
  ['Tier 1', 'Report cards', 'Automatic PDF report cards with averages, rankings and teacher comments.'],
  ['Tier 2', 'School management', 'Admissions, student and staff records, classes and subjects.'],
  ['Tier 2', 'Fees and paywall', 'Fee structures, installments, receipts and tuition paywalls.'],
  ['Tier 2', 'Transport and WhatsApp', 'Bus routes, plus a WhatsApp assistant and broadcasts for parents.'],
].map(([tag, t, d], i) => row(i, tag, t, d)).join('')}</ul>`),
  },
  '/contact': {
    title: 'Contact us',
    html: () => frame('Contact us', 'Tell us about your school and we will get back to you.', `
${block(0, 'Get in touch', '', [`Email: <a class="font-semibold text-ink underline" href="mailto:${site.email}">${site.email}</a>`, `Phone: <span class="font-semibold text-ink">${site.phone}</span>`])}
<form id="contact" ${rv(1)} class="space-y-5" novalidate><h2 class="border-b border-line pb-2 font-display text-2xl font-bold">Send a message</h2>
<div><label for="n" class="font-semibold">Your name</label><input id="n" name="name" required autocomplete="name" class="${input}"></div>
<div><label for="e" class="font-semibold">Email</label><input id="e" name="email" type="email" required autocomplete="email" class="${input}"></div>
<div><label for="m" class="font-semibold">Message</label><textarea id="m" name="message" rows="5" required class="${input}"></textarea></div>
<p id="cerr" role="alert" class="min-h-6 text-sm font-semibold text-red-700"></p><button class="${btn}">Send message</button></form>`),
    mount(root) {
      const form = root.querySelector<HTMLFormElement>('#contact')!;
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const d = new FormData(form);
        const [name, email, message] = ['name', 'email', 'message'].map((k) => String(d.get(k) ?? '').trim());
        const err = root.querySelector<HTMLElement>('#cerr')!;
        if (!name || !message || !/^\S+@\S+\.\S+$/.test(email)) { err.textContent = 'Please enter your name, a valid email and a message.'; return; }
        err.textContent = '';
        // No contact endpoint is assumed, so this opens the visitor's email app.
        location.href = `mailto:${site.email}?subject=${encodeURIComponent(`Enquiry from ${name}`)}&body=${encodeURIComponent(`${message}\n\n${name} (${email})`)}`;
      });
    },
  },
};
