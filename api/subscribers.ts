/**
 * POST /api/subscribers
 *
 * Cadastro do pop-up de newsletter. Proteção contra spam SEM coletar IP
 * (minimização de dados, LGPD):
 *   1. Honeypot — campo "website" escondido por CSS; só um bot preenche.
 *      Se vier preenchido, respondemos 201 "ok" sem gravar nada (não dá
 *      pista pro bot de que foi barrado).
 *   2. Tempo mínimo — o cliente manda `renderedAt` (timestamp de quando o
 *      pop-up abriu); um envio em menos de 1.2s de um formulário com campo
 *      de e-mail + checkbox é, na prática, sempre automação.
 *
 * Duplicidade: `subscribeEmail` já trata via UNIQUE(email_normalized) no
 * banco (ver db/schema.sql) — reenviar o mesmo e-mail responde 200
 * "already_subscribed", nunca um erro.
 */

import type { VercelRequest, VercelResponse } from '../lib/http.js';
import { requireMethod } from '../lib/http.js';
import { subscribeEmail, SubscriberError, type SubscriberErrorCode } from '../lib/subscribers.js';
import { DbNotConfiguredError } from '../lib/db.js';

const STATUS_BY_CODE: Record<SubscriberErrorCode, number> = {
  INVALID_EMAIL: 400,
  CONSENT_REQUIRED: 400,
  INVALID_INPUT: 400,
};

const MIN_FILL_TIME_MS = 1200;

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'POST')) return;

  const body = req.body ?? {};

  // Honeypot: campo que só um bot preenche. Finge sucesso, não grava nada.
  if (typeof body.website === 'string' && body.website.trim()) {
    res.status(201).json({ status: 'created' });
    return;
  }

  const renderedAt = Number(body.renderedAt);
  if (Number.isFinite(renderedAt) && Date.now() - renderedAt < MIN_FILL_TIME_MS) {
    res.status(201).json({ status: 'created' });
    return;
  }

  if (body.locale !== 'pt' && body.locale !== 'en') {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'locale deve ser "pt" ou "en".' });
    return;
  }
  if (typeof body.marketingConsent !== 'boolean') {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'marketingConsent é obrigatório.' });
    return;
  }

  try {
    const result = await subscribeEmail({
      email: String(body.email ?? ''),
      locale: body.locale,
      marketingConsent: body.marketingConsent,
      consentText: String(body.consentText ?? ''),
      source: typeof body.source === 'string' && body.source ? body.source : 'popup',
      campaignKey: typeof body.campaignKey === 'string' && body.campaignKey ? body.campaignKey : null,
    });
    res.status(result.status === 'created' ? 201 : 200).json(result);
  } catch (err) {
    if (err instanceof SubscriberError) {
      res.status(STATUS_BY_CODE[err.code]).json({ error: err.code, message: err.message });
      return;
    }
    if (err instanceof DbNotConfiguredError) {
      res.status(503).json({ error: 'server_not_configured', message: err.message });
      return;
    }
    console.error('Erro ao cadastrar e-mail', err);
    res.status(500).json({ error: 'internal_error' });
  }
}
