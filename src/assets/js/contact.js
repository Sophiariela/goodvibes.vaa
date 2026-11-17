/* ==========================================================================
   Formulário da página /contato.

   Envio REAL: POST /api/contact grava a mensagem no banco (ver
   api/contact.ts). O formulário nunca mostra sucesso sem o servidor ter
   confirmado — se o backend ainda não está configurado (503), a mensagem
   na tela diz exatamente isso e aponta o WhatsApp ao lado, em vez de
   fingir que a mensagem chegou.

   Proteção contra spam sem coletar IP, igual ao pop-up de newsletter:
   honeypot (campo "website" escondido) + tempo mínimo de preenchimento
   (`renderedAt`), os dois verificados de novo no servidor.

   Todo texto vem do <script id="i18n"> da página, nunca daqui.
   ========================================================================== */

const ENDPOINT = '/api/contact';

export function initContact({ i18n }) {
  const form = document.querySelector('[data-contact-form]');
  if (!form) return;

  const T = i18n.contact || {};
  const status = form.querySelector('.form-status');
  const submit = form.querySelector('[type="submit"]');
  const renderedAt = Date.now();

  const setError = (el, msg) => {
    el.setAttribute('aria-invalid', msg ? 'true' : 'false');
    const slot = document.getElementById(`${el.id}-error`);
    if (slot) slot.textContent = msg;
    return !msg;
  };

  // Limpa o erro assim que a pessoa corrige o campo.
  form.addEventListener('input', (e) => {
    const el = e.target;
    if (el.getAttribute('aria-invalid') === 'true' && el.value.trim()) setError(el, '');
  });

  const validate = () => {
    let firstInvalid = null;
    form.querySelectorAll('[required]').forEach((el) => {
      let msg = '';
      if (!el.value.trim()) msg = i18n.required;
      else if (el.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(el.value.trim())) msg = i18n.invalidEmail;
      setError(el, msg);
      if (msg && !firstInvalid) firstInvalid = el;
    });
    if (firstInvalid) firstInvalid.focus();
    return !firstInvalid;
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.classList.remove('is-ok', 'is-bad');
    if (!validate()) return;

    submit.disabled = true;
    status.textContent = T.sending || '';

    try {
      const res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.elements.name.value,
          email: form.elements.email.value,
          subject: form.elements.subject.value,
          message: form.elements.message.value,
          locale: i18n.locale,
          website: form.elements.website.value,
          renderedAt,
        }),
      });

      if (res.ok) {
        status.textContent = T.ok;
        status.classList.add('is-ok');
        form.reset();
        return;
      }
      // 503 = backend ainda não configurado. É diferente de "deu erro":
      // a pessoa precisa saber que o canal não está ativo, não tentar de novo.
      status.textContent = res.status === 503 ? T.offline : T.error;
      status.classList.add('is-bad');
    } catch {
      status.textContent = T.error;
      status.classList.add('is-bad');
    } finally {
      submit.disabled = false;
    }
  });
}
