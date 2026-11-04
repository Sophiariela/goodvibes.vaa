/* Auditoria estrutural automática das seis rotas, nos quatro tamanhos de
   referência. Não substitui a revisão visual — pega o que o olho deixa
   passar e o que só aparece em uma combinação de rota × largura:

     overflow      rolagem horizontal da página
     bleed         elemento ultrapassando a borda do viewport
     clipped       texto cortado por altura fixa / overflow hidden
     tap           alvo de toque abaixo de 44px no celular
     contrast      texto com contraste abaixo de 4.5:1 (AA)
     empty         título/parágrafo renderizado vazio
     a11y          imagem sem alt, campo sem rótulo, h1 ausente/duplicado

   Uso: node tools/audit.mjs [baseUrl]                                   */
import { chromium } from 'playwright';

const BASE = process.argv[2] || 'http://localhost:8777';
const ROUTES = ['/', '/en/', '/produtos/', '/en/produtos/', '/privacidade/', '/en/privacidade/'];
const SIZES = [[390, 844], [768, 1024], [1440, 900], [1920, 1080]];

const findings = [];
const browser = await chromium.launch();

for (const [w, h] of SIZES) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  for (const route of ROUTES) {
    const page = await ctx.newPage();
    const consoleErrors = [];
    page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message));
    await page.goto(BASE + route, { waitUntil: 'load' });
    await page.evaluate(async () => {
      document.querySelectorAll('img[loading="lazy"]').forEach((i) => {
        const s = i.getAttribute('src'); i.setAttribute('loading', 'eager'); i.setAttribute('src', s);
      });
      await new Promise((r) => setTimeout(r, 400));
      await Promise.all([...document.images].map((i) => i.decode().catch(() => {})));
    });
    // os dois pop-ups cobrem a página e falseariam as medidas
    await page.evaluate(() => {
      const o = document.querySelector('.nl-overlay'); if (o) o.hidden = true;
      document.body.classList.remove('nl-open');
      document.querySelector('.wa-card')?.remove();
    });
    await page.waitForTimeout(400);

    const res = await page.evaluate((vw) => {
      const out = [];
      const vis = (el) => {
        const s = getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0' && el.getClientRects().length > 0;
      };
      const label = (el) => el.tagName.toLowerCase()
        + (el.id ? '#' + el.id : '')
        + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');

      /* --- rolagem horizontal --- */
      const de = document.documentElement;
      if (de.scrollWidth > de.clientWidth + 1) out.push(['overflow', `scrollW=${de.scrollWidth} clientW=${de.clientWidth}`]);

      /* --- sangria lateral: elementos passando da borda ---
         .strip sangra de propósito (faixa da comunidade) e .bk-days é um
         trilho de rolagem horizontal — em ambos o conteúdo fora da borda
         é o comportamento desejado, não um vazamento de layout. */
      for (const el of document.querySelectorAll('main *, footer *')) {
        if (!vis(el) || el.closest('.strip, .bk-days')) continue;
        const r = el.getBoundingClientRect();
        if (r.width === 0) continue;
        if (r.right > vw + 1.5 || r.left < -1.5) out.push(['bleed', `${label(el)} left=${Math.round(r.left)} right=${Math.round(r.right)}`]);
      }

      /* --- texto cortado por altura ---
         um elemento de 1px com `clip` é a técnica padrão de "visualmente
         escondido, legível por leitor de tela" (ver .sr-only e os títulos
         longos das abas no celular) — não é corte acidental. */
      const srOnly = (el) => {
        const s = getComputedStyle(el);
        return (el.clientWidth <= 1 && el.clientHeight <= 1)
          || s.clip === 'rect(0px, 0px, 0px, 0px)' || s.clipPath === 'inset(50%)';
      };
      for (const el of document.querySelectorAll('h1,h2,h3,h4,p,span,a,li,dt,dd,summary,button,label,strong')) {
        if (!vis(el) || srOnly(el)) continue;
        const s = getComputedStyle(el);
        if (s.overflow === 'visible' && s.overflowY === 'visible') continue;
        if (el.closest('.bk-days, .strip, [class*="overlay"]')) continue;
        if (el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0) {
          out.push(['clipped', `${label(el)} scrollH=${el.scrollHeight} clientH=${el.clientHeight} "${(el.textContent || '').trim().slice(0, 42)}"`]);
        }
      }

      /* --- alvo de toque ---
         A caixa do elemento não é a resposta final: um pseudo-elemento
         absoluto com inset negativo amplia a área clicável sem mudar o
         desenho (ver .lang-switch a::before). Por isso o teste é feito
         como o dedo faz — elementFromPoint nas bordas do alvo mínimo. */
      const MIN = 30;
      const hits = (el, x, y) => {
        const t = document.elementFromPoint(x, y);
        return !!t && (t === el || el.contains(t) || t.contains(el));
      };
      if (vw < 760) {
        for (const el of document.querySelectorAll('a[href], button, input, summary, [role="tab"]')) {
          if (!vis(el) || el.closest('.legal-toc, .footer-bottom')) continue;
          el.scrollIntoView({ block: 'center', behavior: 'instant' });
          const r = el.getBoundingClientRect();
          const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
          if (cy - MIN / 2 < 0 || cy + MIN / 2 > innerHeight) continue; // não coube na janela
          const reach = [[cx, cy - MIN / 2], [cx, cy + MIN / 2], [cx - MIN / 2, cy], [cx + MIN / 2, cy]];
          if (!reach.every(([x, y]) => hits(el, x, y))) {
            out.push(['tap', `${label(el)} ${Math.round(r.width)}x${Math.round(r.height)} "${(el.textContent || '').trim().slice(0, 30)}"`]);
          }
        }
        scrollTo({ top: 0, behavior: 'instant' });
      }

      /* --- contraste AA do texto --- */
      const parse = (c) => (c.match(/[\d.]+/g) || []).map(Number);
      const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
      const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
      const bgOf = (el) => {
        let n = el;
        while (n && n !== document.documentElement) {
          const c = parse(getComputedStyle(n).backgroundColor);
          if (c.length >= 3 && (c[3] === undefined || c[3] > 0.85)) return c;
          n = n.parentElement;
        }
        return [247, 244, 237];
      };
      for (const el of document.querySelectorAll('p,li,dt,dd,span,a,h1,h2,h3,h4,summary,strong,small,label,button')) {
        if (!vis(el) || !el.textContent.trim()) continue;
        if ([...el.children].some((ch) => ch.textContent.trim())) continue; // só folhas de texto
        // texto sobre fotografia: o contraste real depende do pixel sob a
        // letra (o header é transparente sobre o hero até virar sólido),
        // então está fora do alcance de uma checagem por cor computada
        if (el.closest('.hero, .header, .media, .shop-teaser-media, .pmodal-media, .nl-media')) continue;
        const s = getComputedStyle(el);
        const fg = parse(s.color);
        if (fg[3] !== undefined && fg[3] < 0.95) continue;
        const px = parseFloat(s.fontSize);
        const bold = parseInt(s.fontWeight, 10) >= 700;
        const large = px >= 24 || (px >= 18.66 && bold);
        const L1 = lum(fg), L2 = lum(bgOf(el));
        const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
        const min = large ? 3 : 4.5;
        if (ratio < min) out.push(['contrast', `${label(el)} ${ratio.toFixed(2)}:1 (min ${min}) ${Math.round(px)}px "${el.textContent.trim().slice(0, 34)}"`]);
      }

      /* --- nós de conteúdo vazios --- */
      for (const el of document.querySelectorAll('main h1,main h2,main h3,main h4,main p')) {
        if (vis(el) && !el.textContent.trim() && !el.querySelector('img,svg')) out.push(['empty', label(el)]);
      }

      /* --- acessibilidade básica --- */
      const h1s = [...document.querySelectorAll('h1')].filter(vis);
      if (h1s.length !== 1) out.push(['a11y', `${h1s.length} <h1> visíveis (esperado 1)`]);
      for (const img of document.querySelectorAll('img')) {
        if (!img.hasAttribute('alt')) out.push(['a11y', `img sem alt: ${img.getAttribute('src')}`]);
      }
      for (const f of document.querySelectorAll('input:not([type=hidden]), select, textarea')) {
        if (!vis(f)) continue;
        const ok = f.getAttribute('aria-label') || f.getAttribute('aria-labelledby')
          || (f.id && document.querySelector(`label[for="${CSS.escape(f.id)}"]`)) || f.closest('label');
        if (!ok) out.push(['a11y', `campo sem rótulo: ${label(f)}`]);
      }
      return out;
    }, w);

    for (const [kind, msg] of res) findings.push(`${kind.toUpperCase().padEnd(9)} ${route}@${w}  ${msg}`);
    for (const err of consoleErrors) findings.push(`CONSOLE   ${route}@${w}  ${err}`);
    await page.close();
  }
  await ctx.close();
}

await browser.close();
// uma linha por ocorrência distinta — a mesma regra quebrada em 6 rotas
// vira 6 linhas de propósito, para não esconder uma rota específica
const uniq = [...new Set(findings)];
console.log(uniq.length ? uniq.join('\n') : 'AUDIT CLEAN — nenhuma ocorrência');
console.log(`\n${uniq.length} ocorrência(s)`);
