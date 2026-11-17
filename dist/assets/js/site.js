/* ==========================================================================
   Good Vibes Va'a — comportamento do site
   - Navegação (header sólido ao rolar, menu mobile acessível)
   - Barra fixa mobile
   - Formulários de Treinar/Particular → solicitação via site ou WhatsApp,
     conforme GVV_CONFIG.bookingMode ("demo" | "live" | "off")
   - Reserva de Experimentar (booking.js) e pop-up do WhatsApp (wa-widget.js)

   Os textos de cada idioma vêm do HTML da própria página
   (<script type="application/json" id="i18n">), nunca de troca de texto via JS.
   ========================================================================== */

import { initBooking } from './booking.js';
import { initWaWidget } from './wa-widget.js';
import { initNewsletter } from './newsletter.js';
import { initProducts, initProductFilters } from './products.js';
import { initContact } from './contact.js';

const CONFIG = window.GVV_CONFIG || {};
const I18N = JSON.parse(document.getElementById('i18n')?.textContent || '{}');

/* ---------- Header ---------- */
function initHeader() {
  const header = document.querySelector('.header');
  if (!header) return;

  const hero = document.querySelector('.hero');
  // Sem hero (páginas internas) o cabeçalho é sempre sólido: o estado
  // transparente só existe para ficar sobre a fotografia do hero — sobre o
  // off-white da página o menu claro seria invisível. build.py já entrega
  // essas páginas com .is-solid; aqui garantimos que o scroll não remova.
  const setSolid = () => {
    if (!hero) { header.classList.add('is-solid'); return; }
    header.classList.toggle('is-solid', window.scrollY > Math.min(hero.offsetHeight - 120, 80));
  };
  setSolid();
  window.addEventListener('scroll', setSolid, { passive: true });
}

/* ---------- Menu em painel lateral ----------
   A navegação inteira vive aqui, em todas as larguras. O painel nasce
   `inert` no HTML (ver page_header em build.py): sem JS ele continua
   inalcançável e a navegação da página é a do rodapé.

   Foco: ao abrir vai para o primeiro item; Tab circula dentro do painel
   (não há como tabular para a página atrás dele); Esc fecha e devolve o
   foco ao botão. O `inert` só volta depois da transição — aplicá-lo junto
   com o fechamento tiraria o foco de dentro do painel antes de devolvê-lo
   ao botão, e o foco cairia no <body>. */
const MENU_OPEN_CLASS = 'menu-open';
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';

function initMenu() {
  const drawer = document.getElementById('menu-drawer');
  const overlay = document.querySelector('[data-menu-overlay]');
  const toggle = document.querySelector('[data-menu-toggle]');
  if (!drawer || !overlay || !toggle) return;

  const root = document.documentElement;
  const isOpen = () => root.classList.contains(MENU_OPEN_CLASS);
  let closeTimer = null;

  const open = () => {
    if (isOpen()) return;
    window.clearTimeout(closeTimer);
    drawer.removeAttribute('inert');
    root.classList.add(MENU_OPEN_CLASS);
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', I18N.menuClose);
    // Forçar o cálculo de layout antes de focar: no mesmo quadro em que
    // `inert` sai e o painel deixa de ser visibility:hidden, o navegador
    // ainda trata o conteúdo como inerte e .focus() não pega — o foco
    // ficaria no botão, atrás do overlay. Ler offsetWidth sincroniza isso.
    void drawer.offsetWidth;
    drawer.querySelector(FOCUSABLE)?.focus();
  };

  const close = ({ restoreFocus = true } = {}) => {
    if (!isOpen()) return;
    root.classList.remove(MENU_OPEN_CLASS);
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', I18N.menuOpen);
    if (restoreFocus) toggle.focus();
    closeTimer = window.setTimeout(() => {
      if (!isOpen()) drawer.setAttribute('inert', '');
    }, 340);
  };

  toggle.addEventListener('click', () => (isOpen() ? close() : open()));
  overlay.addEventListener('click', () => close());
  drawer.querySelector('[data-menu-close]')?.addEventListener('click', () => close());
  // Fechar ao escolher uma opção, sem roubar o foco do destino do link.
  drawer.addEventListener('click', (e) => { if (e.target.closest('a')) close({ restoreFocus: false }); });

  document.addEventListener('keydown', (e) => {
    if (!isOpen()) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key !== 'Tab') return;
    const items = [...drawer.querySelectorAll(FOCUSABLE)].filter((el) => el.getClientRects().length > 0);
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
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
 * Ponto único de envio das jornadas Treinar/Particular. Depende de
 * GVV_CONFIG.bookingMode:
 *  - "off"  -> abre o WhatsApp com a solicitação pronta (como sempre foi).
 *  - "demo" -> não envia nada de verdade; só confirma na tela (apresentação).
 *  - "live" -> envia { journey, locale, fields } por POST a CONFIG.apiBase.
 */
async function submitRequest(form, rows) {
  const journey = form.dataset.journey;
  const mode = CONFIG.bookingMode || 'off';

  if (mode === 'live' && CONFIG.apiBase) {
    const res = await fetch(`${CONFIG.apiBase.replace(/\/$/, '')}/requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ journey, locale: I18N.locale, fields: rows }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return 'live';
  }

  if (mode === 'demo') return 'demo';

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
        status.textContent = result === 'live' ? I18N.bk.req_live
          : result === 'demo' ? I18N.bk.req_demo
          : I18N.openedWhatsapp;
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

/* ---------- Carrossel de momentos ----------
   Sem JS a faixa continua rolável com o dedo e com o teclado (o trilho tem
   tabindex), e as setas só acrescentam o controle de clique. Elas
   desabilitam nas pontas pra nao ficar um botao que nao faz nada. */
function initCarousel() {
  document.querySelectorAll('.carousel-track').forEach((track) => {
    const btns = [...document.querySelectorAll(`.carousel-btn[data-carousel="${track.id}"]`)];
    if (!btns.length) return;

    const sync = () => {
      const max = track.scrollWidth - track.clientWidth - 2;
      btns.forEach((btn) => {
        btn.disabled = Number(btn.dataset.dir) < 0 ? track.scrollLeft <= 2 : track.scrollLeft >= max;
      });
    };

    btns.forEach((btn) => {
      btn.addEventListener('click', () => {
        track.scrollBy({ left: track.clientWidth * 0.9 * Number(btn.dataset.dir), behavior: 'smooth' });
      });
    });
    track.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync, { passive: true });
    sync();
  });
}

/* ---------- Ano no rodapé ---------- */
function initYear() {
  document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
}

initHeader();
initMenu();
initDock();
initTabs();
initCarousel();
initForms();
initPreselect();
initYear();
initBooking({ config: CONFIG, i18n: I18N });
initWaWidget({ config: CONFIG });
initProducts({ config: CONFIG, i18n: I18N });
initProductFilters();
initNewsletter({ config: CONFIG, i18n: I18N });
initContact({ i18n: I18N });
