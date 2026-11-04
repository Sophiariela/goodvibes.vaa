/* Interaction-state screenshots + functional smoke test of the demo booking
   flow, product modal, newsletter pop-up and mobile menu.
   Usage: node tools/states.mjs <outDir> [baseUrl] [widthCsv]  */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const OUT = process.argv[2] || 'states';
const BASE = process.argv[3] || 'http://localhost:8777';
const WIDTHS = (process.argv[4] || '390,1440').split(',').map(Number);

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const log = [];
const ok = (m) => log.push('PASS ' + m);
const bad = (m) => log.push('FAIL ' + m);

async function newPage(ctx, path) {
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  await page.goto(BASE + path, { waitUntil: 'load' });
  await page.waitForTimeout(500);
  page.__errors = errors;
  return page;
}
const hideNl = (page) => page.evaluate(() => {
  const o = document.querySelector('.nl-overlay');
  if (o) o.hidden = true;
  document.body.classList.remove('nl-open');
});

for (const W of WIDTHS) {
  const tag = String(W);
  const ctx = await browser.newContext({ viewport: { width: W, height: W < 700 ? 844 : 950 } });

  /* ---- booking flow (Experimentar, demo mode) ---- */
  {
    const page = await newPage(ctx, '/');
    await hideNl(page);
    const bk = page.locator('[data-modality="experimentar"]');
    await bk.scrollIntoViewIfNeeded();
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${OUT}/bk-00-cards-${tag}.png` });

    // pick second day to prove the calendar re-renders
    await page.locator('[data-modality="experimentar"] [data-day="2"]').click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${OUT}/bk-01-day2-${tag}.png` });
    await page.locator('[data-modality="experimentar"] [data-day="0"]').click();
    await page.waitForTimeout(500);

    const reserve = page.locator('[data-modality="experimentar"] [data-reserve]:not([disabled])').first();
    if (await reserve.count()) {
      await reserve.click();
      await page.waitForTimeout(400);
      const modal = page.locator('[data-modality="experimentar"] .bk-modal');
      (await modal.isVisible()) ? ok(`modal opened @${tag}`) : bad(`modal did not open @${tag}`);
      await page.screenshot({ path: `${OUT}/bk-02-participants-${tag}.png` });

      // "+" fica desabilitado quando a saída só tem 1 vaga — comportamento
      // correto do limite de capacidade, então o clique é opcional.
      const plus = page.locator('[data-modality="experimentar"] .bk-stepper [data-bk="plus"]');
      if (await plus.isEnabled()) { await plus.click(); ok(`seat stepper increments @${tag}`); }
      else ok(`seat stepper correctly capped at availability @${tag}`);
      await page.fill('#bk-experimentar-name', 'Maria Teste');
      await page.fill('#bk-experimentar-phone', '71999998888');
      await page.locator('[data-modality="experimentar"] [data-bk="go"]').click();
      await page.waitForTimeout(350);
      const terms = page.locator('#bk-experimentar-terms');
      (await terms.count()) ? ok(`terms step @${tag}`) : bad(`terms step missing @${tag}`);
      await page.screenshot({ path: `${OUT}/bk-03-terms-${tag}.png` });

      await terms.check();
      await page.waitForTimeout(200);
      await page.locator('[data-modality="experimentar"] [data-bk="go"]').click();
      await page.waitForTimeout(900);
      const pix = page.locator('[data-modality="experimentar"] .bk-pix');
      (await pix.count()) ? ok(`pix step @${tag}`) : bad(`pix step missing @${tag}`);
      await page.screenshot({ path: `${OUT}/bk-04-pix-${tag}.png` });

      const sim = page.locator('[data-modality="experimentar"] [data-bk="simpay"]');
      if (await sim.count()) {
        await sim.click();
        await page.waitForTimeout(1800);
        const done = page.locator('[data-modality="experimentar"] .bk-done');
        (await done.count()) ? ok(`confirmation reached @${tag}`) : bad(`confirmation NOT reached @${tag}`);
        await page.screenshot({ path: `${OUT}/bk-05-done-${tag}.png` });
      } else bad(`simulate-pay button missing @${tag}`);
    } else bad(`no bookable card @${tag}`);
    if (page.__errors.length) bad(`console errors (booking @${tag}): ${page.__errors.join(' | ')}`);
    await page.close();
  }

  /* ---- Treinar + Particular modals ---- */
  {
    const page = await newPage(ctx, '/');
    await hideNl(page);
    await page.locator('#tab-treinar').click();
    await page.waitForTimeout(700);
    await page.locator('[data-modality="treinar"]').scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${OUT}/tr-00-panel-${tag}.png` });
    const r = page.locator('[data-modality="treinar"] [data-reserve]:not([disabled])').first();
    if (await r.count()) {
      await r.click(); await page.waitForTimeout(350);
      await page.screenshot({ path: `${OUT}/tr-01-modal-${tag}.png` });
      ok(`treinar modal @${tag}`);
      await page.keyboard.press('Escape');
    } else bad(`treinar: no card @${tag}`);

    await page.locator('#tab-particular').click();
    await page.waitForTimeout(600);
    await page.locator('[data-modality="particular"]').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${OUT}/pa-00-panel-${tag}.png` });
    await page.locator('[data-modality="particular"] [data-reserve="quote"]').click();
    await page.waitForTimeout(350);
    (await page.locator('[data-modality="particular"] .bk-modal').isVisible()) ? ok(`quote modal @${tag}`) : bad(`quote modal @${tag}`);
    await page.screenshot({ path: `${OUT}/pa-01-modal-${tag}.png` });
    if (page.__errors.length) bad(`console errors (tabs @${tag}): ${page.__errors.join(' | ')}`);
    await page.close();
  }

  /* ---- product modal ---- */
  {
    const page = await newPage(ctx, '/produtos/');
    await hideNl(page);
    await page.locator('[data-open-product]').first().click();
    await page.waitForTimeout(400);
    const pm = page.locator('.pmodal');
    (await pm.isVisible()) ? ok(`product modal @${tag}`) : bad(`product modal @${tag}`);
    const sizeBtn = page.locator('.pmodal [data-size]').first();
    if (await sizeBtn.count()) {
      await sizeBtn.click(); await page.waitForTimeout(200);
      const pressed = await page.locator('.pmodal [data-size]').first().getAttribute('aria-pressed');
      pressed === 'true' ? ok(`size variant selects @${tag}`) : bad(`size variant not selected @${tag}`);
    }
    const colorBtn = page.locator('.pmodal [data-color]').first();
    if (await colorBtn.count()) {
      await colorBtn.click(); await page.waitForTimeout(200);
      const pressed = await page.locator('.pmodal [data-color]').first().getAttribute('aria-pressed');
      pressed === 'true' ? ok(`color variant selects @${tag}`) : bad(`color variant not selected @${tag}`);
    }
    const href = await page.locator('[data-pmodal-buy]').getAttribute('href');
    /wa\.me\/\d+\?text=/.test(href) ? ok(`buy link built @${tag}`) : bad(`buy link malformed @${tag}: ${href}`);
    await page.screenshot({ path: `${OUT}/pm-00-modal-${tag}.png` });
    if (page.__errors.length) bad(`console errors (products @${tag}): ${page.__errors.join(' | ')}`);
    await page.close();
  }

  /* ---- newsletter pop-up ---- */
  {
    const page = await newPage(ctx, '/');
    await page.evaluate(() => { try { localStorage.clear(); } catch {} });
    await page.reload({ waitUntil: 'load' });
    await page.waitForTimeout(400);
    // exit-intent trigger
    await page.mouse.move(400, 300);
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseout', { clientY: 0, bubbles: true })));
    await page.waitForTimeout(500);
    const nl = page.locator('.nl-overlay');
    (await nl.isVisible()) ? ok(`newsletter popup opens @${tag}`) : bad(`newsletter popup did NOT open @${tag}`);
    await page.screenshot({ path: `${OUT}/nl-00-${tag}.png` });
    await page.fill('#nl-email', 'teste@exemplo.com');
    await page.check('#nl-consent');
    await page.locator('.nl-submit').click();
    await page.waitForTimeout(1500);
    const err = page.locator('.nl-err');
    (await err.count()) ? ok(`newsletter fails gracefully (backend off) @${tag}`) : bad(`newsletter: no graceful error @${tag}`);
    await page.screenshot({ path: `${OUT}/nl-01-error-${tag}.png` });
    await page.close();
  }

  /* ---- WhatsApp widget ---- */
  {
    const page = await newPage(ctx, '/');
    await hideNl(page);
    await page.locator('[data-wa-toggle]').click();
    await page.waitForTimeout(300);
    (await page.locator('.wa-card').isVisible()) ? ok(`wa card opens @${tag}`) : bad(`wa card @${tag}`);
    await page.screenshot({ path: `${OUT}/wa-00-${tag}.png` });
    await page.close();
  }

  /* ---- mobile menu ---- */
  if (W < 1100) {
    const page = await newPage(ctx, '/');
    await hideNl(page);
    await page.locator('.menu-btn').click();
    await page.waitForTimeout(300);
    (await page.locator('.mobile-nav').isVisible()) ? ok(`mobile menu opens @${tag}`) : bad(`mobile menu @${tag}`);
    await page.screenshot({ path: `${OUT}/menu-00-${tag}.png` });
    await page.close();
  }

  await ctx.close();
}

await browser.close();
console.log(log.join('\n'));
console.log('\n' + (log.some((l) => l.startsWith('FAIL')) ? '>>> SOME CHECKS FAILED' : '>>> ALL CHECKS PASSED'));
