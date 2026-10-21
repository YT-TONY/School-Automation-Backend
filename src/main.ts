import '@fontsource-variable/bricolage-grotesque';
import '@fontsource-variable/public-sans';
import './styles.css';
import { navButton, navLinks, site } from './config';
import { session } from './api';
import { setToken } from './services/http';
import { views } from './views';

const app = document.getElementById('app')!;
const link = 'rounded px-3 py-2 transition hover:bg-white aria-[current=page]:font-bold aria-[current=page]:underline underline-offset-8';

app.innerHTML = `
<a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-white focus:px-4 focus:py-2">Skip to content</a>
<div class="border-b border-line bg-white text-sm print:hidden"><div class="mx-auto flex max-w-6xl flex-wrap justify-end gap-x-6 gap-y-1 px-5 py-2 text-muted"><a class="hover:underline" href="mailto:${site.email}">${site.email}</a><span>${site.phone}</span></div></div>
<header class="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur print:hidden"><div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-3">
  <a href="#/" class="font-display text-xl font-bold">${site.name}</a>
  <nav aria-label="Main" class="flex flex-wrap items-center gap-1">
    ${navLinks.map((n) => `<a href="#${n.path}" data-path="${n.path}" class="${link}">${n.label}</a>`).join('')}
    <div class="relative ml-2">
      <button id="menu-btn" aria-haspopup="menu" aria-expanded="false" aria-controls="menu" class="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 font-semibold text-white transition hover:opacity-90 active:scale-95">${navButton.label}<svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" stroke-width="2"/></svg></button>
      <ul id="menu" role="menu" hidden class="absolute right-0 mt-2 w-72 animate-pop rounded-lg border border-line bg-white p-2 shadow-xl">
        ${navButton.items.map((i) => `<li role="none"><a role="menuitem" href="#${i.path}" class="block rounded-md px-3 py-3 transition hover:bg-paper"><span class="block font-semibold">${i.label}</span><span class="block text-sm text-muted">${i.note}</span></a></li>`).join('')}
      </ul>
    </div>
  </nav></div></header>
<main id="main" tabindex="-1" class="mx-auto max-w-6xl px-5"></main>
<footer class="mt-24 print:hidden">
  <section class="bg-starter text-white"><div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-10">
    <h2 data-reveal class="font-display text-2xl font-bold">Ready to simplify your school's results?</h2>
    <a data-reveal style="--d:120ms" href="#/contact" class="rounded-md bg-white px-5 py-3 font-semibold text-deep transition hover:opacity-90 active:scale-95">Contact us</a></div></section>
  <div class="bg-deep text-white/80"><div class="mx-auto grid max-w-6xl gap-8 px-5 py-12 text-sm md:grid-cols-4">
    <div data-reveal><p class="font-display text-xl font-bold text-white">${site.name}</p><p class="mt-2">Software for school results and operations.</p></div>
    <nav data-reveal style="--d:90ms" aria-label="Footer"><p class="font-semibold text-white">Quick links</p><ul class="mt-2 space-y-1">${navLinks.map((n) => `<li><a class="hover:underline" href="#${n.path}">${n.label}</a></li>`).join('')}</ul></nav>
    <div data-reveal style="--d:180ms"><p class="font-semibold text-white">Portals</p><ul class="mt-2 space-y-1">${navButton.items.map((i) => `<li><a class="hover:underline" href="#${i.path}">${i.label}</a></li>`).join('')}</ul></div>
    <div data-reveal style="--d:270ms"><p class="font-semibold text-white">Contact</p><p class="mt-2">${site.email}<br>${site.phone}</p></div></div>
    <p class="border-t border-white/15 py-4 text-center text-xs">&copy; ${new Date().getFullYear()} ${site.name}</p></div>
</footer>`;


// Scroll animation: reveal elements marked data-reveal as they enter the viewport
const io = 'IntersectionObserver' in window
  ? new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io!.unobserve(e.target); } }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' })
  : null;
const reveal = () => document.querySelectorAll('[data-reveal]:not(.is-in)').forEach((el) => (io ? io.observe(el) : el.classList.add('is-in')));

const main = document.getElementById('main')!;
const btn = document.getElementById('menu-btn') as HTMLButtonElement;
const menu = document.getElementById('menu')!;
const items = () => [...menu.querySelectorAll<HTMLElement>('[role=menuitem]')];

const setMenu = (open: boolean, focus = false) => {
  menu.hidden = !open;
  btn.setAttribute('aria-expanded', String(open));
  if (open) items()[0]?.focus(); else if (focus) btn.focus();
};
btn.addEventListener('click', () => setMenu(Boolean(menu.hidden)));
btn.addEventListener('keydown', (e) => { if (e.key === 'ArrowDown') { e.preventDefault(); setMenu(true); } });
menu.addEventListener('keydown', (e) => {
  const list = items(), i = list.indexOf(document.activeElement as HTMLElement);
  if (e.key === 'Escape') setMenu(false, true);
  else if (e.key === 'ArrowDown') { e.preventDefault(); list[(i + 1) % list.length].focus(); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
  else if (e.key === 'Tab') setMenu(false);
});
document.addEventListener('click', (e) => { if (!menu.hidden && !(e.target as Element).closest('#menu, #menu-btn')) setMenu(false); });

// Log out buttons inside the Tier 1 pages
main.addEventListener('click', (e) => {
  if ((e.target as Element).closest('[data-logout]')) { session.set(null); setToken(null); location.hash = '/tier1/login'; }
});

function render() {
  const [path, q = ''] = (location.hash.slice(1) || '/').split('?');
  const view = views[path] ?? views['/404'];
  const redirect = view.guard?.();
  if (redirect) { location.hash = redirect; return; }
  document.title = `${view.title} | ${site.name}`;
  document.body.dataset.page = view.accent ?? 'home';
  main.innerHTML = view.html();
  view.mount?.(main, new URLSearchParams(q));
  reveal();
  setMenu(false);
  document.querySelectorAll<HTMLAnchorElement>('[data-path]').forEach((a) => {
    if (a.dataset.path === path) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  window.scrollTo(0, 0);
  main.focus();
}
window.addEventListener('hashchange', render);
render();
reveal();
