// Render each SVG passed on the command line to png/<name>.png at 2x.
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  for (const name of process.argv.slice(2)) {
    await page.goto("file://" + path.join(__dirname, name));
    await page.locator("svg").screenshot({
      path: path.join(__dirname, "png", name.replace(/\.svg$/, ".png")),
      omitBackground: true,
    });
  }
  await browser.close();
})();
