/* ==========================================================================
   Sistema único de agendamento — calendário + cartões + modal.

   Uma instância por painel (data-modality="experimentar|treinar|particular"
   em build.py), todas com a mesma "casca" visual, comportamento por `flow`
   (ver booking_content.py, MODALITIES):
   - "calendar+pix"     Experimentar: calendário real, cartão por saída,
                         reserva abre modal (participantes → termo → Pix).
   - "calendar+request" Treinar: mesmo calendário/cartão, sem cobrança —
                         modal confirma a vaga direto (sem Pix).
   - "quote"             Particular: sem calendário, um cartão fixo que abre
                         o modal de orçamento (sem vaga, sem pagamento).

   Modos (GVV_CONFIG.bookingMode):
   - "demo": dados ilustrativos gerados aqui, com aviso visível.
   - "live": usa o backend em GVV_CONFIG.apiBase (contrato no README/SETUP).
   - "off" : este módulo não roda; a jornada usa o formulário de WhatsApp.
   ========================================================================== */

const pad = (n) => String(n).padStart(2, '0');
const dateKey = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (str, vars) => str.replace(/\{(\w+)\}/g, (_, k) => vars[k]);

/* ---------------- Adaptadores de dados ---------------- */

function demoApi(modality, defaultSeats) {
  const seeded = (str) => { let h = 0; for (const ch of str) h = (h * 31 + ch.charCodeAt(0)) % 9973; return h; };
  const records = new Map();
  let counter = 1040;

  return {
    demo: true,
    async cardsForDay(key, dow) {
      return modality.activities
        .filter((a) => !a.weekdays || a.weekdays.includes(dow))
        .map((a) => {
          const capacity = a.capacity || defaultSeats;
          const taken = seeded(key + a.id) % (capacity + 1);
          return { ...a, dateKey: key, capacity, available: capacity - taken };
        });
    },
    async book(data) {
      const id = `b${++counter}`;
      const amount = Math.round((data.price * data.people) / 2);
      records.set(id, { status: 'pending' });
      return {
        bookingId: id, code: `GV-${counter}`, amount, expiresAt: Date.now() + 30 * 60 * 1000,
        pix: { copyPaste: `00020126DEMO${counter}5204000053039865802BR5915GOOD VIBES VAA6008SALVADOR`, qrImage: null },
      };
    },
    async status(id) { return records.get(id)?.status || 'expired'; },
    simulatePaid(id) { records.set(id, { status: 'paid' }); },
    async request() {
      const id = `r${++counter}`;
      return { requestId: id, code: `GV-${counter}` };
    },
  };
}

function liveApi(base, modality) {
  const req = async (path, opts = {}) => {
    const res = await fetch(base.replace(/\/$/, '') + path, {
      ...opts, headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  };
  let cache = null;
  async function loadAll() {
    if (cache) return cache;
    cache = new Map();
    await Promise.all(modality.activities.map(async (a) => {
      try {
        const data = await req(`/availability?experience=${encodeURIComponent(a.id)}`);
        cache.set(a.id, data.sessions || []);
      } catch { cache.set(a.id, []); }
    }));
    return cache;
  }
  return {
    demo: false,
    async cardsForDay(key) {
      const all = await loadAll();
      const out = [];
      for (const a of modality.activities) {
        const sessions = (all.get(a.id) || []).filter((s) => s.startsAt.slice(0, 10) === key);
        for (const s of sessions) {
          out.push({
            ...a, dateKey: key, sessionId: s.sessionId, time: s.startsAt.slice(11, 16),
            capacity: s.capacity, available: s.seatsAvailable,
            price: s.priceCents != null ? s.priceCents / 100 : a.price,
          });
        }
      }
      return out;
    },
    async book(data) {
      const res = await req('/reservations/create', {
        method: 'POST',
        body: JSON.stringify({
          sessionId: data.sessionId, participants: data.participants, locale: data.locale,
          contactName: data.name, contactPhone: data.phone, termsAcceptedAt: data.termsAcceptedAt,
        }),
      });
      return {
        bookingId: res.reservationId, code: res.reservationId.slice(0, 8).toUpperCase(),
        amount: res.totalPriceCents / 100, expiresAt: new Date(res.holdExpiresAt).getTime(),
        pix: {
          copyPaste: res.payment.qrCode,
          qrImage: res.payment.qrCodeBase64 ? `data:image/png;base64,${res.payment.qrCodeBase64}` : null,
        },
      };
    },
    async status(id) {
      const res = await req(`/reservations/${encodeURIComponent(id)}/status`);
      return res.status === 'confirmed' ? 'paid' : res.status === 'expired' ? 'expired' : 'pending';
    },
    async request(data) {
      const res = await req('/requests', {
        method: 'POST',
        body: JSON.stringify({
          journey: modality.key, locale: data.locale, contactName: data.name, contactPhone: data.phone,
          sessionId: data.sessionId || undefined, experienceSlug: data.experienceSlug || undefined,
          participantsCount: data.people || 1, notes: data.notes,
        }),
      });
      return { requestId: res.reservationId, code: res.reservationId.slice(0, 8).toUpperCase() };
    },
  };
}

/* QR ilustrativo para o modo demo (não é um código Pix válido) */
function demoQR(seedStr) {
  let s = 0; for (const ch of seedStr) s = (s * 33 + ch.charCodeAt(0)) % 2147483647;
  const rn = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648;
  let r = '';
  for (let y = 0; y < 25; y++) for (let x = 0; x < 25; x++) {
    const inF = (x < 7 && y < 7) || (x > 17 && y < 7) || (x < 7 && y > 17);
    if (inF) {
      const fx = x > 17 ? x - 18 : x, fy = y > 17 ? y - 18 : y;
      if (fx === 0 || fx === 6 || fy === 0 || fy === 6 || (fx > 1 && fx < 5 && fy > 1 && fy < 5)) r += `<rect x="${x}" y="${y}" width="1" height="1"/>`;
    } else if (rn() > 0.52) r += `<rect x="${x}" y="${y}" width="1" height="1"/>`;
  }
  return `<svg viewBox="-1 -1 27 27"><rect x="-1" y="-1" width="27" height="27" fill="#fff"/><g fill="#202B28">${r}</g></svg>`;
}

/* ---------------- Componente ---------------- */

export function initBooking({ config, i18n }) {
  const hosts = document.querySelectorAll('[data-booking]');
  if (!hosts.length || config.bookingMode === 'off') return;
  const modalities = i18n.modalities || [];
  hosts.forEach((host) => {
    const modality = modalities.find((m) => m.key === host.dataset.modality);
    if (modality) initModality(host, modality, config, i18n);
  });
}

function initModality(host, modality, config, i18n) {
  const root = host.querySelector('.bk-root');
  const T = i18n.bk;
  const uid = `bk-${modality.key}`;
  const flow = modality.flow;
  const api = config.bookingMode === 'live' ? liveApi(config.apiBase, modality) : demoApi(modality, config.seats);
  const locale = i18n.locale === 'en' ? 'en-US' : 'pt-BR';
  const money = (v) => v.toLocaleString(locale, { style: 'currency', currency: 'BRL' });
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const DAYS = 14;

  const S = {
    days: Array.from({ length: DAYS }, (_, i) => { const d = new Date(today); d.setDate(d.getDate() + i); return d; }),
    dayIdx: 0, cards: [], cardsLoading: flow !== 'quote',
    modalOpen: false, activity: null, step: 0,
    people: 1, name: '', phone: '', notes: '', terms: false,
    alreadyTrain: null, qType: '', qDate: '', qPeople: '1', qDetails: '',
    errors: {}, busy: false, failed: false, booking: null, payStatus: 'pending',
    timer: null, poll: null, lastFocus: null,
  };

  const dayLabel = (key) => { const [y, m, d] = key.split('-').map(Number); const dt = new Date(y, m - 1, d); return `${T.weekdays[dt.getDay()]}, ${dt.getDate()} ${T.months[dt.getMonth()]}`; };
  const timeLabel = (t) => (i18n.locale === 'en' ? t : t.replace(':', 'h'));
  const phoneDigits = () => S.phone.replace(/\D/g, '');

  function maskPhone(v) {
    const d = v.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 2) return d ? `(${d}` : '';
    if (d.length <= 7) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
    return `(${d.slice(0, 2)}) ${d.slice(2, d.length - 4)}-${d.slice(-4)}`;
  }

  function stopTimers() { clearInterval(S.timer); clearInterval(S.poll); S.timer = S.poll = null; }
  const err = (k) => (S.errors[k] ? `<p class="bk-err" id="${uid}-${k}-err">${esc(S.errors[k])}</p>` : '');
  // Sem botão nenhum (ex.: etapa do Pix, que avança sozinha) o rodapé não é
  // renderizado — uma barra vazia só somaria peso visual ao modal.
  const footer = (nextLabel, disabled = false, showBack = false) => (!nextLabel && !showBack ? '' : `
    <div class="bk-foot">
      ${showBack ? `<button type="button" class="btn btn--ghost" data-bk="back">${esc(T.back)}</button>` : ''}
      ${nextLabel ? `<button type="button" class="btn btn--gold" data-bk="go" ${disabled ? 'aria-disabled="true"' : ''} ${S.busy ? 'disabled' : ''}>${S.busy ? esc(T.sending) : esc(nextLabel)}</button>` : ''}
    </div>`);

  /* O acento de cada jornada vem de MODALITIES (booking_content.py) como
     "ocean" | "forest" | "sand" e resolve para os tokens --accent-* do CSS. */
  const accentVar = `--card-accent: var(--accent-${modality.accent})`;

  /* ----- calendário + cartões ----- */
  function renderCalendar() {
    const chips = S.days.map((d, i) => {
      const top = i === 0 ? T.today : T.weekdays[d.getDay()];
      return `<button type="button" class="bk-day" data-day="${i}" aria-pressed="${S.dayIdx === i}"><small>${esc(top)}</small><b>${d.getDate()}</b><small>${esc(T.months[d.getMonth()])}</small></button>`;
    }).join('');
    return `<div class="bk-cal">
      <p class="bk-label" id="${uid}-day-l">${esc(T.day)}</p>
      <div class="bk-days" role="group" aria-labelledby="${uid}-day-l">${chips}</div>
    </div>`;
  }

  function cardHtml(a) {
    const full = a.available <= 0;
    const capacity = a.capacity || a.available || 1;
    const pct = Math.max(0, Math.min(100, Math.round((a.available / capacity) * 100)));
    const price = a.price != null
      ? `<span class="bk-card-price">${money(a.price)}${flow === 'calendar+pix' ? `<small>${esc(T.per_person)}</small>` : ''}</span>`
      : `<span class="bk-card-price bk-card-price--request">${esc(T.price_on_request)}</span>`;
    const instr = a.instructor
      ? `<p class="bk-card-instr">${a.instructorPhoto ? `<img src="${esc(a.instructorPhoto)}" alt="" width="30" height="30">` : ''}<span>${esc(fmt(T.with_instructor, { name: a.instructor }))}</span></p>`
      : '';
    return `<article class="bk-card${full ? ' bk-card--full' : ''}" style="${accentVar}">
      <div class="bk-card-top">
        <span class="bk-card-time">${esc(timeLabel(a.time))}</span>
        <span class="bk-card-dur">${esc(a.dur)}</span>
      </div>
      <h4>${esc(a.name)}</h4>
      <p class="bk-card-desc">${esc(a.desc)}</p>
      ${instr}
      <div class="bk-card-foot">
        <span class="bk-seats">
          <span class="bk-card-seats">${full ? esc(T.full) : esc(fmt(T.seats_n, { n: a.available }))}</span>
          <span class="bk-meter" aria-hidden="true"><i style="--pct:${pct}%"></i></span>
        </span>
        ${price}
      </div>
      <button type="button" class="btn btn--solid bk-card-cta" data-reserve="${esc(a.id)}" ${full ? 'disabled' : ''}>${esc(T.reserve)}</button>
    </article>`;
  }

  function renderCards() {
    if (S.cardsLoading) return `<p class="bk-wait"><span class="bk-dot" aria-hidden="true"></span>${esc(T.loading)}</p>`;
    if (!S.cards.length) return `<p class="bk-note">${esc(T.no_dates)}</p>`;
    return `<div class="bk-cards">${S.cards.map(cardHtml).join('')}</div>`;
  }

  function renderQuoteCard() {
    return `<div class="bk-cards bk-cards--quote"><article class="bk-card bk-card--quote" style="${accentVar}">
      <h4>${esc(T.quote_title)}</h4>
      <p class="bk-card-desc">${esc(T.quote_lead)}</p>
      <button type="button" class="btn btn--solid bk-card-cta" data-reserve="quote">${esc(T.send_quote)}</button>
    </article></div>`;
  }

  /* ----- modal: participantes/termo/pagamento (Experimentar) ----- */
  function peopleStep() {
    const left = S.activity.available - S.people;
    return `<div class="bk-body">
      <div class="bk-row"><span class="bk-label">${esc(T.people)}</span>
        <div class="bk-stepper"><button type="button" data-bk="minus" aria-label="−1" ${S.people <= 1 ? 'disabled' : ''}>−</button>
          <output aria-live="polite">${S.people}</output>
          <button type="button" data-bk="plus" aria-label="+1" ${S.people >= S.activity.available ? 'disabled' : ''}>+</button></div></div>
      <p class="bk-note">${esc(fmt(T.seats_after, { n: left }))}</p>
      <div class="bk-field"><label for="${uid}-name">${esc(T.name)}</label>
        <input id="${uid}-name" autocomplete="name" value="${esc(S.name)}" ${S.errors.name ? `aria-invalid="true" aria-describedby="${uid}-name-err"` : ''}>${err('name')}</div>
      <div class="bk-field"><label for="${uid}-phone">${esc(T.phone)}</label>
        <input id="${uid}-phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(71) 9 0000-0000" value="${esc(S.phone)}" ${S.errors.phone ? `aria-invalid="true" aria-describedby="${uid}-phone-err"` : ''}>
        <small>${esc(T.phone_hint)}</small>${err('phone')}</div>
    </div>${footer(T.next)}`;
  }

  function termsStep() {
    return `<div class="bk-body">
      <div class="bk-terms" tabindex="0">${T.terms.map((p) => `<p>${esc(p)}</p>`).join('')}<p class="bk-note">${esc(T.terms_note)}</p></div>
      <label class="bk-check"><input type="checkbox" id="${uid}-terms" ${S.terms ? 'checked' : ''}><span>${esc(T.terms_accept)}</span></label>${err('terms')}
    </div>${footer(T.to_pay, false, true)}`;
  }

  function paymentStep() {
    if (S.failed) return `<div class="bk-body"><p class="bk-err">${esc(T.error)}</p></div>${footer(null)}`;
    if (!S.booking) return `<div class="bk-body"><p class="bk-wait">${esc(T.waiting)}</p></div>`;
    const total = S.activity.price * S.people;
    const left = Math.max(0, S.booking.expiresAt - Date.now());
    const mm = pad(Math.floor(left / 60000)), ss = pad(Math.floor((left % 60000) / 1000));
    const expired = S.payStatus === 'expired' || left <= 0;
    const qr = S.booking.pix.qrImage ? `<img src="${esc(S.booking.pix.qrImage)}" alt="QR Code Pix" width="184" height="184">` : `<span role="img" aria-label="${esc(T.pix_alt)}">${demoQR(S.booking.code)}</span>`;
    return `<div class="bk-body">
      <dl class="bk-sum">
        <div><dt>${S.people}× ${esc(S.activity.name)}</dt><dd>${money(total)}</dd></div>
        <div><dt>${esc(T.remaining)}</dt><dd>${money(total - S.booking.amount)}</dd></div>
        <div class="bk-strong"><dt>${esc(T.deposit)}</dt><dd>${money(S.booking.amount)}</dd></div>
      </dl>
      ${expired ? `<div class="bk-pix"><p class="bk-err">${esc(T.expired)}</p><button type="button" class="btn btn--solid" data-bk="regen">${esc(T.regen)}</button></div>` : `
      <div class="bk-pix">${qr}
        <p class="bk-note bk-timer" data-bk-timer>${esc(fmt(T.pix_valid, { t: `${mm}:${ss}` }))}</p>
        <button type="button" class="btn btn--line-dark btn--sm bk-copy" data-bk="copy">${esc(T.copy)}</button>
        <p class="bk-wait" aria-live="polite"><span class="bk-dot" aria-hidden="true"></span>${esc(T.waiting)}</p>
        ${api.demo ? `<button type="button" class="btn btn--gold" data-bk="simpay">${esc(T.sim_pay)}</button>` : ''}
      </div>`}
    </div>${footer(null)}`;
  }

  function doneStepPix() {
    return `<div class="bk-body bk-done">
      <span class="bk-ok" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span>
      <h4 class="bk-title" tabindex="-1">${esc(T.done_title)}</h4>
      <dl class="bk-sum">
        <div><dt>${esc(T.code)}</dt><dd><b>${esc(S.booking.code)}</b></dd></div>
        <div><dt>${esc(T.experience)}</dt><dd>${esc(S.activity.name)}</dd></div>
        <div><dt>${esc(T.when)}</dt><dd>${esc(dayLabel(S.activity.dateKey))} · ${esc(timeLabel(S.activity.time))}</dd></div>
        <div><dt>${esc(T.who)}</dt><dd>${S.people}</dd></div>
        <div><dt>${esc(T.paid)}</dt><dd>${money(S.booking.amount)}</dd></div>
      </dl>
      <p class="bk-note">${esc(T.meeting)}<br>${esc(T.wa_note)}</p>
      <div class="bk-foot bk-foot--stack">
        <button type="button" class="btn btn--solid" data-bk="ics">${esc(T.ics)}</button>
        <button type="button" class="btn btn--ghost" data-bk="close">${esc(T.again)}</button>
      </div>
    </div>`;
  }

  /* ----- modal: Treinar (sem Pix) ----- */
  function requestStep() {
    const instr = S.activity.instructor
      ? `<p class="bk-note">${esc(fmt(T.with_instructor, { name: S.activity.instructor }))}</p>` : '';
    return `<div class="bk-body">
      ${instr}
      <div class="bk-field"><label for="${uid}-name">${esc(T.name)}</label>
        <input id="${uid}-name" autocomplete="name" value="${esc(S.name)}" ${S.errors.name ? 'aria-invalid="true"' : ''}>${err('name')}</div>
      <div class="bk-field"><label for="${uid}-phone">${esc(T.phone)}</label>
        <input id="${uid}-phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(71) 9 0000-0000" value="${esc(S.phone)}" ${S.errors.phone ? 'aria-invalid="true"' : ''}>${err('phone')}</div>
      <fieldset class="bk-field"><legend class="bk-label">${esc(T.already_train_q)}</legend>
        <label class="bk-radio"><input type="radio" name="${uid}-train" value="yes" ${S.alreadyTrain === 'yes' ? 'checked' : ''}><span>${esc(T.already_train_yes)}</span></label>
        <label class="bk-radio"><input type="radio" name="${uid}-train" value="no" ${S.alreadyTrain === 'no' ? 'checked' : ''}><span>${esc(T.already_train_no)}</span></label>
      </fieldset>
      <div class="bk-field"><label for="${uid}-notes">${esc(T.notes_label)}</label><textarea id="${uid}-notes">${esc(S.notes)}</textarea></div>
    </div>${footer(T.send_request)}`;
  }

  function doneStepRequest() {
    if (S.failed) return `<div class="bk-body"><p class="bk-err">${esc(T.error)}</p></div>${footer(null)}`;
    return `<div class="bk-body bk-done">
      <span class="bk-ok" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span>
      <h4 class="bk-title" tabindex="-1">${esc(T.done_title)}</h4>
      <dl class="bk-sum">
        <div><dt>${esc(T.code)}</dt><dd><b>${esc(S.booking.code)}</b></dd></div>
        <div><dt>${esc(T.experience)}</dt><dd>${esc(S.activity.name)}</dd></div>
        <div><dt>${esc(T.when)}</dt><dd>${esc(dayLabel(S.activity.dateKey))} · ${esc(timeLabel(S.activity.time))}</dd></div>
      </dl>
      <p class="bk-note">${esc(T.train_done_note)}</p>
      <div class="bk-foot bk-foot--stack"><button type="button" class="btn btn--ghost" data-bk="close">${esc(T.again)}</button></div>
    </div>`;
  }

  /* ----- modal: Particular (orçamento) ----- */
  function quoteStep() {
    return `<div class="bk-body">
      <div class="bk-field"><label for="${uid}-name">${esc(T.name)}</label>
        <input id="${uid}-name" autocomplete="name" value="${esc(S.name)}" ${S.errors.name ? 'aria-invalid="true"' : ''}>${err('name')}</div>
      <div class="bk-field"><label for="${uid}-phone">${esc(T.phone)}</label>
        <input id="${uid}-phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(71) 9 0000-0000" value="${esc(S.phone)}" ${S.errors.phone ? 'aria-invalid="true"' : ''}>${err('phone')}</div>
      <div class="bk-field"><label for="${uid}-type">${esc(T.type_label)}</label>
        <select id="${uid}-type" ${S.errors.type ? 'aria-invalid="true"' : ''}><option value=""></option>${T.type_options.map(([v, l]) => `<option value="${esc(v)}" ${S.qType === v ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select>${err('type')}</div>
      <div class="bk-field"><label for="${uid}-date">${esc(T.date_label)}</label>
        <input id="${uid}-date" type="date" value="${esc(S.qDate)}" ${S.errors.date ? 'aria-invalid="true"' : ''}>${err('date')}</div>
      <div class="bk-field"><label for="${uid}-people">${esc(T.people_label)}</label>
        <input id="${uid}-people" type="number" min="1" inputmode="numeric" value="${esc(S.qPeople)}"></div>
      <div class="bk-field"><label for="${uid}-details">${esc(T.details_label)}</label>
        <textarea id="${uid}-details">${esc(S.qDetails)}</textarea><small>${esc(T.details_hint)}</small></div>
    </div>${footer(T.send_quote)}`;
  }

  function doneStepQuote() {
    if (S.failed) return `<div class="bk-body"><p class="bk-err">${esc(T.error)}</p></div>${footer(null)}`;
    return `<div class="bk-body bk-done">
      <span class="bk-ok" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span>
      <h4 class="bk-title" tabindex="-1">${esc(T.quote_done_title)}</h4>
      <dl class="bk-sum"><div><dt>${esc(T.code)}</dt><dd><b>${esc(S.booking.code)}</b></dd></div></dl>
      <p class="bk-note">${esc(T.quote_done_note)}</p>
      <div class="bk-foot bk-foot--stack"><button type="button" class="btn btn--ghost" data-bk="close">${esc(T.again)}</button></div>
    </div>`;
  }

  /* ----- modal: casca comum ----- */
  function modalTitle() {
    if (flow === 'calendar+pix') return S.activity.name;
    if (flow === 'calendar+request') return T.request_title;
    return T.quote_title;
  }
  /* Olho do modal: dia e horário escolhidos (dado que a pessoa acabou de
     selecionar), para o corpo não repetir essa linha. */
  function modalKicker() {
    if (flow === 'quote' || !S.activity || !S.activity.dateKey) return '';
    return `${dayLabel(S.activity.dateKey)} · ${timeLabel(S.activity.time)}`;
  }
  /* Trilha de etapas — só o fluxo com pagamento tem mais de um passo de
     preenchimento. Os rótulos vêm de T.steps (booking_content.py): os três
     últimos são Participantes / Termo / Pagamento. */
  function modalSteps() {
    if (flow !== 'calendar+pix') return '';
    const labels = (T.steps || []).slice(-3);
    if (labels.length < 3) return '';
    const items = labels.map((label, i) => {
      const state = S.step > i ? 'done' : S.step === i ? 'on' : 'next';
      return `<li data-state="${state}"${state === 'on' ? ' aria-current="step"' : ''}><b>${String(i + 1).padStart(2, '0')}</b>${esc(label)}</li>`;
    }).join('');
    return `<ol class="bk-steps">${items}</ol>`;
  }
  function modalBody() {
    if (flow === 'calendar+pix') return [peopleStep, termsStep, paymentStep, doneStepPix][S.step]();
    if (flow === 'calendar+request') return [requestStep, doneStepRequest][S.step]();
    return [quoteStep, doneStepQuote][S.step]();
  }
  function renderModal() {
    const kicker = modalKicker();
    return `<div class="bk-overlay" data-bk-overlay>
      <div class="bk-modal" role="dialog" aria-modal="true" aria-labelledby="${uid}-modal-title">
        <div class="bk-modal-head">
          <div>
            ${kicker ? `<p class="eyebrow">${esc(kicker)}</p>` : ''}
            <h4 id="${uid}-modal-title" class="bk-title" tabindex="-1">${esc(modalTitle())}</h4>
          </div>
          <button type="button" class="bk-modal-close" data-bk="close" aria-label="${esc(T.modal_close)}">
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 5l14 14M19 5L5 19"/></svg>
          </button>
        </div>
        ${modalSteps()}
        ${modalBody()}
      </div>
    </div>`;
  }

  function render(focus = false) {
    const body = flow === 'quote' ? renderQuoteCard() : `${renderCalendar()}${renderCards()}`;
    root.innerHTML = body + (S.modalOpen ? renderModal() : '');
    if (S.modalOpen && focus) root.querySelector('.bk-modal-head .bk-title, .bk-done .bk-title')?.focus({ preventScroll: true });
  }

  function focusableInModal() {
    const modal = root.querySelector('.bk-modal');
    if (!modal) return [];
    return [...modal.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')];
  }

  async function selectDay(i) {
    S.dayIdx = i; S.cards = []; S.cardsLoading = true;
    render();
    const d = S.days[i];
    S.cards = await api.cardsForDay(dateKey(d), d.getDay());
    S.cardsLoading = false;
    render();
  }

  function openModal(activity) {
    S.activity = activity;
    Object.assign(S, {
      modalOpen: true, step: 0, people: 1, name: '', phone: '', notes: '', terms: false,
      alreadyTrain: null, qType: '', qDate: '', qPeople: '1', qDetails: '',
      errors: {}, busy: false, failed: false, booking: null, payStatus: 'pending',
    });
    S.lastFocus = document.activeElement;
    document.body.classList.add('bk-modal-open');
    render(true);
  }

  function closeModal() {
    stopTimers();
    S.modalOpen = false;
    document.body.classList.remove('bk-modal-open');
    render();
    S.lastFocus?.focus?.();
  }

  function validateContact() {
    S.errors = {};
    if (!S.name.trim()) S.errors.name = T.err_name;
    if (phoneDigits().length < 10) S.errors.phone = T.err_phone;
    return !Object.keys(S.errors).length;
  }
  function validateQuoteFields() {
    S.errors = {};
    if (!S.name.trim()) S.errors.name = T.err_name;
    if (phoneDigits().length < 10) S.errors.phone = T.err_phone;
    if (!S.qType) S.errors.type = i18n.required;
    if (!S.qDate) S.errors.date = i18n.required;
    return !Object.keys(S.errors).length;
  }

  async function startPayment() {
    stopTimers(); S.failed = false; S.booking = null; S.payStatus = 'pending';
    try {
      S.booking = await api.book({
        sessionId: S.activity.sessionId, participants: Array.from({ length: S.people }, () => ({ fullName: S.name.trim(), isMinor: false, birthDate: null })),
        people: S.people, price: S.activity.price,
        name: S.name.trim(), phone: phoneDigits(), locale: i18n.locale, termsAcceptedAt: new Date().toISOString(),
      });
    } catch (e) { S.failed = true; return; }
    S.timer = setInterval(() => {
      const el = root.querySelector('[data-bk-timer]');
      const left = S.booking.expiresAt - Date.now();
      if (left <= 0) { S.payStatus = 'expired'; stopTimers(); render(); return; }
      if (el) el.textContent = fmt(T.pix_valid, { t: `${pad(Math.floor(left / 60000))}:${pad(Math.floor((left % 60000) / 1000))}` });
    }, 1000);
    S.poll = setInterval(async () => {
      try {
        const st = await api.status(S.booking.bookingId);
        if (st === 'paid') { stopTimers(); S.step = 3; render(true); }
        if (st === 'expired') { S.payStatus = 'expired'; stopTimers(); render(); }
      } catch (e) { /* tenta de novo no próximo ciclo */ }
    }, api.demo ? 1000 : 4000);
  }

  async function submitRequest() {
    S.busy = true; render();
    try {
      const note = `${T.already_train_q} ${S.alreadyTrain === 'yes' ? T.already_train_yes : S.alreadyTrain === 'no' ? T.already_train_no : '—'}${S.notes ? '. ' + S.notes : ''}`;
      S.booking = await api.request({
        sessionId: S.activity.sessionId || null, people: 1,
        name: S.name.trim(), phone: phoneDigits(), locale: i18n.locale, notes: note,
      });
      S.step = 1;
    } catch (e) { S.failed = true; }
    S.busy = false; render(true);
  }

  async function submitQuote() {
    S.busy = true; render();
    try {
      const note = `${T.type_label}: ${S.qType}. ${T.date_label}: ${S.qDate}. ${T.details_label}: ${S.qDetails || '—'}`;
      S.booking = await api.request({
        sessionId: null, experienceSlug: 'particular', people: Number(S.qPeople) || 1,
        name: S.name.trim(), phone: phoneDigits(), locale: i18n.locale, notes: note,
      });
      S.step = 1;
    } catch (e) { S.failed = true; }
    S.busy = false; render(true);
  }

  function downloadICS() {
    const [y, m, d] = S.activity.dateKey.split('-').map(Number);
    const [h, mi] = S.activity.time.split(':').map(Number);
    const start = new Date(y, m - 1, d, h, mi);
    const end = new Date(start.getTime() + 90 * 60000);
    const f = (x) => `${x.getFullYear()}${pad(x.getMonth() + 1)}${pad(x.getDate())}T${pad(x.getHours())}${pad(x.getMinutes())}00`;
    const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Good Vibes Vaa//Reserva//PT', 'BEGIN:VEVENT',
      `UID:${S.booking.code}@goodvibesvaa`, `DTSTART:${f(start)}`, `DTEND:${f(end)}`,
      `SUMMARY:${T.ics_title} · ${S.activity.name}`, 'LOCATION:Praia da Preguiça\\, Salvador - BA',
      `DESCRIPTION:${T.code} ${S.booking.code}. ${T.meeting}`, 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: `${S.booking.code}.ics` });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  /* ----- eventos ----- */
  root.addEventListener('change', (e) => {
    if (e.target.id === `${uid}-terms`) { S.terms = e.target.checked; S.errors.terms = ''; render(); return; }
    if (e.target.name === `${uid}-train`) { S.alreadyTrain = e.target.value; return; }
    if (e.target.id === `${uid}-type`) { S.qType = e.target.value; return; }
  });
  root.addEventListener('input', (e) => {
    if (e.target.id === `${uid}-name`) S.name = e.target.value;
    if (e.target.id === `${uid}-phone`) { const m = maskPhone(e.target.value); e.target.value = m; S.phone = m; }
    if (e.target.id === `${uid}-notes`) S.notes = e.target.value;
    if (e.target.id === `${uid}-date`) S.qDate = e.target.value;
    if (e.target.id === `${uid}-people`) S.qPeople = e.target.value;
    if (e.target.id === `${uid}-details`) S.qDetails = e.target.value;
  });
  root.addEventListener('keydown', (e) => {
    if (!S.modalOpen) return;
    if (e.key === 'Escape') { e.preventDefault(); closeModal(); return; }
    if (e.key === 'Tab') {
      const items = focusableInModal();
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  root.addEventListener('click', async (e) => {
    const overlay = e.target.closest('[data-bk-overlay]');
    if (overlay === e.target) { closeModal(); return; }

    const day = e.target.closest('[data-day]');
    if (day) { await selectDay(+day.dataset.day); root.querySelector(`[data-day="${day.dataset.day}"]`)?.focus(); return; }

    const reserve = e.target.closest('[data-reserve]');
    if (reserve && !reserve.disabled) {
      const id = reserve.dataset.reserve;
      openModal(id === 'quote' ? {} : S.cards.find((c) => c.id === id));
      return;
    }

    const b = e.target.closest('[data-bk]');
    if (!b) return;
    const act = b.dataset.bk;
    if (act === 'close') { closeModal(); return; }
    if (act === 'back') { S.step = Math.max(0, S.step - 1); render(true); return; }
    if (act === 'go') {
      if (b.getAttribute('aria-disabled') === 'true' || S.busy) return;
      if (flow === 'calendar+pix') {
        if (S.step === 0) { if (!validateContact()) { render(); return; } S.step = 1; render(true); return; }
        if (S.step === 1) { if (!S.terms) { S.errors = { terms: T.err_terms }; render(); return; } S.step = 2; render(true); await startPayment(); render(); return; }
      }
      if (flow === 'calendar+request' && S.step === 0) { if (!validateContact()) { render(); return; } await submitRequest(); return; }
      if (flow === 'quote' && S.step === 0) { if (!validateQuoteFields()) { render(); return; } await submitQuote(); return; }
    }
    if (act === 'plus' && S.people < S.activity.available) { S.people++; render(); root.querySelector('[data-bk="plus"]')?.focus(); }
    if (act === 'minus' && S.people > 1) { S.people--; render(); root.querySelector('[data-bk="minus"]')?.focus(); }
    if (act === 'copy') {
      try { await navigator.clipboard.writeText(S.booking.pix.copyPaste); } catch (err) { /* sem permissão de área de transferência */ }
      b.textContent = T.copied; setTimeout(() => { b.textContent = T.copy; }, 2000);
    }
    if (act === 'simpay' && api.demo) { api.simulatePaid(S.booking.bookingId); }
    if (act === 'regen') { await startPayment(); render(true); }
    if (act === 'ics') downloadICS();
  });

  if (flow === 'quote') render();
  else selectDay(0);
}
