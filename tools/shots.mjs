/* Screenshot harness for visual review. Not part of the site build.
   Usage: node tools/shots.mjs <outDir> [baseUrl]  */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const OUT = process.argv[2] || 'shots';
const BASE = process.argv[3] || 'http://localhost:8777';

const ROUTES = [
  ['home-pt', '/'],
  ['home-en', '/en/'],
  ['produtos-pt', '/produtos/'],
  ['produtos-en', '/en/produtos/'],
  ['privacidade-pt', '/privacidade/'],
  ['privacidade-en', '/en/privacidade/'],
];
const SIZES = [
  ['390', 390, 844],
  ['768', 768, 1024],
  ['1440', 1440, 900],
  ['1920', 1920, 1080],
];

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const problems = [];

for (const [label, w, h] of SIZES) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  for (const [name, path] of ROUTES) {
    const page = await ctx.newPage();
    const errors = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    await page.goto(BASE + path, { waitUntil: 'load' });
    // force lazy images to decode so full-page shots are not full of holes
    await page.evaluate(async () => {
      document.querySelectorAll('img[loading="lazy"]').forEach((i) => {
        const src = i.getAttribute('src');
        i.setAttribute('loading', 'eager');
        i.setAttribute('src', src); // re-kick the fetch now that it is eager
      });
      await new Promise((r) => setTimeout(r, 400));
      await Promise.all([...document.images].map((i) => i.decode().catch(() => {})));
    });
    await page.waitForTimeout(1200);
    // kill the newsletter pop-up so it never covers review shots
    await page.evaluate(() => {
      const o = document.querySelector('.nl-overlay');
      if (o) o.hidden = true;
      document.body.classList.remove('nl-open');
    });
    const overflow = await page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth,
      clientW: document.documentElement.clientWidth,
    }));
    if (overflow.scrollW > overflow.clientW + 1) {
      problems.push(`OVERFLOW ${name}@${label}: scrollW=${overflow.scrollW} clientW=${overflow.clientW}`);
    }
    if (errors.length) problems.push(`CONSOLE ${name}@${label}: ${errors.join(' | ')}`);
    await page.screenshot({ path: `${OUT}/${name}-${label}.png`, fullPage: true });
    await page.close();
  }
  await ctx.close();
}

await browser.close();
console.log(problems.length ? problems.join('\n') : 'no overflow / no console errors');
