/**
 * POST /api/contact
 *
 * Formulário da página /contato. Mesma proteção contra spam do cadastro de
 * newsletter, e pela mesma razão (minimização de dados — não coletamos IP):
 *   1. Honeypot — campo "website" escondido por CSS; só bot preenche.
 *   2. Tempo mínimo — o cliente manda `renderedAt` (quando o formulário
 *      foi montado); preencher nome, e-mail, assunto e mensagem em menos
 *      de 2s é, na prática, sempre automação.
 * Nos dois casos respondemos 201 sem gravar nada: não damos ao bot a
 * pista de que foi barrado.
 *
 * A mensagem é gravada em contact_messages (ver lib/contact.ts) — o site
 * não dispara e-mail. Sem SUPABASE_DB_URL o endpoint responde 503
 * "server_not_configured", e o formulário mostra que o envio por e-mail
 * ainda não está ativo e oferece o WhatsApp. NUNCA responder sucesso
 * quando a mensagem não foi gravada.
 */

import type { VercelRequest, VercelResponse } from '../lib/http.js';
import { requireMethod } from '../lib/http.js';
import { saveContactMessage, ContactError, type ContactErrorCode } from '../lib/contact.js';
import { DbNotConfiguredError } from '../lib/db.js';

const STATUS_BY_CODE: Record<ContactErrorCode, number> = {
  INVALID_NAME: 400,
  INVALID_EMAIL: 400,
  INVALID_SUBJECT: 400,
  INVALID_MESSAGE: 400,
};

const MIN_FILL_TIME_MS = 2000;

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'POST')) return;

  const body = req.body ?? {};

  if (typeof body.website === 'string' && body.website.trim()) {
    res.status(201).json({ status: 'received' });
    return;
  }

  const renderedAt = Number(body.renderedAt);
  if (Number.isFinite(renderedAt) && Date.now() - renderedAt < MIN_FILL_TIME_MS) {
    res.status(201).json({ status: 'received' });
    return;
  }

  if (body.locale !== 'pt' && body.locale !== 'en') {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'locale deve ser "pt" ou "en".' });
    return;
  }

  try {
    const result = await saveContactMessage({
      name: String(body.name ?? ''),
      email: String(body.email ?? ''),
      subject: String(body.subject ?? ''),
      message: String(body.message ?? ''),
      locale: body.locale,
    });
    res.status(201).json({ status: result.status });
  } catch (err) {
    if (err instanceof ContactError) {
      res.status(STATUS_BY_CODE[err.code]).json({ error: err.code, message: err.message });
      return;
    }
    if (err instanceof DbNotConfiguredError) {
      res.status(503).json({ error: 'server_not_configured', message: err.message });
      return;
    }
    console.error('Erro ao gravar mensagem de contato', err);
    res.status(500).json({ error: 'internal_error' });
  }
}
