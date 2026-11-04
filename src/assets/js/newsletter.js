/* ==========================================================================
   Pop-up de captação de e-mail (site inteiro).

   - Não aparece na hora: dispara no primeiro entre (a) alguns segundos na
     página ou (b) o mouse saindo por cima da janela (intenção de sair).
   - Não aparece de novo pra quem já se cadastrou (localStorage permanente)
     nem pra quem fechou recentemente (localStorage com validade de alguns
     dias) — ver SNOOZE_DAYS abaixo.
   - Consentimento de marketing é um campo SEPARADO do e-mail, obrigatório
     pra cadastrar — nunca marcado por padrão.
   - Proteção contra spam sem coletar IP: honeypot (campo escondido) +
     tempo mínimo de preenchimento, ambos verificados de novo no servidor
     (ver api/subscribers.ts) — o cliente só evita o óbvio.
   - Campanha (ver GVV_CONFIG.campaign): quando ligada, troca o título/texto
     pelo da campanha — a inscrição em si nunca muda de comportamento.
   ========================================================================== */

const KEY_SUBSCRIBED = 'gvv-nl-subscribed';
const KEY_SNOOZE_UNTIL = 'gvv-nl-snooze-until';
const SNOOZE_DAYS = 7;
const TIMER_MS = 25000;
const MIN_FILL_MS = 1200;

const store = {
  subscribed() {
    try { return localStorage.getItem(KEY_SUBSCRIBED) === '1'; } catch { return false; }
  },
  markSubscribed() {
    try { localStorage.setItem(KEY_SUBSCRIBED, '1'); } catch { /* sem storage */ }
  },
  snoozed() {
    try {
      const until = Number(localStorage.getItem(KEY_SNOOZE_UNTIL));
      return Number.isFinite(until) && Date.now() < until;
    } catch { return false; }
  },
  snooze() {
    try { localStorage.setItem(KEY_SNOOZE_UNTIL, String(Date.now() + SNOOZE_DAYS * 86400000)); } catch { /* sem storage */ }
  },
};

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function initNewsletter({ config, i18n }) {
  const root = document.querySelector('[data-nl-widget]');
  if (!root) return;
  if (store.subscribed() || store.snoozed()) return;

  const T = i18n.newsletter;
  const campaign = config.campaign && config.campaign.enabled ? config.campaign : null;
  const title = campaign ? campaign.title : T.title;
  const text = campaign ? campaign.text : T.text;
  const campaignKey = campaign ? campaign.key : null;
  const renderedAt = Date.now();

  let step = 'form'; // 'form' | 'success' | 'duplicate'
  let busy = false;
  let error = '';
  let lastFocus = null;

  root.innerHTML = `
    <div class="nl-overlay" data-nl-overlay hidden>
      <div class="nl-modal" role="dialog" aria-modal="true" aria-labelledby="nl-title">
        <button type="button" class="nl-close" data-nl-close aria-label="${esc(T.close)}">
          <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 5l14 14M19 5L5 19"/></svg>
        </button>
        <figure class="nl-media"><img src="${esc(T.image)}" alt="${esc(T.image_alt)}" width="900" height="1125" loading="lazy"></figure>
        <div class="nl-panel" data-nl-panel></div>
      </div>
    </div>`;

  const overlay = root.querySelector('[data-nl-overlay]');
  const panel = root.querySelector('[data-nl-panel]');

  function formView() {
    return `
      <p class="eyebrow">Good Vibes Va'a</p>
      <h3 class="nl-title" id="nl-title" tabindex="-1">${esc(title)}</h3>
      <p class="nl-text">${esc(text)}</p>
      <form data-nl-form novalidate>
        <div class="nl-field">
          <label for="nl-email">${esc(T.email_label)}</label>
          <input id="nl-email" name="email" type="email" placeholder="${esc(T.email_placeholder)}" autocomplete="email" required>
        </div>
        <label class="nl-check">
          <input type="checkbox" id="nl-consent" required>
          <span>${esc(T.consent_label)}</span>
        </label>
        ${error ? `<p class="nl-err">${esc(error)}</p>` : ''}
        <p class="nl-privacy">${esc(T.privacy_prefix)}<a href="${esc(i18n.privacyHref)}" target="_blank" rel="noopener">${esc(T.privacy_link)}</a></p>
        <div class="nl-hp" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        <button type="submit" class="btn btn--gold nl-submit" ${busy ? 'disabled' : ''}>${busy ? esc(T.sending) : esc(T.cta)}</button>
      </form>`;
  }

  function resultView(resultTitle, resultText) {
    return `
      <span class="nl-ok" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span>
      <h3 class="nl-title" tabindex="-1">${esc(resultTitle)}</h3>
      <p class="nl-text">${esc(resultText)}</p>`;
  }

  function render(focus = false) {
    if (step === 'success') panel.innerHTML = resultView(T.success_title, T.success_text);
    else if (step === 'duplicate') panel.innerHTML = resultView(T.duplicate_title, T.duplicate_text);
    else panel.innerHTML = formView();
    if (focus) panel.querySelector('.nl-title')?.focus({ preventScroll: true });
  }

  function open() {
    if (overlay.hidden === false) return;
    lastFocus = document.activeElement;
    render();
    overlay.hidden = false;
    document.body.classList.add('nl-open');
    requestAnimationFrame(() => panel.querySelector('.nl-title')?.focus({ preventScroll: true }));
  }

  function close(byUser) {
    overlay.hidden = true;
    document.body.classList.remove('nl-open');
    if (byUser && step === 'form') store.snooze();
    lastFocus?.focus?.();
  }

  function focusable() {
    return [...overlay.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])')];
  }

  overlay.addEventListener('keydown', (e) => {
    if (overlay.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); close(true); return; }
    if (e.key === 'Tab') {
      const items = focusable();
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(true); });
  root.addEventListener('click', (e) => { if (e.target.closest('[data-nl-close]')) close(true); });

  root.addEventListener('submit', async (e) => {
    const form = e.target.closest('[data-nl-form]');
    if (!form) return;
    e.preventDefault();
    if (busy) return;

    const email = form.querySelector('#nl-email').value.trim();
    const consent = form.querySelector('#nl-consent').checked;
    const honeypot = form.querySelector('[name="website"]').value;

    error = '';
    if (!EMAIL_RE.test(email)) { error = T.err_email; render(); return; }
    if (!consent) { error = T.err_consent; render(); return; }

    busy = true; render();
    try {
      const res = await fetch(`${(config.apiBase || '').replace(/\/$/, '')}/subscribers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          locale: i18n.locale,
          marketingConsent: true,
          consentText: T.consent_label,
          source: campaign ? 'popup_campaign' : 'popup',
          campaignKey,
          website: honeypot,
          renderedAt,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      busy = false;
      store.markSubscribed();
      step = data.status === 'already_subscribed' ? 'duplicate' : 'success';
      render(true);
      setTimeout(() => close(false), 6000);
    } catch (err) {
      busy = false;
      error = T.err_generic;
      render();
    }
  });

  let triggered = false;
  const trigger = () => {
    if (triggered) return;
    triggered = true;
    open();
  };
  const timer = setTimeout(trigger, TIMER_MS);
  const onExitIntent = (e) => {
    if (e.clientY <= 0) { trigger(); document.removeEventListener('mouseout', onExitIntent); clearTimeout(timer); }
  };
  document.addEventListener('mouseout', onExitIntent);
}
