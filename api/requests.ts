/**
 * POST /api/requests
 *
 * Treinar e Particular: solicitação sem Pix (ver lib/reservations.ts,
 * createDirectRequest). Diferente de /api/reservations/create, nunca gera
 * cobrança — Treinar trava uma vaga real na turma e confirma direto;
 * Particular é sempre um pedido de orçamento, sem agenda fixa.
 *
 * Corpo esperado:
 * {
 *   journey: 'treinar' | 'particular',
 *   locale: 'pt' | 'en',
 *   contactName: string,
 *   contactPhone?: string,
 *   contactEmail?: string,
 *   sessionId?: string,       // obrigatório para "treinar"
 *   experienceSlug?: string,  // obrigatório para "particular"
 *   participantsCount?: number,
 *   notes?: string
 * }
 */

import type { VercelRequest, VercelResponse } from '../lib/http.js';
import { requireMethod } from '../lib/http.js';
import { createDirectRequest, ReservationError, type ReservationErrorCode } from '../lib/reservations.js';
import { DbNotConfiguredError } from '../lib/db.js';

const STATUS_BY_CODE: Record<ReservationErrorCode, number> = {
  NOT_FOUND: 404,
  PAST_SESSION: 409,
  CANCELLED: 409,
  NO_CAPACITY: 409,
  INVALID_INPUT: 400,
};

function isNonEmptyString(v: unknown): v is string {
  return typeof v === 'string' && v.trim().length > 0;
}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'POST')) return;

  const body = req.body ?? {};
  if (body.journey !== 'treinar' && body.journey !== 'particular') {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'journey deve ser "treinar" ou "particular".' });
    return;
  }
  if (body.locale !== 'pt' && body.locale !== 'en') {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'locale deve ser "pt" ou "en".' });
    return;
  }
  if (!isNonEmptyString(body.contactName)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'contactName é obrigatório.' });
    return;
  }
  if (body.journey === 'treinar' && !isNonEmptyString(body.sessionId)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'sessionId é obrigatório para treinar.' });
    return;
  }
  if (body.journey === 'particular' && !isNonEmptyString(body.experienceSlug)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'experienceSlug é obrigatório para particular.' });
    return;
  }
  if (!isNonEmptyString(body.contactEmail) && !isNonEmptyString(body.contactPhone)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'Informe e-mail ou telefone de contato.' });
    return;
  }

  try {
    const result = await createDirectRequest({
      sessionId: body.journey === 'treinar' ? body.sessionId : null,
      experienceSlug: body.journey === 'particular' ? body.experienceSlug : null,
      participantsCount: Number.isInteger(body.participantsCount) && body.participantsCount > 0 ? body.participantsCount : 1,
      locale: body.locale,
      contactName: body.contactName,
      contactPhone: body.contactPhone ?? null,
      contactEmail: body.contactEmail ?? null,
      notes: body.notes ?? null,
    });
    res.status(201).json({ reservationId: result.reservationId, status: result.status });
  } catch (err) {
    if (err instanceof ReservationError) {
      res.status(STATUS_BY_CODE[err.code]).json({ error: err.code, message: err.message });
      return;
    }
    if (err instanceof DbNotConfiguredError) {
      res.status(503).json({ error: 'server_not_configured', message: err.message });
      return;
    }
    console.error('Erro ao criar solicitação', err);
    res.status(500).json({ error: 'internal_error' });
  }
}
