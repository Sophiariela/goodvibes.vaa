/**
 * Mensagens da página de contato (/contato) — ver api/contact.ts.
 *
 * O site não envia e-mail: grava a mensagem no banco (tabela
 * contact_messages) para a equipe responder. Isso é de propósito —
 * inventar credencial de um provedor de e-mail seria mentira, e um
 * formulário que "finge" ter enviado é pior do que não existir. Quando o
 * clube tiver um endereço oficial e um provedor (Resend, Postmark, SES...),
 * basta somar o envio a `saveContactMessage`: o contrato da API, a
 * validação e o formulário não mudam.
 *
 * Validação pura aqui (testável sem banco); só o INSERT toca o Postgres.
 */

import { query } from './db.js';

export type ContactErrorCode =
  | 'INVALID_NAME'
  | 'INVALID_EMAIL'
  | 'INVALID_SUBJECT'
  | 'INVALID_MESSAGE';

export class ContactError extends Error {
  constructor(message: string, public code: ContactErrorCode) {
    super(message);
    this.name = 'ContactError';
  }
}

/** Mesma expressão de lib/subscribers.ts: aceita a grande maioria dos
 *  e-mails reais e rejeita o óbvio errado, sem validar o domínio. */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function isValidEmail(email: unknown): email is string {
  return typeof email === 'string' && email.trim().length <= 254 && EMAIL_RE.test(email.trim());
}

/** Assuntos aceitos. Espelha `ct_subjects` em build.py (os `value` do
 *  <select>): mudar um dos dois lados sem o outro faz o envio falhar com
 *  INVALID_SUBJECT. */
export const CONTACT_SUBJECTS = ['reserva', 'treino', 'particular', 'produtos', 'outro'] as const;
export type ContactSubject = (typeof CONTACT_SUBJECTS)[number];

export function isValidSubject(subject: unknown): subject is ContactSubject {
  return typeof subject === 'string' && (CONTACT_SUBJECTS as readonly string[]).includes(subject);
}

export const NAME_MIN = 2;
export const NAME_MAX = 120;
export const MESSAGE_MIN = 10;
export const MESSAGE_MAX = 4000;

export interface ContactInput {
  name: string;
  email: string;
  subject: string;
  message: string;
  locale: 'pt' | 'en';
}

export interface ContactResult {
  status: 'received';
  id: string;
}

/** Valida e grava. Lança ContactError (400 na API) quando o conteúdo é
 *  inválido e deixa erro de banco subir — api/contact.ts distingue "falta
 *  configurar" (503) de "quebrou" (500). */
export async function saveContactMessage(input: ContactInput): Promise<ContactResult> {
  const name = String(input.name ?? '').trim();
  const email = String(input.email ?? '').trim();
  const message = String(input.message ?? '').trim();

  if (name.length < NAME_MIN || name.length > NAME_MAX) {
    throw new ContactError('Informe seu nome.', 'INVALID_NAME');
  }
  if (!isValidEmail(email)) {
    throw new ContactError('E-mail inválido.', 'INVALID_EMAIL');
  }
  if (!isValidSubject(input.subject)) {
    throw new ContactError('Assunto inválido.', 'INVALID_SUBJECT');
  }
  if (message.length < MESSAGE_MIN || message.length > MESSAGE_MAX) {
    throw new ContactError('Escreva sua mensagem.', 'INVALID_MESSAGE');
  }

  const rows = await query<{ id: string }>(
    `insert into contact_messages (name, email, subject, message, locale)
     values ($1, $2, $3, $4, $5)
     returning id`,
    [name, email, input.subject, message, input.locale],
  );

  const row = rows[0];
  if (!row) {
    // insert ... returning sempre devolve a linha; se nao devolveu, algo
    // falhou de verdade e o chamador precisa saber (500), nunca "enviado".
    throw new Error('INSERT em contact_messages nao retornou linha.');
  }
  return { status: 'received', id: row.id };
}
