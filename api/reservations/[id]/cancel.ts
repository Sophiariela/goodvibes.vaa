/**
 * POST /api/reservations/:id/cancel
 *
 * Cliente desistindo antes de pagar. Só cancela enquanto a reserva está
 * 'pending_payment' — depois de confirmada, cancelamento é coisa de admin
 * (api/admin/*, etapa futura), não deste endpoint público.
 */

import type { VercelRequest, VercelResponse } from '../../../lib/http.js';
import { requireMethod } from '../../../lib/http.js';
import { cancelPendingReservation } from '../../../lib/reservations.js';
import { DbNotConfiguredError } from '../../../lib/db.js';

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'POST')) return;

  const id = typeof req.query.id === 'string' ? req.query.id : undefined;
  if (!id) {
    res.status(400).json({ error: 'INVALID_INPUT', message: 'id é obrigatório.' });
    return;
  }

  try {
    const cancelled = await cancelPendingReservation(id);
    if (!cancelled) {
      res.status(409).json({
        error: 'CANNOT_CANCEL',
        message: 'Reserva não encontrada, ou já não está mais aguardando pagamento.',
      });
      return;
    }
    res.status(200).json({ reservationId: id, status: 'cancelled' });
  } catch (err) {
    if (err instanceof DbNotConfiguredError) {
      res.status(503).json({ error: 'server_not_configured', message: err.message });
      return;
    }
    console.error('Erro ao cancelar reserva', err);
    res.status(500).json({ error: 'internal_error' });
  }
}
