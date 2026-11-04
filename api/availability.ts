/**
 * GET /api/availability?experience=<slug>
 *
 * Lista as próximas sessões de uma experiência com vagas calculadas em
 * tempo real (view session_availability — ver db/schema.sql). Só leitura,
 * sem lock: o lock de verdade acontece em POST /api/reservations.
 */

import type { VercelRequest, VercelResponse } from '../lib/http.js';
import { requireMethod } from '../lib/http.js';
import { query, DbNotConfiguredError } from '../lib/db.js';
import { labelFromSeatsAvailable } from '../lib/availability.js';

interface SessionRow {
  session_id: string;
  starts_at: string;
  capacity: number;
  session_status: 'open' | 'cancelled';
  seats_available: number;
  price_cents: number | null;
  name_pt: string;
  name_en: string;
}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'GET')) return;

  const slug = typeof req.query.experience === 'string' ? req.query.experience : undefined;
  if (!slug) {
    res.status(400).json({ error: 'missing_experience', message: 'Informe ?experience=<slug>.' });
    return;
  }

  let rows: SessionRow[];
  try {
    rows = await query<SessionRow>(
      `select sa.session_id, sa.starts_at, sa.capacity, sa.session_status, sa.seats_available,
              e.price_cents, e.name_pt, e.name_en
         from session_availability sa
         join experiences e on e.id = sa.experience_id
        where e.slug = $1 and e.active = true and sa.starts_at > now()
        order by sa.starts_at asc`,
      [slug],
    );
  } catch (err) {
    if (err instanceof DbNotConfiguredError) {
      res.status(503).json({ error: 'server_not_configured', message: err.message });
      return;
    }
    console.error('Erro ao buscar disponibilidade', err);
    res.status(500).json({ error: 'internal_error' });
    return;
  }

  const sessions = rows.map((r) => ({
    sessionId: r.session_id,
    startsAt: r.starts_at,
    capacity: r.capacity,
    seatsAvailable: Math.max(r.seats_available, 0),
    priceCents: r.price_cents,
    status: labelFromSeatsAvailable(r.session_status, r.seats_available),
    name: { pt: r.name_pt, en: r.name_en },
  }));

  res.status(200).json({ sessions });
}
