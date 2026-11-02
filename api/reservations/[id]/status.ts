/**
 * GET /api/reservations/:id/status
 *
 * Usado pelo frontend fazendo polling (a cada poucos segundos) enquanto o
 * modal do Pix está aberto, pra saber quando o pagamento foi confirmado.
 * Nunca retorna "confirmed" a não ser que reservations.status já tenha sido
 * atualizado pelo webhook (fonte da verdade) — este endpoint só lê.
 */

import type { VercelRequest, VercelResponse } from '../../../lib/http';
import { requireMethod } from '../../../lib/http';
import { query } from '../../../lib/db';

interface StatusRow {
  id: string;
  status: string;
  hold_expires_at: string | null;
  total_price_cents: number | null;
  payment_status: string | null;
  qr_code: string | null;
  qr_code_base64: string | null;
  payment_expires_at: string | null;
}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'GET')) return;

  const id = typeof req.query.id === 'string' ? req.query.id : undefined;
  if (!id) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'id é obrigatório.' });
    return;
  }

  let rows: StatusRow[];
  try {
    rows = await query<StatusRow>(
      `select r.id, r.status, r.hold_expires_at, r.total_price_cents,
              p.status as payment_status, p.qr_code, p.qr_code_base64, p.expires_at as payment_expires_at
         from reservations r
         left join payments p on p.reservation_id = r.id
        where r.id = $1
        order by p.created_at desc
        limit 1`,
      [id],
    );
  } catch (err) {
    console.error('Erro ao consultar status da reserva', err);
    res.status(500).json({ error: 'internal_error' });
    return;
  }

  const row = rows[0];
  if (!row) {
    res.status(404).json({ error: 'NOT_FOUND' });
    return;
  }

  res.status(200).json({
    reservationId: row.id,
    status: row.status,
    holdExpiresAt: row.hold_expires_at,
    totalPriceCents: row.total_price_cents,
    payment: row.payment_status
      ? { status: row.payment_status, qrCode: row.qr_code, qrCodeBase64: row.qr_code_base64, expiresAt: row.payment_expires_at }
      : null,
  });
}
