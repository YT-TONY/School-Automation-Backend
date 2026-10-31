import { publicViews } from './public';
import { tier1Views } from './tier1';

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

export const views: Record<string, View> = {
  ...publicViews,
  '/tier2': {
    title: 'Tier 2: Complete School OS', accent: 'enterprise',
    html: () => section('Tier 2: Complete School OS', 'Full school operations, billing and messaging.', `
<div class="${card} max-w-xl"><h2 class="text-2xl font-bold text-accent">Details coming soon</h2><p class="mt-2 text-muted">We will share what Tier 2 includes and how to get started later. Contact us if you want to be told first.</p><a class="${btn} mt-6" href="#/contact">Contact us</a></div>`),
  },
  ...tier1Views,
  '/404': { title: 'Page not found', html: () => section('Page not found', 'That page does not exist.', `<a class="${btn}" href="#/">Go home</a>`) },
};
