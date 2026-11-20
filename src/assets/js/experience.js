/* ==========================================================================
   Good Vibes Va'a — /agendar/: descoberta por carrossel e fluxo por jornada

   Uma experiência por vez. O visitante navega o carrossel (setas, swipe,
   teclado, indicadores), escolhe uma jornada e só então vê os campos
   daquela jornada — quem vai treinar nunca lê texto de passeio turístico.

   Estado e envio
   --------------
   O <form data-journey> já existe no HTML desde o carregamento: é ele que
   o site.js vincula em initForms(). Este módulo nunca cria um formulário
   novo — ele move o que já existe para dentro do passo certo e escreve os
   valores nos campos ocultos ([data-xp-field]), com o rótulo que vai sair
   na mensagem. Assim validação, collect() e o envio pelo WhatsApp seguem
   sendo exatamente os de sempre.

   O que a pessoa preencheu fica em sessionStorage por jornada: voltar ao
   carrossel e escolher outra experiência não apaga o que já foi dito, e
   recarregar a página retoma de onde parou.

   Todo texto vem de I18N.xp (resolve_xp em build.py) — nada escrito aqui.
   ========================================================================== */

import { initDatePicker } from './datepicker.js';

const KEY = 'gvv-xp';

const load = () => {
  try { return JSON.parse(sessionStorage.getItem(KEY) || '{}'); } catch (e) { return {}; }
};
const save = (state) => {
  try { sessionStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* sem storage */ }
};

export function initExperience(I18N) {
  const root = document.querySelector('[data-xp]');
  const XP = I18N.xp;
  if (!root || !XP) return;

  const track = root.querySelector('[data-xp-track]');
  const slides = [...root.querySelectorAll('[data-xp-slide]')];
  const controls = root.querySelector('[data-xp-controls]');
  const dots = [...root.querySelectorAll('[data-xp-dot]')];
  const stage = root.querySelector('[data-xp-stage]');
  const flow = root.querySelector('[data-xp-flow]');
  const stepsEl = root.querySelector('[data-xp-steps]');
  const panel = root.querySelector('[data-xp-panel]');
  const form = root.querySelector('[data-xp-form]');
  const contact = root.querySelector('[data-xp-contact]');
  const hint = root.querySelector('[data-xp-hint]');
  if (!track || !slides.length || !form) return;

  const saved = load();
  const S = {
    index: 0,
    journey: null,
    step: 0,
    answers: saved.answers || {},
  };

  const keyOf = (i) => slides[i].dataset.xpSlide;
  const answers = (j) => (S.answers[j] = S.answers[j] || {});

  /* ---------- Carrossel ---------- */
  // Com JS os controles aparecem; sem ele, os três artigos ficam em
  // sequência e cada "Explorar" é um link normal para a home.
  controls.hidden = false;
  root.classList.add('is-js');

  function renderCarousel() {
    track.style.transform = `translateX(-${S.index * 100}%)`;
    slides.forEach((s, i) => {
      const on = i === S.index;
      s.classList.toggle('is-active', on);
      // Fora de tela não deve receber foco nem ser lido como conteúdo atual.
      s.toggleAttribute('inert', !on);
      s.setAttribute('aria-hidden', String(!on));
    });
    dots.forEach((d, i) => {
      d.classList.toggle('is-on', i === S.index);
      d.setAttribute('aria-selected', String(i === S.index));
    });
  }

  const go = (i) => {
    S.index = (i + slides.length) % slides.length;
    renderCarousel();
  };

  root.querySelector('[data-xp-prev]').addEventListener('click', () => go(S.index - 1));
  root.querySelector('[data-xp-next]').addEventListener('click', () => go(S.index + 1));
  dots.forEach((d, i) => d.addEventListener('click', () => go(i)));

  stage.addEventListener('keydown', (ev) => {
    if (ev.key === 'ArrowLeft') { ev.preventDefault(); go(S.index - 1); }
    if (ev.key === 'ArrowRight') { ev.preventDefault(); go(S.index + 1); }
  });

  // Swipe: só horizontal e só se o gesto for claramente lateral, para não
  // sequestrar a rolagem vertical da página no celular.
  let x0 = null; let y0 = null;
  stage.addEventListener('pointerdown', (ev) => { x0 = ev.clientX; y0 = ev.clientY; });
  stage.addEventListener('pointerup', (ev) => {
    if (x0 === null) return;
    const dx = ev.clientX - x0;
    const dy = ev.clientY - y0;
    x0 = null;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy) * 1.5) go(S.index + (dx < 0 ? 1 : -1));
  });

  /* ---------- Campos ocultos: o que será enviado ---------- */
  const fieldEl = (name) => form.querySelector(`[data-xp-field="${name}"]`);

  function setField(name, label, value) {
    const el = fieldEl(name);
    if (!el) return;
    el.value = value || '';
    // Sem rótulo o collect() ainda leria o campo; com valor vazio ele pula.
    el.dataset.label = value ? label : '';
  }

  function clearFields() {
    form.querySelectorAll('[data-xp-field]').forEach((el) => { el.value = ''; el.dataset.label = ''; });
  }

  // Espelha as respostas da jornada atual nos campos ocultos do form.
  function syncFields() {
    clearFields();
    const j = S.journey;
    if (!j) return;
    const card = XP.cards.find((c) => c.key === j);
    setField('experiencia', XP.labels.experience || card.title, card.title);
    XP.config[j].forEach((f) => {
      const v = answers(j)[f.id];
      if (v === undefined || v === '') return;
      const label = f.label;
      const shown = f.type === 'choice'
        ? (f.options.find((o) => o.value === v) || {}).label || v
        : String(v);
      setField(f.id, label, shown);
    });
    const d = answers(j).data;
    if (d) setField('data', XP.labels.date, formatDate(d, I18N.locale));
    form.dataset.journey = j;
    form.dataset.intro = XP.intro[j] || '';
  }

  function formatDate(iso, locale) {
    if (!iso) return '';
    const [y, m, d] = iso.split('-');
    return locale === 'en' ? `${m}/${d}/${y}` : `${d}/${m}/${y}`;
  }

  /* ---------- Passos ---------- */
  const STEP_CONFIG = 0;
  const STEP_DATE = 1;
  const STEP_CONTACT = 2;
  const STEP_REVIEW = 3;

  function renderSteps() {
    stepsEl.textContent = '';
    XP.steps.forEach((label, i) => {
      const li = document.createElement('li');
      li.className = 'xp-step';
      if (i === S.step) li.classList.add('is-on');
      if (i < S.step) li.classList.add('is-done');
      li.textContent = label;
      if (i === S.step) li.setAttribute('aria-current', 'step');
      stepsEl.append(li);
    });
  }

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  };

  function navRow({ onBack, nextLabel, onNext }) {
    const row = el('div', 'xp-nav');
    if (onBack) {
      const b = el('button', 'btn btn--line-dark xp-nav-back', XP.prev);
      b.type = 'button';
      b.addEventListener('click', onBack);
      row.append(b);
    }
    if (onNext) {
      const n = el('button', 'btn btn--gold xp-nav-next', nextLabel || XP.next);
      n.type = 'button';
      n.addEventListener('click', onNext);
      row.append(n);
    }
    return row;
  }

  /* Passo 1 — Configurar: só os campos daquela jornada. */
  function renderConfig() {
    const j = S.journey;
    const card = XP.cards.find((c) => c.key === j);
    panel.append(el('h2', 'xp-panel-title', card.title));
    panel.append(el('p', 'xp-panel-lead', card.desc));

    XP.config[j].forEach((f) => {
      const group = el('div', 'xp-group');
      group.append(el('span', 'xp-label', f.label));

      if (f.type === 'choice') {
        const list = el('div', 'xp-choices');
        f.options.forEach((o) => {
          const b = el('button', 'xp-choice', o.label);
          b.type = 'button';
          b.setAttribute('aria-pressed', String(answers(j)[f.id] === o.value));
          b.addEventListener('click', () => {
            answers(j)[f.id] = o.value;
            persist();
            render();
          });
          list.append(b);
        });
        group.append(list);
      } else {
        const wrap = el('div', 'xp-number');
        const dec = el('button', 'xp-step-btn', '−');
        const inc = el('button', 'xp-step-btn', '+');
        dec.type = 'button'; inc.type = 'button';
        dec.setAttribute('aria-label', `${f.label} −`);
        inc.setAttribute('aria-label', `${f.label} +`);
        const out = el('input', 'xp-number-input');
        out.type = 'number';
        out.min = f.min; out.max = f.max;
        out.inputMode = 'numeric';
        out.setAttribute('aria-label', f.label);
        out.value = answers(j)[f.id] || f.value;
        answers(j)[f.id] = Number(out.value);
        const bump = (d) => {
          const v = Math.min(f.max, Math.max(f.min, Number(out.value || f.value) + d));
          out.value = v; answers(j)[f.id] = v; persist();
        };
        dec.addEventListener('click', () => bump(-1));
        inc.addEventListener('click', () => bump(1));
        out.addEventListener('input', () => {
          const v = Number(out.value);
          if (!Number.isNaN(v)) { answers(j)[f.id] = v; persist(); }
        });
        wrap.append(dec, out, inc);
        group.append(wrap);
      }
      panel.append(group);
    });

    // Só avança com as escolhas feitas — número já nasce preenchido.
    const missing = XP.config[j].some((f) => f.type === 'choice' && !answers(j)[f.id]);
    const next = navRow({
      onBack: backToCarousel,
      onNext: missing ? null : () => { S.step = STEP_DATE; persist(); render(); },
    });
    if (missing) next.append(el('p', 'xp-nav-note', XP.choose));
    panel.append(next);
  }

  /* Passo 2 — Data: calendário visual (datepicker.js). */
  function renderDate() {
    const j = S.journey;
    panel.append(el('h2', 'xp-panel-title', j === 'treinar' ? XP.dateTitleTreinar : XP.dateTitle));

    const group = el('div', 'xp-group');
    const holder = el('div', 'cal');
    holder.setAttribute('data-datepicker', '');
    holder.setAttribute('data-for', 'xp-date');
    const input = el('input');
    input.type = 'date';
    input.id = 'xp-date';
    input.className = 'xp-date-input';
    input.value = answers(j).data || '';
    input.addEventListener('input', () => {
      answers(j).data = input.value;
      persist();
      const n = panel.querySelector('.xp-nav-next');
      if (n) n.disabled = !input.value;
    });
    group.append(holder, input);
    panel.append(group);

    const row = navRow({
      onBack: () => { S.step = STEP_CONFIG; persist(); render(); },
      onNext: () => { if (answers(j).data) { S.step = STEP_CONTACT; persist(); render(); } },
    });
    panel.append(row);
    const n = row.querySelector('.xp-nav-next');
    if (n) n.disabled = !answers(j).data;

    initDatePicker(I18N);
  }

  /* Passo 3 — Seus dados: o form real entra aqui. */
  function renderContact() {
    panel.append(el('h2', 'xp-panel-title', XP.contactTitle));
    mountForm('contact');
    panel.append(navRow({
      onBack: () => { S.step = STEP_DATE; persist(); render(); },
      onNext: () => {
        const name = form.querySelector('#xp-name');
        const err = document.getElementById('xp-name-error');
        if (!name.value.trim()) {
          name.setAttribute('aria-invalid', 'true');
          if (err) err.textContent = I18N.required;
          name.focus();
          return;
        }
        S.step = STEP_REVIEW; persist(); render();
      },
    }));
  }

  /* Passo 4 — Confirmar: revisão do que será enviado + botão real. */
  function renderReview() {
    panel.append(el('h2', 'xp-panel-title', XP.reviewTitle));
    panel.append(el('p', 'xp-panel-lead', XP.reviewLead));

    const dl = el('dl', 'xp-review');
    rowsForReview().forEach(([label, value]) => {
      const d = el('div');
      d.append(el('dt', null, label), el('dd', null, value));
      dl.append(d);
    });
    panel.append(dl);

    const edit = el('button', 'btn btn--line-dark xp-nav-back', XP.edit);
    edit.type = 'button';
    edit.addEventListener('click', () => { S.step = STEP_CONFIG; persist(); render(); });
    panel.append(edit);

    mountForm('review');
  }

  // Mesma leitura que o collect() do site.js fará no envio.
  function rowsForReview() {
    const rows = [];
    form.querySelectorAll('[data-label]').forEach((f) => {
      const v = (f.value || '').trim();
      if (!v || !f.dataset.label) return;
      rows.push([f.dataset.label, v]);
    });
    return rows;
  }

  /* O form vive fora do painel e é movido para dentro dele. Mover um nó
     preserva os listeners que o site.js já ligou — por isso ele nunca é
     recriado. */
  function mountForm(mode) {
    form.hidden = false;
    form.classList.toggle('is-review', mode === 'review');
    contact.hidden = mode !== 'contact';
    panel.append(form);
  }

  function unmountForm() {
    form.hidden = true;
    root.querySelector('.wrap').append(form);
  }

  /* ---------- Render geral ---------- */
  function render() {
    syncFields();
    panel.textContent = '';

    if (!S.journey) {
      unmountForm();
      stage.hidden = false;
      flow.hidden = true;
      hint.hidden = false;
      renderCarousel();
      return;
    }

    stage.hidden = true;
    flow.hidden = false;
    hint.hidden = true;
    renderSteps();

    if (S.step === STEP_CONFIG) renderConfig();
    else if (S.step === STEP_DATE) renderDate();
    else if (S.step === STEP_CONTACT) renderContact();
    else renderReview();

    syncFields();
  }

  function enter(journey, { focus = true } = {}) {
    S.journey = journey;
    S.step = STEP_CONFIG;
    persist();
    render();
    if (focus) panel.focus();
  }

  function backToCarousel() {
    S.journey = null;
    persist();
    render();
    const active = slides[S.index].querySelector('[data-xp-explore]');
    if (active) active.focus();
  }

  function persist() {
    save({ answers: S.answers, journey: S.journey, step: S.step });
  }

  root.querySelectorAll('[data-xp-explore]').forEach((a) => {
    a.addEventListener('click', (ev) => {
      ev.preventDefault();
      enter(a.dataset.xpExplore);
    });
  });
  root.querySelector('[data-xp-back-all]').addEventListener('click', backToCarousel);

  // Entrada direta: /agendar/?xp=treinar ou /agendar/#treinar — é assim que
  // os cartões da home levam a pessoa já para dentro da jornada certa.
  const params = new URLSearchParams(window.location.search);
  const deep = params.get('xp') || window.location.hash.replace('#', '');
  const deepIndex = slides.findIndex((s) => s.dataset.xpSlide === deep);

  if (deepIndex >= 0) {
    S.index = deepIndex;
    enter(deep, { focus: false });
  } else if (saved.journey && XP.config[saved.journey]) {
    S.index = Math.max(0, slides.findIndex((s) => s.dataset.xpSlide === saved.journey));
    S.journey = saved.journey;
    S.step = Math.min(STEP_REVIEW, saved.step || 0);
    render();
    if (hint) { hint.hidden = false; hint.textContent = XP.resumed; }
  } else {
    render();
  }
}
