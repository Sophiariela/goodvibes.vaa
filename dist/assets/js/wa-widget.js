/* ==========================================================================
   Pop-up do WhatsApp no canto da tela
   - Botão redondo fixo; abre um cartão pequeno com mensagem da equipe.
   - Abre sozinho uma vez por visita (8 s ou ao passar do hero), nunca
     enquanto a pessoa está preenchendo a reserva.
   - Fechado pela pessoa, não reabre sozinho na mesma visita.
   ========================================================================== */

const KEY = 'gvv-wa-dismissed';
const store = {
  get() { try { return sessionStorage.getItem(KEY) === '1'; } catch (e) { return false; } },
  set() { try { sessionStorage.setItem(KEY, '1'); } catch (e) { /* sem storage */ } },
};

export function initWaWidget({ config }) {
  const root = document.querySelector('[data-wa-widget]');
  if (!root) return;
  const card = root.querySelector('.wa-card');
  const fab = root.querySelector('[data-wa-toggle]');
  const form = root.querySelector('[data-wa-form]');
  const text = root.querySelector('textarea');
  const booking = document.querySelector('[data-booking]');

  const open = (byUser) => {
    card.hidden = false;
    root.classList.add('is-open');
    fab.setAttribute('aria-expanded', 'true');
    if (byUser) text.focus();
  };
  const close = (byUser) => {
    card.hidden = true;
    root.classList.remove('is-open');
    fab.setAttribute('aria-expanded', 'false');
    if (byUser) { store.set(); fab.focus(); }
  };

  fab.addEventListener('click', () => (card.hidden ? open(true) : close(true)));
  root.querySelector('[data-wa-close]').addEventListener('click', () => close(true));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !card.hidden) close(true); });

  // Botões "Fale com a equipe" abrem o pop-up em vez de sair da página
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-wa-open]');
    if (!trigger) return;
    e.preventDefault();
    document.querySelector('.header.is-open .menu-btn')?.click();
    open(true);
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = text.value.trim() || root.dataset.default;
    const a = Object.assign(document.createElement('a'), {
      href: `https://wa.me/${config.whatsapp}?text=${encodeURIComponent(msg)}`, target: '_blank', rel: 'noopener',
    });
    document.body.appendChild(a); a.click(); a.remove();
    text.value = '';
    close(false);
  });

  // Abertura automática, uma vez, sem atrapalhar a reserva — nem em foco,
  // nem sobrepondo o cartão enquanto ele está visível na tela. Checagem
  // síncrona de geometria (não só IntersectionObserver) para não cair numa
  // corrida onde o gatilho de "saiu do hero" dispara antes do observer do
  // cartão processar a nova posição.
  const bookingOnScreen = () => {
    if (!booking) return false;
    const r = booking.getBoundingClientRect();
    return r.bottom > 0 && r.top < (window.innerHeight || document.documentElement.clientHeight);
  };
  const busy = () => bookingOnScreen() || (booking && booking.contains(document.activeElement));
  let auto = false;
  let retries = 0;
  const autoOpen = () => {
    if (auto || store.get() || !card.hidden) return;
    if (busy()) { if (retries++ < 20) setTimeout(autoOpen, 3000); return; }
    auto = true;
    open(false);
  };
  setTimeout(autoOpen, 8000);
  const hero = document.querySelector('.hero');
  if (hero && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(([en]) => { if (!en.isIntersecting && window.scrollY > 0) { autoOpen(); io.disconnect(); } });
    io.observe(hero);
  }
  // Se a pessoa começa a reservar, o cartão aberto automaticamente se recolhe
  booking?.addEventListener('focusin', () => { if (!card.hidden && !root.contains(document.activeElement)) close(false); });
}
