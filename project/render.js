// Usage: node render.js <map.json> <script.json> <out.mp4|--stills> <audio.wav> [times...]
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path'); const { spawn } = require('child_process');
(async () => {
  const [mapF, scriptF, out, audio, ...times] = process.argv.slice(2);
  const m = JSON.parse(fs.readFileSync(mapF)); const s = JSON.parse(fs.readFileSync(scriptF));
  const data = { map: m.map, dur: m.dur, scenes: s.scenes, lines: s.lines };
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 854, height: 480 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'motion.html'));
  await page.evaluate(d => init(d), data);
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => { drawFrame(1); drawFrame(5); }); // warm fonts/emoji
  if (out === '--stills') {
    for (const t of times) {
      const [u] = await page.evaluate(([t]) => framesJPEG(t, 1, 25), [parseFloat(t)]);
      fs.writeFileSync(`still_${t}.jpg`, Buffer.from(u.split(',')[1], 'base64'));
    }
    await browser.close(); return;
  }
  const fps = 25, total = Math.ceil(data.dur * fps);
  const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '28', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '96k', '-ac', '1', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const B = 50;
  for (let f = 0; f < total; f += B) {
    const n = Math.min(B, total - f);
    const urls = await page.evaluate(([t0, n, fps]) => framesJPEG(t0, n, fps), [f / fps, n, fps]);
    for (const u of urls) { if (!ff.stdin.write(Buffer.from(u.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r)); }
    if (f % 1000 === 0) process.stdout.write(`frame ${f}/${total}\n`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close(); console.log('done', out);
})();
