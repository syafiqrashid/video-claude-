// node render.js <build_dir> <out.mp4> <audio.wav|-> <width> <fps> [stillsTimes...]
// env FRAMES=a:b renders only frames [a,b) ; audio '-' = video only (for parallel chunks)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [dir, out, audio, W, FPS, ...stills] = process.argv.slice(2);
  const w = +W, h = Math.round(w * 9 / 16), fps = +FPS;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: w / 1920 });
  await page.goto('file://' + path.resolve(dir, 'index.html'));
  await page.evaluate(() => window.ready);
  const dur = await page.evaluate(() => window.DURATION);
  if (stills.length) {
    for (const t of stills) { await page.evaluate(t => render(+t), t); await page.screenshot({ path: `${out}_${t}.png` }); }
    await browser.close(); return;
  }
  const aud = audio === '-' ? ['-map', '0:v'] : ['-i', audio, '-filter_complex', `[1:a]adelay=4000|4000,apad[a]`, '-map', '0:v', '-map', '[a]'];
  const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    ...aud,
    '-c:v', 'libx264', '-preset', w > 1000 ? 'medium' : 'veryfast', '-crf', w > 1000 ? '18' : '26', '-pix_fmt', 'yuv420p',
    '-vf', `scale=${w}:${h}`, '-c:a', 'aac', '-b:a', w > 1000 ? '256k' : '128k', ...(audio === '-' ? [] : ['-shortest']), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.ceil(dur * fps); const t0 = Date.now();
  const [fa, fb] = (process.env.FRAMES || `0:${N}`).split(':').map(Number);
  for (let i = fa; i < Math.min(fb, N); i++) {
    await page.evaluate(t => render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: w > 1000 ? 95 : 85 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (fps * 15) === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close();
  console.log('done', out);
})();
