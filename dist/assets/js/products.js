/* ==========================================================================
   Página /produtos — modal de detalhes do produto.

   Os cartões já vêm renderizados no HTML (ver build.py, render_produtos).
   Este módulo só abre/fecha o modal e monta o conteúdo a partir de
   I18N.products (injetado no <script id="i18n">) — tamanho/cor só
   aparecem quando o produto tem a lista preenchida (ver products.py).
   ========================================================================== */

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (str, vars) => str.replace(/\{(\w+)\}/g, (_, k) => vars[k]);
const ICON_WA = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor" width="18" height="18"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 1.9s.8 2.2.9 2.4c.1.1 1.6 2.5 3.9 3.5 1.5.6 2 .7 2.7.6.4-.1 1.3-.5 1.5-1 .2-.5.2-1 .1-1.1l-.5-.2Z"/></svg>';

export function initProducts({ config, i18n }) {
  const overlay = document.querySelector('[data-pmodal-overlay]');
  if (!overlay) return;
  const bodyEl = overlay.querySelector('[data-pmodal-body]');
  const closeBtn = overlay.querySelector('[data-pmodal-close]');
  const T = i18n.produtos;
  const products = i18n.products || [];
  const byId = new Map(products.map((p) => [p.id, p]));

  let current = null;
  let selection = { size: null, color: null };
  let lastFocus = null;

  function waLink(product) {
    let text = fmt(T.waIntro, { product: product.name });
    if (selection.size) text += ` — ${T.sizeLabel}: ${selection.size}`;
    if (selection.color) text += ` — ${T.colorLabel}: ${selection.color}`;
    return `https://wa.me/${config.whatsapp}?text=${encodeURIComponent(text)}`;
  }

  function render() {
    const p = current;
    const sizesHtml = p.sizes.length
      ? `<div class="pmodal-field"><span class="pmodal-label">${esc(T.sizeLabel)}</span>
          <div class="pmodal-opts">${p.sizes.map((s) => `<button type="button" class="pmodal-opt" data-size="${esc(s)}" aria-pressed="${selection.size === s}">${esc(s)}</button>`).join('')}</div></div>`
      : '';
    const colorsHtml = p.colors.length
      ? `<div class="pmodal-field"><span class="pmodal-label">${esc(T.colorLabel)}</span>
          <div class="pmodal-opts pmodal-opts--color">${p.colors.map((c) => `<button type="button" class="pmodal-color" data-color="${esc(c.name)}" aria-pressed="${selection.color === c.name}" style="--swatch:${esc(c.hex)}" aria-label="${esc(c.name)}"></button>`).join('')}</div></div>`
      : '';
    bodyEl.innerHTML = `
      <figure class="pmodal-media"><img src="${esc(p.image)}" alt="${esc(p.imageAlt)}" width="900" height="900" loading="lazy"></figure>
      <div class="pmodal-info">
        <span class="pmodal-cat">${esc(p.category)}</span>
        <h3 class="pmodal-title" id="pmodal-title" tabindex="-1">${esc(p.name)}</h3>
        <p class="pmodal-desc">${esc(p.description)}</p>
        <p class="pmodal-price">${esc(p.priceLabel)}</p>
        <p class="pmodal-stock pmodal-stock--${esc(p.stock)}">${esc(p.stockLabel)}</p>
        ${sizesHtml}${colorsHtml}
        <a class="btn btn--dark pmodal-buy" data-pmodal-buy href="${waLink(p)}" target="_blank" rel="noopener">${ICON_WA}${esc(T.buyCta)}</a>
      </div>`;
  }

  function open(id) {
    const p = byId.get(id);
    if (!p) return;
    current = p;
    selection = { size: null, color: null };
    lastFocus = document.activeElement;
    render();
    overlay.hidden = false;
    document.body.classList.add('pmodal-open');
    overlay.querySelector('.pmodal-title')?.focus({ preventScroll: true });
  }

  function close() {
    overlay.hidden = true;
    document.body.classList.remove('pmodal-open');
    current = null;
    lastFocus?.focus?.();
  }

  function focusable() {
    return [...overlay.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')];
  }

  document.querySelectorAll('[data-open-product]').forEach((btn) => {
    btn.addEventListener('click', () => open(btn.dataset.openProduct));
  });
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  overlay.addEventListener('keydown', (e) => {
    if (overlay.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key === 'Tab') {
      const items = focusable();
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  bodyEl.addEventListener('click', (e) => {
    const sizeBtn = e.target.closest('[data-size]');
    if (sizeBtn) { selection.size = selection.size === sizeBtn.dataset.size ? null : sizeBtn.dataset.size; render(); return; }
    const colorBtn = e.target.closest('[data-color]');
    if (colorBtn) { selection.color = selection.color === colorBtn.dataset.color ? null : colorBtn.dataset.color; render(); }
  });
}
