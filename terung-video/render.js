// Render index.html to JPEG frames (30 fps, 30 s) using 4 parallel pages.
const { chromium } = require('playwright');
const fs = require('fs');
const FPS = 30, DUR = 30, N = FPS * DUR, W = 4;
const out = process.argv[2] || 'frames';
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch();
  await Promise.all(Array.from({ length: W }, async (_, w) => {
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    await p.goto('file://' + __dirname + '/index.html');
    await p.evaluate(() => window.ready);
    for (let f = w; f < N; f += W) {
      await p.evaluate(t => seek(t), f / FPS);
      await p.screenshot({ path: `${out}/f${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 92 });
      if (f % 150 === 0) console.log('frame', f);
    }
  }));
  await b.close();
})();
