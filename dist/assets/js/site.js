/* ==========================================================================
   Good Vibes Va'a — comportamento do site
   - Navegação (header sólido ao rolar, menu mobile acessível)
   - Barra fixa mobile
   - Formulários das três jornadas → solicitação via WhatsApp
   - Ponto único de integração para reservas/pagamentos futuros

   Os textos de cada idioma vêm do HTML da própria página
   (<script type="application/json" id="i18n">), nunca de troca de texto via JS.
   ========================================================================== */

const CONFIG = window.GVV_CONFIG || {};
const I18N = JSON.parse(document.getElementById('i18n')?.textContent || '{}');

/* ---------- Header ---------- */
function initHeader() {
  const header = document.querySelector('.header');
  const btn = document.querySelector('.menu-btn');
  const mobileNav = document.getElementById('mobile-nav');
  if (!header) return;

  const hero = document.querySelector('.hero');
  const setSolid = () => {
    const limit = hero ? hero.offsetHeight - 120 : 40;
    header.classList.toggle('is-solid', window.scrollY > Math.min(limit, 80));
  };
  setSolid();
  window.addEventListener('scroll', setSolid, { passive: true });

  if (!btn || !mobileNav) return;
  const close = () => {
    header.classList.remove('is-open');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', I18N.menuOpen);
    document.body.style.overflow = '';
  };
  btn.addEventListener('click', () => {
    const open = !header.classList.contains('is-open');
    header.classList.toggle('is-open', open);
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? I18N.menuClose : I18N.menuOpen);
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) mobileNav.querySelector('a')?.focus();
  });
  mobileNav.addEventListener('click', (e) => { if (e.target.closest('a')) close(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && header.classList.contains('is-open')) { close(); btn.focus(); }
  });
  window.matchMedia('(min-width: 1080px)').addEventListener('change', (m) => { if (m.matches) close(); });
}

/* ---------- Barra fixa mobile: aparece depois do hero ---------- */
function initDock() {
  const dock = document.querySelector('.dock');
  const hero = document.querySelector('.hero');
  if (!dock || !hero || !('IntersectionObserver' in window)) return;
  new IntersectionObserver(([entry]) => {
    dock.classList.toggle('is-visible', !entry.isIntersecting);
    dock.toggleAttribute('inert', entry.isIntersecting);
  }).observe(hero);
}

/* ---------- Formulários ---------- */
function formatDate(value) {
  if (!value) return '';
  const [y, m, d] = value.split('-');
  return I18N.locale === 'en' ? `${m}/${d}/${y}` : `${d}/${m}/${y}`;
}

function collect(form) {
  const rows = [];
  form.querySelectorAll('[data-label]').forEach((el) => {
    let value = el.value.trim();
    if (!value) return;
    if (el.tagName === 'SELECT') value = el.options[el.selectedIndex].text;
    if (el.type === 'date') value = formatDate(value);
    rows.push({ name: el.name, label: el.dataset.label, value });
  });
  return rows;
}

function buildMessage(form, rows) {
  const intro = form.dataset.intro;
  const lines = rows.map((r) => `• ${r.label}: ${r.value}`);
  return [intro, '', ...lines].join('\n');
}

function validate(form) {
  let firstInvalid = null;
  form.querySelectorAll('[required]').forEach((el) => {
    const error = document.getElementById(`${el.id}-error`);
    let msg = '';
    if (!el.value.trim()) msg = I18N.required;
    else if (el.type === 'date' && el.min && el.value < el.min) msg = I18N.datePast;
    else if (el.type === 'number' && Number(el.value) < Number(el.min || 1)) msg = I18N.minPeople;
    el.setAttribute('aria-invalid', msg ? 'true' : 'false');
    if (error) error.textContent = msg;
    if (msg && !firstInvalid) firstInvalid = el;
  });
  if (firstInvalid) firstInvalid.focus();
  return !firstInvalid;
}

/**
 * Ponto único de envio. Hoje: abre o WhatsApp com a solicitação pronta.
 * Quando houver backend de reservas/pagamentos, defina GVV_CONFIG.requestEndpoint
 * e esta função enviará o JSON { journey, locale, fields } por POST.
 */
async function submitRequest(form, rows) {
  const journey = form.dataset.journey;
  if (CONFIG.requestEndpoint) {
    const res = await fetch(CONFIG.requestEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ journey, locale: I18N.locale, fields: rows }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return 'sent';
  }
  const text = encodeURIComponent(buildMessage(form, rows));
  const url = `https://wa.me/${CONFIG.whatsapp}?text=${text}`;
  // Abre em nova aba via link real (window.open com 'noopener' sempre retorna null,
  // o que impediria detectar bloqueio de pop-up).
  const a = document.createElement('a');
  a.href = url;
  a.target = '_blank';
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  return 'whatsapp';
}

function initForms() {
  const today = new Date();
  const iso = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  document.querySelectorAll('input[type="date"]').forEach((el) => { el.min = iso; });

  document.querySelectorAll('form[data-journey]').forEach((form) => {
    const status = form.querySelector('.form-status');
    form.addEventListener('input', (e) => {
      const el = e.target;
      if (el.getAttribute('aria-invalid') === 'true' && el.value.trim()) {
        el.setAttribute('aria-invalid', 'false');
        const err = document.getElementById(`${el.id}-error`);
        if (err) err.textContent = '';
      }
    });
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validate(form)) return;
      const btn = form.querySelector('[type="submit"]');
      btn.disabled = true;
      try {
        const result = await submitRequest(form, collect(form));
        status.textContent = result === 'sent' ? I18N.sent : I18N.openedWhatsapp;
      } catch (err) {
        status.textContent = I18N.sendError;
      } finally {
        btn.disabled = false;
      }
    });
  });
}

/* ---------- Pré-seleção a partir dos links "Solicitar" ---------- */
function initPreselect() {
  document.querySelectorAll('[data-preselect]').forEach((link) => {
    link.addEventListener('click', () => {
      const [selectId, value] = link.dataset.preselect.split(':');
      const select = document.getElementById(selectId);
      if (select) select.value = value;
    });
  });
}

/* ---------- Jornadas em abas ----------
   Sem JS, os três painéis aparecem em sequência (links âncora normais).
   Com JS, só o painel escolhido fica visível, e links do menu (#treinar,
   #particular…) abrem a aba certa. */
function initTabs() {
  const root = document.querySelector('.journeys');
  if (!root) return;
  const tabs = [...root.querySelectorAll('[role="tab"]')];
  const panels = tabs.map((t) => document.getElementById(t.getAttribute('aria-controls')));
  const ids = panels.map((p) => p.id);
  root.classList.add('js-tabs');

  const select = (id, { focus = false, scroll = false } = {}) => {
    tabs.forEach((tab, i) => {
      const on = panels[i].id === id;
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
      panels[i].hidden = !on;
      if (on && focus) tab.focus();
    });
    if (scroll) root.querySelector('.tabs').scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const fromHash = (hash) => {
    const id = (hash || '').slice(1);
    if (ids.includes(id)) return id;
    if (id === 'primeira-remada') return 'experimentar';
    return null;
  };

  select(fromHash(location.hash) || ids[0]);
  if (fromHash(location.hash)) requestAnimationFrame(() => select(fromHash(location.hash), { scroll: true }));

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      select(ids[i]);
      history.replaceState(null, '', `#${ids[i]}`);
    });
    tab.addEventListener('keydown', (e) => {
      const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (e.key in keys) {
        e.preventDefault();
        select(ids[(i + keys[e.key] + ids.length) % ids.length], { focus: true });
      } else if (e.key === 'Home' || e.key === 'End') {
        e.preventDefault();
        select(ids[e.key === 'Home' ? 0 : ids.length - 1], { focus: true });
      }
    });
  });

  // Links em qualquer lugar da página que apontam para uma jornada
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || a.getAttribute('role') === 'tab') return;
    const id = fromHash(a.getAttribute('href'));
    if (!id) return;
    e.preventDefault();
    select(id, { scroll: true });
    history.replaceState(null, '', `#${id}`);
  });
}

/* ---------- Ano no rodapé ---------- */
function initYear() {
  document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
}

initHeader();
initDock();
initTabs();
initForms();
initPreselect();
initYear();
