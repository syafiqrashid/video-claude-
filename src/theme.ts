import {continueRender, delayRender, staticFile} from 'remotion';

export const FONT = 'Montserrat, sans-serif';

// Load bundled Montserrat (public/fonts) so renders don't depend on network access
if (typeof document !== 'undefined') {
  const handle = delayRender('Loading Montserrat');
  Promise.all(
    [600, 800, 900].map((w) => {
      const face = new FontFace('Montserrat', `url(${staticFile(`fonts/Montserrat-${w}.woff2`)}) format('woff2')`, {
        weight: String(w),
      });
      document.fonts.add(face);
      return face.load();
    }),
  )
    .then(() => continueRender(handle))
    .catch((err) => {
      console.error(err);
      continueRender(handle);
    });
}

export const C = {
  bgDeep: '#06140d',
  bgMid: '#0d2d1c',
  leaf: '#7bc043',
  turmeric: '#f6b40e',
  turmericDeep: '#e07b00',
  hitam: '#5b4bb7',
  cream: '#fff6e0',
};
