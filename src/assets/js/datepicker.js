/* ==========================================================================
   Good Vibes Va'a — calendário visual da reserva

   Camada de apresentação sobre um <input type="date"> real: o input
   continua guardando o valor, recebendo o `min` de hoje (initForms em
   site.js) e sendo lido por collect()/validate(). Este módulo só desenha o
   mês e escreve no input — nenhuma regra de reserva, disponibilidade ou
   envio passa por aqui.

   Os nomes de mês e as iniciais de semana vêm do i18n da página
   (I18N.cal), nunca de toLocaleDateString: o texto do site sai sempre do
   HTML, como manda o CLAUDE.md.
   ========================================================================== */

function isoOf(date) {
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${m}-${d}`;
}

export function initDatePicker(I18N) {
  const cal = I18N.cal;
  if (!cal) return;

  document.querySelectorAll('[data-datepicker]').forEach((root) => {
    const input = document.getElementById(root.dataset.for);
    if (!input) return;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const view = new Date(today.getFullYear(), today.getMonth(), 1);

    const head = document.createElement('div');
    head.className = 'cal-head';

    const prev = document.createElement('button');
    prev.type = 'button';
    prev.className = 'cal-nav';
    prev.setAttribute('aria-label', cal.prev);
    prev.textContent = '‹';

    const label = document.createElement('span');
    label.className = 'cal-month';
    label.setAttribute('aria-live', 'polite');

    const next = document.createElement('button');
    next.type = 'button';
    next.className = 'cal-nav';
    next.setAttribute('aria-label', cal.next);
    next.textContent = '›';

    head.append(prev, label, next);

    const grid = document.createElement('div');
    grid.className = 'cal-grid';

    root.append(head, grid);

    function render() {
      label.textContent = `${cal.months[view.getMonth()]} ${view.getFullYear()}`;
      grid.textContent = '';

      // Cabeçalho de semana: decorativo para leitor de tela, que já ouve a
      // data inteira no aria-label de cada dia.
      cal.weekdays.forEach((w) => {
        const s = document.createElement('span');
        s.className = 'cal-wd';
        s.setAttribute('aria-hidden', 'true');
        s.textContent = w;
        grid.append(s);
      });

      const first = new Date(view.getFullYear(), view.getMonth(), 1);
      for (let i = 0; i < first.getDay(); i += 1) {
        const pad = document.createElement('span');
        pad.className = 'cal-pad';
        grid.append(pad);
      }

      const total = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
      for (let d = 1; d <= total; d += 1) {
        const date = new Date(view.getFullYear(), view.getMonth(), d);
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cal-day';
        btn.textContent = String(d);
        btn.dataset.date = isoOf(date);
        btn.disabled = date < today;
        if (date.getTime() === today.getTime()) btn.classList.add('is-today');
        btn.setAttribute('aria-pressed', input.value === btn.dataset.date ? 'true' : 'false');
        btn.setAttribute(
          'aria-label',
          `${cal.weekdaysFull[date.getDay()]}, ${d} ${cal.months[view.getMonth()]} ${view.getFullYear()}`,
        );
        grid.append(btn);
      }

      // Não há passado para navegar: o mês de hoje é o primeiro possível.
      prev.disabled = view.getFullYear() === today.getFullYear()
        && view.getMonth() === today.getMonth();
    }

    grid.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.cal-day');
      if (!btn || btn.disabled) return;
      input.value = btn.dataset.date;
      // Avisa o formulário: é esse evento que limpa o estado de erro do
      // campo em site.js (initForms).
      input.dispatchEvent(new Event('input', { bubbles: true }));
      render();
    });

    prev.addEventListener('click', () => { view.setMonth(view.getMonth() - 1); render(); });
    next.addEventListener('click', () => { view.setMonth(view.getMonth() + 1); render(); });
    // Quem digitar a data pelo campo em .sr-only vê o calendário acompanhar.
    input.addEventListener('change', render);

    render();
  });
}
