/* Viewport-sized crops of specific sections, for judging composition at
   real scale (full-page shots shrink everything at 1920).
   Usage: node tools/crops.mjs <outDir> [baseUrl]  */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const OUT = process.argv[2] || 'crops';
const BASE = process.argv[3] || 'http://localhost:8777';
const SIZES = [[390, 844], [768, 1024], [1440, 900], [1920, 1080]];
const TARGETS = [
  ['hero', '/', null],
  ['journeys', '/', '#experiencias'],
  ['club', '/', '#clube'],
  ['community', '/', '.strip'],
  ['shop', '/', '.shop-teaser'],
  ['info', '/', '#local'],
  ['closing', '/', '.closing'],
  ['footer', '/', '.footer'],
  ['produtos', '/produtos/', null],
  ['legal', '/privacidade/', null],
];

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
for (const [w, h] of SIZES) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  for (const [name, path, sel] of TARGETS) {
    const page = await ctx.newPage();
    await page.goto(BASE + path, { waitUntil: 'load' });
    await page.evaluate(async () => {
      document.querySelectorAll('img[loading="lazy"]').forEach((i) => {
        const s = i.getAttribute('src'); i.setAttribute('loading', 'eager'); i.setAttribute('src', s);
      });
      const o = document.querySelector('.nl-overlay'); if (o) o.hidden = true;
      document.body.classList.remove('nl-open');
      // o pop-up do WhatsApp abre sozinho uma vez por visita e cobriria o
      // canto inferior direito de toda crop de revisão
      const wa = document.querySelector('.wa-card'); if (wa) wa.remove();
      await new Promise((r) => setTimeout(r, 500));
      await Promise.all([...document.images].map((i) => i.decode().catch(() => {})));
    });
    if (sel) {
      await page.evaluate((s) => {
        const el = document.querySelector(s);
        if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY, behavior: 'instant' });
      }, sel);
    }
    await page.waitForTimeout(700);
    await page.screenshot({ path: `${OUT}/${name}-${w}.png` });
    await page.close();
  }
  await ctx.close();
}
await browser.close();
console.log('crops done ->', OUT);
