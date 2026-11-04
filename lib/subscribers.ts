/**
 * Cadastro de e-mail do pop-up de newsletter — ver api/subscribers.ts.
 * Validação de formato + consentimento aqui (puro, testável); o
 * INSERT com dedupe por e-mail toca o banco.
 */

import { query } from './db.js';

export type SubscriberErrorCode = 'INVALID_EMAIL' | 'CONSENT_REQUIRED' | 'INVALID_INPUT';

export class SubscriberError extends Error {
  constructor(message: string, public code: SubscriberErrorCode) {
    super(message);
    this.name = 'SubscriberError';
  }
}

// RFC 5322 "bom o bastante": aceita a grande maioria dos e-mails reais,
// rejeita o óbvio errado, sem tentar validar o domínio de verdade (isso
// só o envio de um e-mail real confirma).
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function isValidEmail(email: unknown): email is string {
  return typeof email === 'string' && email.trim().length <= 254 && EMAIL_RE.test(email.trim());
}

export interface SubscribeInput {
  email: string;
  locale: 'pt' | 'en';
  marketingConsent: boolean;
  consentText: string;
  source: string;
  campaignKey: string | null;
}

export type SubscribeResult = { status: 'created' } | { status: 'already_subscribed' };

export async function subscribeEmail(input: SubscribeInput): Promise<SubscribeResult> {
  if (!isValidEmail(input.email)) {
    throw new SubscriberError('E-mail inválido.', 'INVALID_EMAIL');
  }
  if (!input.marketingConsent) {
    throw new SubscriberError('É preciso aceitar para continuar.', 'CONSENT_REQUIRED');
  }
  if (!input.consentText?.trim()) {
    throw new SubscriberError('Texto de consentimento ausente.', 'INVALID_INPUT');
  }

  const rows = await query<{ id: string }>(
    `insert into subscribers (email, locale, marketing_consent, consent_text, source, campaign_key)
     values ($1, $2, $3, $4, $5, $6)
     on conflict (email_normalized) do nothing
     returning id`,
    [input.email.trim(), input.locale, input.marketingConsent, input.consentText, input.source, input.campaignKey],
  );

  return rows.length > 0 ? { status: 'created' } : { status: 'already_subscribed' };
}
