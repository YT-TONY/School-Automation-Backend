// Edit this file to customise the site name, navigation and the navbar dropdown button.
export const site = { name: 'Schoolhub', email: 'hello@example.com', phone: '+234 000 000 0000' };

export const navLinks = [
  { label: 'Home', path: '/' },
  { label: 'About us', path: '/about' },
  { label: 'Services', path: '/services' },
  { label: 'Contact us', path: '/contact' },
];

/** The customisable navbar button. Change the label or add/remove items freely. */
export const navButton = {
  label: 'Portals',
  items: [
    { label: 'Tier 1: Result Portal', note: 'Log in, buy a result PIN and view results', path: '/tier1/login' },
    { label: 'Tier 2: Complete School OS', note: 'Details coming soon', path: '/tier2' },
  ],
};
