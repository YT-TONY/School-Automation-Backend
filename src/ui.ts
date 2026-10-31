export const esc = (v: unknown) => String(v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string));
export const money = (n: number) => new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', maximumFractionDigits: 0 }).format(n);
export const msg = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong. Please try again.');
export const btn = 'inline-flex items-center justify-center rounded-md border-2 border-accent bg-accent px-5 py-3 font-semibold text-white transition hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50';
export const btnOutline = 'inline-flex items-center justify-center rounded-md border-2 border-accent px-5 py-3 font-semibold text-accent transition hover:bg-white active:scale-95';
export const input = 'mt-1 w-full rounded-md border border-line bg-white px-3 py-3 transition focus:border-accent';
export const card = 'rounded-lg border border-line bg-white p-6 transition duration-200 hover:-translate-y-1 hover:shadow-lg animate-fade-up';
export const notice = (title: string, text: string, href: string, label: string) =>
  `<div class="${card}" role="alert"><h2 class="text-2xl font-bold">${esc(title)}</h2><p class="mt-2 text-muted">${esc(text)}</p><a class="${btn} mt-6" href="#${href}">${esc(label)}</a></div>`;
