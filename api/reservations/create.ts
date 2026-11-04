/**
 * POST /api/reservations
 *
 * Cria a reserva com a vaga travada (ver lib/reservations.ts) e, se deu
 * certo, já gera a cobrança Pix no Mercado Pago. Se a reserva foi criada
 * mas o Pix falhou, a reserva é cancelada de volta (não deixamos uma vaga
 * seguradasem cobrança pendurada).
 *
 * Corpo esperado:
 * {
 *   sessionId: string,
 *   participants: { fullName: string, isMinor: boolean, birthDate: string|null }[],
 *   locale: 'pt' | 'en',
 *   contactName: string,
 *   contactPhone?: string,
 *   contactEmail?: string,
 *   termsAcceptedAt: string (ISO),
 *   notes?: string
 * }
 */

import type { VercelRequest, VercelResponse } from '../../lib/http.js';
import { requireMethod } from '../../lib/http.js';
import { createReservationWithHold, ReservationError, type ReservationErrorCode } from '../../lib/reservations.js';
import { createPixPayment, MercadoPagoError } from '../../lib/mercadopago.js';
import { query, DbNotConfiguredError } from '../../lib/db.js';

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

  const accessToken = process.env.MP_ACCESS_TOKEN;
  const baseUrl = process.env.PUBLIC_BASE_URL;
  if (!accessToken || !baseUrl) {
    res.status(503).json({
      error: 'server_not_configured',
      message: 'Backend de pagamento ainda não configurado (faltam credenciais do Mercado Pago). Ver docs/SETUP.md.',
    });
    return;
  }

  const body = req.body ?? {};
  if (!isNonEmptyString(body.sessionId)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'sessionId é obrigatório.' });
    return;
  }
  if (!Array.isArray(body.participants) || body.participants.length === 0) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'Informe ao menos um participante.' });
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
  if (!isNonEmptyString(body.termsAcceptedAt)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'É preciso aceitar os termos.' });
    return;
  }
  if (!isNonEmptyString(body.contactEmail) && !isNonEmptyString(body.contactPhone)) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'Informe e-mail ou telefone de contato.' });
    return;
  }

  let reservation;
  try {
    reservation = await createReservationWithHold({
      sessionId: body.sessionId,
      participantsCount: body.participants.length,
      participants: body.participants.map((p: any) => ({
        fullName: String(p?.fullName ?? ''),
        isMinor: Boolean(p?.isMinor),
        birthDate: p?.birthDate ?? null,
      })),
      locale: body.locale,
      contactName: body.contactName,
      contactPhone: body.contactPhone ?? null,
      contactEmail: body.contactEmail ?? null,
      termsAcceptedAt: body.termsAcceptedAt,
      notes: body.notes ?? null,
    });
  } catch (err) {
    if (err instanceof ReservationError) {
      res.status(STATUS_BY_CODE[err.code]).json({ error: err.code, message: err.message });
      return;
    }
    if (err instanceof DbNotConfiguredError) {
      res.status(503).json({ error: 'server_not_configured', message: err.message });
      return;
    }
    console.error('Erro ao criar reserva', err);
    res.status(500).json({ error: 'internal_error' });
    return;
  }

  try {
    const payment = await createPixPayment(
      {
        amountCents: reservation.totalPriceCents,
        description: `Good Vibes Va'a — reserva ${reservation.reservationId}`,
        payerEmail: isNonEmptyString(body.contactEmail) ? body.contactEmail : 'sememail@goodvibesvaa.com.br',
        externalReference: reservation.reservationId,
        notificationUrl: `${baseUrl}/api/webhooks/mercadopago`,
      },
      accessToken,
      reservation.reservationId, // idempotency key: nunca cria 2 cobranças pra mesma reserva
    );

    await query(
      `insert into payments
         (reservation_id, provider, provider_payment_id, status, amount_cents, qr_code, qr_code_base64, expires_at, raw_last_status)
       values ($1,'mercadopago',$2,$3,$4,$5,$6,$7,$8)`,
      [
        reservation.reservationId, String(payment.id), payment.status, reservation.totalPriceCents,
        payment.qrCode, payment.qrCodeBase64, payment.expiresAt, JSON.stringify(payment.raw),
      ],
    );

    res.status(201).json({
      reservationId: reservation.reservationId,
      holdExpiresAt: reservation.holdExpiresAt.toISOString(),
      totalPriceCents: reservation.totalPriceCents,
      payment: {
        status: payment.status,
        qrCode: payment.qrCode,
        qrCodeBase64: payment.qrCodeBase64,
        expiresAt: payment.expiresAt,
      },
    });
  } catch (err) {
    // A vaga foi travada mas a cobrança falhou — libera de volta, não
    // prende a vaga de ninguém sem uma forma real de pagar.
    await query(`update reservations set status = 'cancelled' where id = $1 and status = 'pending_payment'`, [
      reservation.reservationId,
    ]).catch((cleanupErr) => console.error('Falha ao desfazer hold após erro de pagamento', cleanupErr));

    console.error('Erro ao criar cobrança Pix', err);
    const message = err instanceof MercadoPagoError ? err.message : 'Falha ao criar cobrança Pix.';
    res.status(502).json({ error: 'payment_provider_error', message });
  }
}
