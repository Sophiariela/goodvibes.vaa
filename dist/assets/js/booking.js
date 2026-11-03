/* ==========================================================================
   Reserva dentro do site (aba "Quero experimentar")

   Modos (GVV_CONFIG.bookingMode):
   - "demo": dados ilustrativos gerados aqui, com aviso visível. Só para apresentação.
   - "live": usa o backend em GVV_CONFIG.apiBase (contrato descrito no README).
   - "off" : este módulo não roda; a aba usa o formulário de WhatsApp.
   ========================================================================== */

const pad = (n) => String(n).padStart(2, '0');
const dateKey = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const fromKey = (k) => { const [y, m, d] = k.split('-').map(Number); return new Date(y, m - 1, d); };
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (str, vars) => str.replace(/\{(\w+)\}/g, (_, k) => vars[k]);

/* ---------------- Adaptadores de dados ---------------- */

function demoApi(experiences, seats) {
  const bookings = new Map();
  let counter = 1040;
  const seeded = (str) => { let h = 0; for (const ch of str) h = (h * 31 + ch.charCodeAt(0)) % 9973; return h; };

  return {
    demo: true,
    async experiences() { return experiences; },
    async departures(expId, fromKeyStr, days) {
      const exp = experiences.find((e) => e.id === expId);
      const start = fromKey(fromKeyStr);
      const out = [];
      for (let i = 0; i < days; i++) {
        const d = new Date(start); d.setDate(d.getDate() + i);
        const key = dateKey(d);
        const taken = seeded(key + expId) % (seats + 1);
        out.push({ id: `${key}-${expId}`, date: key, time: exp.time, capacity: seats, available: seats - taken, price: exp.price });
      }
      return out;
    },
    async hold(departureId, people) {
      return { holdId: `h-${departureId}-${people}`, expiresAt: Date.now() + 30 * 60 * 1000 };
    },
    async book(data) {
      const id = `b${++counter}`;
      const amount = Math.round((data.price * data.people) / 2);
      bookings.set(id, { status: 'pending' });
      return { bookingId: id, code: `GV-${counter}`, amount, expiresAt: Date.now() + 30 * 60 * 1000,
               pix: { copyPaste: `00020126DEMO${counter}5204000053039865802BR5915GOOD VIBES VAA6008SALVADOR`, qrImage: null } };
    },
    async status(id) { return bookings.get(id)?.status || 'expired'; },
    simulatePaid(id) { bookings.set(id, { status: 'paid' }); },
  };
}

function liveApi(base) {
  const req = async (path, opts = {}) => {
    const res = await fetch(base.replace(/\/$/, '') + path, {
      ...opts, headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  };
  return {
    demo: false,
    experiences: () => req('/experiences'),
    departures: (expId, from, days) => req(`/departures?experience=${encodeURIComponent(expId)}&from=${from}&days=${days}`),
    hold: (departureId, people) => req('/holds', { method: 'POST', body: JSON.stringify({ departureId, people }) }),
    book: (data) => req('/bookings', { method: 'POST', body: JSON.stringify(data) }),
    status: async (id) => (await req(`/bookings/${encodeURIComponent(id)}/status`)).status,
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
  const host = document.querySelector('[data-booking]');
  if (!host || config.bookingMode === 'off') return;
  const root = host.querySelector('.bk-root');
  const T = i18n.bk;
  const api = config.bookingMode === 'live' ? liveApi(config.apiBase) : demoApi(i18n.demoExperiences, config.seats);
  const locale = i18n.locale === 'en' ? 'en-US' : 'pt-BR';
  const money = (v) => v.toLocaleString(locale, { style: 'currency', currency: 'BRL' });
  const DAYS = 14;
  const TOTAL = T.steps.length;

  const S = {
    step: 0, exps: [], exp: null, deps: [], dayIdx: 0, dep: null,
    people: 1, name: '', phone: '', terms: false, errors: {},
    hold: null, booking: null, payStatus: 'pending', timer: null, poll: null, busy: false, failed: false,
  };

  const today = new Date(); today.setHours(0, 0, 0, 0);
  const dayDate = (i) => { const d = new Date(today); d.setDate(d.getDate() + i); return d; };
  const dayLabel = (key) => { const d = fromKey(key); return `${T.weekdays[d.getDay()]}, ${d.getDate()} ${T.months[d.getMonth()]}`; };
  const timeLabel = (t) => (i18n.locale === 'en' ? t : t.replace(':', 'h'));
  const phoneDigits = () => S.phone.replace(/\D/g, '');

  function maskPhone(v) {
    const d = v.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 2) return d ? `(${d}` : '';
    if (d.length <= 7) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
    return `(${d.slice(0, 2)}) ${d.slice(2, d.length - 4)}-${d.slice(-4)}`;
  }

  function stopTimers() { clearInterval(S.timer); clearInterval(S.poll); S.timer = S.poll = null; }

  /* ----- partes da interface ----- */
  const header = () => {
    if (S.step >= TOTAL) return '';
    const bars = T.steps.map((label, i) => `<li class="${i < S.step ? 'done' : i === S.step ? 'on' : ''}"><span class="sr-only">${esc(label)}</span></li>`).join('');
    return `<div class="bk-steps"><p class="bk-count">${esc(fmt(T.step, { n: S.step + 1, t: TOTAL }))}</p>
      <h4 class="bk-title" tabindex="-1">${esc(T.steps[S.step])}</h4><ol class="bk-bar" aria-hidden="true">${bars}</ol></div>`;
  };
  const footer = (nextLabel, disabled = false, showBack = true) => `
    <div class="bk-foot">
      ${showBack && S.step > 0 ? `<button type="button" class="btn btn--ghost" data-bk="back">${esc(T.back)}</button>` : '<span></span>'}
      ${nextLabel ? `<button type="button" class="btn btn--dark" data-bk="next" ${disabled ? 'aria-disabled="true"' : ''}>${esc(nextLabel)}</button>` : ''}
    </div>`;
  const err = (k) => (S.errors[k] ? `<p class="bk-err" id="bk-${k}-err">${esc(S.errors[k])}</p>` : '');

  function viewExperience() {
    const items = S.exps.map((x) => `
      <label class="bk-opt">
        <input type="radio" name="bk-exp" value="${esc(x.id)}" ${S.exp?.id === x.id ? 'checked' : ''}>
        <span class="bk-opt-main"><strong>${esc(x.name)}</strong><small>${esc(x.desc)}</small>
          <small class="bk-meta">${esc(fmt(T.departure, { t: timeLabel(x.time) }))} · ${esc(x.dur)}</small></span>
        <span class="bk-price">${money(x.price)}<small>${esc(T.per_person)}</small></span>
      </label>`).join('');
    return `${header()}<fieldset class="bk-body"><legend class="sr-only">${esc(T.steps[0])}</legend><div class="bk-opts">${items}</div></fieldset>${footer(T.next, !S.exp)}`;
  }

  function viewDate() {
    const chips = S.deps.map((d, i) => {
      const dt = fromKey(d.date);
      const top = i === 0 ? T.today : T.weekdays[dt.getDay()];
      return `<button type="button" class="bk-day" data-day="${i}" aria-pressed="${S.dayIdx === i}"><small>${esc(top)}</small><b>${dt.getDate()}</b><small>${esc(T.months[dt.getMonth()])}</small></button>`;
    }).join('');
    const d = S.deps[S.dayIdx];
    let slot = '';
    if (d) {
      const full = d.available <= 0;
      const seats = Array.from({ length: d.capacity }, (_, i) => `<i class="${i < d.capacity - d.available ? 't' : ''}"></i>`).join('');
      slot = `<button type="button" class="bk-slot" data-dep="${esc(d.id)}" aria-pressed="${S.dep?.id === d.id}" ${full ? 'disabled' : ''}>
        <span><b>${esc(timeLabel(d.time))}</b><small>${full ? esc(T.full) : esc(fmt(T.free, { n: d.available, c: d.capacity }))}</small></span>
        <span class="bk-seats" aria-hidden="true">${seats}</span></button>`;
    }
    return `${header()}<div class="bk-body">
      <p class="bk-label" id="bk-day-l">${esc(T.day)}</p>
      <div class="bk-days" role="group" aria-labelledby="bk-day-l">${chips}</div>
      <p class="bk-label">${esc(T.slots)} · ${esc(S.exp.name)}</p>${slot}${err('slot')}
    </div>${footer(T.next, !S.dep)}`;
  }

  function viewPeople() {
    const left = S.dep.available - S.people;
    return `${header()}<div class="bk-body">
      <div class="bk-row">
        <span class="bk-label">${esc(T.people)}</span>
        <div class="bk-stepper"><button type="button" data-bk="minus" aria-label="−1" ${S.people <= 1 ? 'disabled' : ''}>−</button>
          <output aria-live="polite">${S.people}</output>
          <button type="button" data-bk="plus" aria-label="+1" ${S.people >= S.dep.available ? 'disabled' : ''}>+</button></div>
      </div>
      <p class="bk-note">${esc(fmt(T.seats_after, { n: left }))}</p>
      <div class="bk-field"><label for="bk-name">${esc(T.name)}</label>
        <input id="bk-name" autocomplete="name" value="${esc(S.name)}" ${S.errors.name ? 'aria-invalid="true" aria-describedby="bk-name-err"' : ''}>${err('name')}</div>
      <div class="bk-field"><label for="bk-phone">${esc(T.phone)}</label>
        <input id="bk-phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(71) 9 0000-0000" value="${esc(S.phone)}" aria-describedby="bk-phone-hint${S.errors.phone ? ' bk-phone-err' : ''}" ${S.errors.phone ? 'aria-invalid="true"' : ''}>
        <small id="bk-phone-hint">${esc(T.phone_hint)}</small>${err('phone')}</div>
    </div>${footer(T.next)}`;
  }

  function viewTerms() {
    return `${header()}<div class="bk-body">
      <div class="bk-terms" tabindex="0" aria-label="${esc(T.steps[3])}">${T.terms.map((p) => `<p>${esc(p)}</p>`).join('')}<p class="bk-note">${esc(T.terms_note)}</p></div>
      <label class="bk-check"><input type="checkbox" id="bk-terms" ${S.terms ? 'checked' : ''} ${S.errors.terms ? 'aria-invalid="true" aria-describedby="bk-terms-err"' : ''}><span>${esc(T.terms_accept)}</span></label>${err('terms')}
    </div>${footer(T.to_pay)}`;
  }

  function viewPayment() {
    const total = S.dep.price * S.people;
    if (S.failed) return `${header()}<div class="bk-body"><p class="bk-err">${esc(T.error)}</p></div>${footer(null)}`;
    if (!S.booking) return `${header()}<div class="bk-body"><p class="bk-wait">${esc(T.waiting)}</p></div>`;
    const left = Math.max(0, S.booking.expiresAt - Date.now());
    const mm = pad(Math.floor(left / 60000)), ss = pad(Math.floor((left % 60000) / 1000));
    const expired = S.payStatus === 'expired' || left <= 0;
    const qr = S.booking.pix.qrImage ? `<img src="${esc(S.booking.pix.qrImage)}" alt="QR Code Pix" width="180" height="180">` : `<span role="img" aria-label="${esc(T.pix_alt)}">${demoQR(S.booking.code)}</span>`;
    return `${header()}<div class="bk-body">
      <dl class="bk-sum">
        <div><dt>${S.people}× ${esc(S.exp.name)}</dt><dd>${money(total)}</dd></div>
        <div><dt>${esc(T.remaining)}</dt><dd>${money(total - S.booking.amount)}</dd></div>
        <div class="bk-strong"><dt>${esc(T.deposit)}</dt><dd>${money(S.booking.amount)}</dd></div>
      </dl>
      ${expired ? `<div class="bk-pix"><p class="bk-err">${esc(T.expired)}</p><button type="button" class="btn btn--dark" data-bk="regen">${esc(T.regen)}</button></div>` : `
      <div class="bk-pix">${qr}
        <p class="bk-note" data-bk-timer>${esc(fmt(T.pix_valid, { t: `${mm}:${ss}` }))}</p>
        <button type="button" class="btn btn--ghost bk-copy" data-bk="copy">${esc(T.copy)}</button>
        <p class="bk-wait" aria-live="polite"><span class="bk-dot" aria-hidden="true"></span>${esc(T.waiting)}</p>
        ${api.demo ? `<button type="button" class="btn btn--dark" data-bk="simpay">${esc(T.sim_pay)}</button>` : ''}
      </div>`}
    </div>${footer(null)}`;
  }

  function viewDone() {
    return `<div class="bk-body bk-done">
      <span class="bk-ok" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span>
      <h4 class="bk-title" tabindex="-1">${esc(T.done_title)}</h4>
      <dl class="bk-sum">
        <div><dt>${esc(T.code)}</dt><dd><b>${esc(S.booking.code)}</b></dd></div>
        <div><dt>${esc(T.experience)}</dt><dd>${esc(S.exp.name)}</dd></div>
        <div><dt>${esc(T.when)}</dt><dd>${esc(dayLabel(S.dep.date))} · ${esc(timeLabel(S.dep.time))}</dd></div>
        <div><dt>${esc(T.who)}</dt><dd>${S.people}</dd></div>
        <div><dt>${esc(T.paid)}</dt><dd>${money(S.booking.amount)}</dd></div>
      </dl>
      <p class="bk-note">${esc(T.meeting)}<br>${esc(T.wa_note)}</p>
      <div class="bk-foot bk-foot--stack">
        <button type="button" class="btn btn--dark" data-bk="ics">${esc(T.ics)}</button>
        <button type="button" class="btn btn--ghost" data-bk="again">${esc(T.again)}</button>
      </div>
    </div>`;
  }

  function render(focus = false) {
    const views = [viewExperience, viewDate, viewPeople, viewTerms, viewPayment, viewDone];
    root.innerHTML = views[S.step]();
    if (focus) root.querySelector('.bk-title')?.focus({ preventScroll: false });
  }

  /* ----- navegação ----- */
  async function go(step) {
    S.errors = {};
    S.step = step;
    if (step === 1) {
      S.deps = await api.departures(S.exp.id, dateKey(today), DAYS);
      if (!S.deps[S.dayIdx]) S.dayIdx = 0;
    }
    if (step === 4) await startPayment();
    render(true);
    host.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function validatePeople() {
    S.errors = {};
    if (!S.name.trim()) S.errors.name = T.err_name;
    if (phoneDigits().length < 10) S.errors.phone = T.err_phone;
    return !Object.keys(S.errors).length;
  }

  async function startPayment() {
    stopTimers(); S.failed = false; S.booking = null; S.payStatus = 'pending';
    try {
      S.hold = await api.hold(S.dep.id, S.people);
      S.booking = await api.book({
        holdId: S.hold.holdId, departureId: S.dep.id, experienceId: S.exp.id, people: S.people, price: S.dep.price,
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
        if (st === 'paid') { stopTimers(); S.step = TOTAL; render(true); }
        if (st === 'expired') { S.payStatus = 'expired'; stopTimers(); render(); }
      } catch (e) { /* tenta de novo no próximo ciclo */ }
    }, api.demo ? 1000 : 4000);
  }

  function downloadICS() {
    const d = fromKey(S.dep.date);
    const [h, m] = S.dep.time.split(':').map(Number);
    const start = new Date(d.getFullYear(), d.getMonth(), d.getDate(), h, m);
    const end = new Date(start.getTime() + 90 * 60000);
    const f = (x) => `${x.getFullYear()}${pad(x.getMonth() + 1)}${pad(x.getDate())}T${pad(x.getHours())}${pad(x.getMinutes())}00`;
    const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Good Vibes Vaa//Reserva//PT', 'BEGIN:VEVENT',
      `UID:${S.booking.code}@goodvibesvaa`, `DTSTART:${f(start)}`, `DTEND:${f(end)}`,
      `SUMMARY:${T.ics_title} · ${S.exp.name}`, 'LOCATION:Praia da Preguiça\\, Salvador - BA',
      `DESCRIPTION:${T.code} ${S.booking.code}. ${T.meeting}`, 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: `${S.booking.code}.ics` });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  /* ----- eventos ----- */
  root.addEventListener('change', (e) => {
    if (e.target.name === 'bk-exp') { S.exp = S.exps.find((x) => x.id === e.target.value); S.dep = null; render(); root.querySelector(`input[value="${CSS.escape(S.exp.id)}"]`)?.focus(); }
    if (e.target.id === 'bk-terms') { S.terms = e.target.checked; S.errors.terms = ''; }
  });
  root.addEventListener('input', (e) => {
    if (e.target.id === 'bk-name') S.name = e.target.value;
    if (e.target.id === 'bk-phone') { const m = maskPhone(e.target.value); e.target.value = m; S.phone = m; }
  });
  root.addEventListener('click', async (e) => {
    const day = e.target.closest('[data-day]');
    if (day) { S.dayIdx = +day.dataset.day; S.dep = null; render(); root.querySelector(`[data-day="${S.dayIdx}"]`)?.focus(); return; }
    const dep = e.target.closest('[data-dep]');
    if (dep && !dep.disabled) { S.dep = S.deps.find((x) => x.id === dep.dataset.dep); S.people = Math.min(S.people, S.dep.available); render(); root.querySelector('[data-dep]')?.focus(); return; }
    const b = e.target.closest('[data-bk]'); if (!b) return;
    const act = b.dataset.bk;
    if (act === 'back') { stopTimers(); go(S.step - 1); }
    if (act === 'next') {
      if (b.getAttribute('aria-disabled') === 'true') {
        if (S.step === 1) { S.errors = { slot: T.pick_slot }; render(); }
        return;
      }
      if (S.step === 2 && !validatePeople()) { render(); root.querySelector('[aria-invalid="true"]')?.focus(); return; }
      if (S.step === 3 && !S.terms) { S.errors = { terms: T.err_terms }; render(); root.querySelector('#bk-terms')?.focus(); return; }
      go(S.step + 1);
    }
    if (act === 'plus' && S.people < S.dep.available) { S.people++; render(); root.querySelector('[data-bk="plus"]')?.focus(); }
    if (act === 'minus' && S.people > 1) { S.people--; render(); root.querySelector('[data-bk="minus"]')?.focus(); }
    if (act === 'copy') {
      try { await navigator.clipboard.writeText(S.booking.pix.copyPaste); } catch (err) { /* sem permissão de área de transferência */ }
      b.textContent = T.copied; setTimeout(() => { b.textContent = T.copy; }, 2000);
    }
    if (act === 'simpay' && api.demo) api.simulatePaid(S.booking.bookingId);
    if (act === 'regen') { await startPayment(); render(true); }
    if (act === 'ics') downloadICS();
    if (act === 'again') {
      stopTimers();
      Object.assign(S, { step: 0, exp: null, dep: null, dayIdx: 0, people: 1, terms: false, booking: null, errors: {} });
      render(true);
    }
  });

  (async () => {
    try { S.exps = await api.experiences(); render(); }
    catch (e) { root.innerHTML = `<p class="bk-err">${esc(T.error)}</p>`; }
  })();
}
