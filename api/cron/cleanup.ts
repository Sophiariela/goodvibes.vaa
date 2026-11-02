/**
 * GET /api/cron/cleanup — disparado 1x/dia pela Vercel (ver vercel.json,
 * "crons"). Isso é só faxina/organização: marca como 'expired' reservas
 * que ficaram 'pending_payment' com hold já vencido.
 *
 * A disponibilidade mostrada ao usuário NUNCA depende deste job — a query
 * de vagas (session_availability, em db/schema.sql) já ignora holds
 * vencidos automaticamente. Sem este cron, a aplicação continua correta;
 * só os registros antigos ficariam com status desatualizado por mais
 * tempo.
 *
 * A Vercel assina as chamadas de cron com o header `Authorization: Bearer
 * $CRON_SECRET` quando essa env var está definida — não é obrigatório,
 * mas evita que qualquer um dispare a faxina manualmente.
 */

import type { VercelRequest, VercelResponse } from '../../lib/http';
import { requireMethod } from '../../lib/http';
import { query } from '../../lib/db';

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'GET')) return;

  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret) {
    const auth = req.headers['authorization'];
    if (auth !== `Bearer ${cronSecret}`) {
      res.status(401).json({ error: 'unauthorized' });
      return;
    }
  }

  try {
    const expired = await query<{ id: string }>(
      `update reservations
          set status = 'expired'
        where status = 'pending_payment'
          and hold_expires_at is not null
          and hold_expires_at <= now()
        returning id`,
    );
    res.status(200).json({ expiredCount: expired.length });
  } catch (err) {
    console.error('Erro na faxina de reservas expiradas', err);
    res.status(500).json({ error: 'internal_error' });
  }
}
