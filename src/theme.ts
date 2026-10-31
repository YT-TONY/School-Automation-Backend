// Tier 1 branding comes from the backend (GET /branding). The last good copy is cached to avoid a colour flash.
export interface Branding { schoolName: string; primaryColor: string } // primaryColor: "#rrggbb"

const KEY = 'schoolhub.brand';
const HEX = /^#[0-9a-f]{6}$/i;

function valid(b: unknown): b is Branding {
  const x = b as Partial<Branding> | null;
  return !!x && typeof x.schoolName === 'string' && typeof x.primaryColor === 'string' && HEX.test(x.primaryColor);
}

const lum = (hex: string) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const toHex = (c: number[]) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

/** Darkens a colour until white text on it is readable (WCAG AA, 4.5:1), so any school colour stays usable. */
export function readable(hex: string): string {
  let c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  for (let n = 0; n < 30 && 1.05 / (lum(toHex(c)) + 0.05) < 4.5; n++) c = c.map((v) => v * 0.92);
  return toHex(c);
}

let current: Branding = { schoolName: '', primaryColor: '#0e7a5a' };
try { const s = JSON.parse(localStorage.getItem(KEY) ?? 'null'); if (valid(s)) current = s; } catch { /* use default */ }

export const getBrand = () => current;

export function applyBrand(b: unknown) {
  if (!valid(b)) return; // ignore bad data from the backend, never put it into CSS
  current = b;
  try { localStorage.setItem(KEY, JSON.stringify(b)); } catch { /* storage unavailable */ }
  document.documentElement.style.setProperty('--brand', readable(b.primaryColor));
  document.querySelectorAll<HTMLElement>('[data-school]').forEach((el) => { el.textContent = b.schoolName; });
}
