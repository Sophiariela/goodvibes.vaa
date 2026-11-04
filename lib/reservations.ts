/**
 * Lógica de reservas que toca o banco — a parte que não dá pra testar sem
 * um Postgres real (Supabase). As regras puras (quanto cabe, o que conta
 * contra a capacidade) estão isoladas em lib/availability.ts e já têm
 * testes unitários; aqui só orquestra a transação.
 */

import { withTransaction, query } from './db.js';
import { computeHoldExpiry, isSessionInPast } from './availability.js';

export type ReservationErrorCode = 'NOT_FOUND' | 'PAST_SESSION' | 'CANCELLED' | 'NO_CAPACITY' | 'INVALID_INPUT';

export class ReservationError extends Error {
  constructor(message: string, public code: ReservationErrorCode) {
    super(message);
    this.name = 'ReservationError';
  }
}

export interface ParticipantInput {
  fullName: string;
  isMinor: boolean;
  birthDate: string | null;
}

export interface CreateReservationInput {
  sessionId: string;
  participantsCount: number;
  participants: ParticipantInput[];
  locale: 'pt' | 'en';
  contactName: string;
  contactPhone: string | null;
  contactEmail: string | null;
  termsAcceptedAt: string;
  notes: string | null;
}

export interface CreateReservationResult {
  reservationId: string;
  totalPriceCents: number;
  holdExpiresAt: Date;
}

/**
 * Cria a reserva com a vaga travada (hold), numa única transação:
 * 1. SELECT ... FOR UPDATE na sessão — trava a linha, ninguém mais consegue
 *    ler/decidir a mesma sessão até esta transação terminar.
 * 2. Soma participantes de reservas que já contam contra a capacidade
 *    (confirmadas, ou pending_payment com hold ainda válido).
 * 3. Só insere a reserva se couber — senão, lança NO_CAPACITY e a
 *    transação é desfeita (nada é escrito).
 *
 * Isso é o que de fato impede duas pessoas pegando a última vaga ao mesmo
 * tempo: a segunda transação só consegue o lock depois que a primeira
 * commitar (ou desistir), e nesse ponto já vê a vaga ocupada.
 */
export async function createReservationWithHold(input: CreateReservationInput): Promise<CreateReservationResult> {
  if (!Number.isInteger(input.participantsCount) || input.participantsCount <= 0) {
    throw new ReservationError('Número de participantes inválido.', 'INVALID_INPUT');
  }
  if (input.participants.length !== input.participantsCount) {
    throw new ReservationError('A lista de participantes não bate com o número informado.', 'INVALID_INPUT');
  }
  if (!input.contactName?.trim()) {
    throw new ReservationError('Nome de contato é obrigatório.', 'INVALID_INPUT');
  }
  if (!input.termsAcceptedAt) {
    throw new ReservationError('É preciso aceitar os termos antes de reservar.', 'INVALID_INPUT');
  }

  return withTransaction(async (client) => {
    const sessionRows = await client.query(
      `select s.id, s.experience_id, s.starts_at, s.capacity, s.status,
              e.price_cents, e.pricing_mode, e.journey
         from sessions s
         join experiences e on e.id = s.experience_id
        where s.id = $1
        for update of s`,
      [input.sessionId],
    );
    const session = sessionRows.rows[0];
    if (!session) throw new ReservationError('Sessão não encontrada.', 'NOT_FOUND');
    if (session.status === 'cancelled') throw new ReservationError('Esta sessão foi cancelada.', 'CANCELLED');
    if (isSessionInPast(new Date(session.starts_at))) {
      throw new ReservationError('Esta sessão já passou.', 'PAST_SESSION');
    }
    if (session.pricing_mode !== 'fixed' || session.price_cents == null) {
      throw new ReservationError('Esta experiência ainda não tem preço fixo configurado — use o fluxo de orçamento.', 'INVALID_INPUT');
    }

    const takenRows = await client.query<{ taken: number }>(
      `select coalesce(sum(participants_count), 0)::int as taken
         from reservations
        where session_id = $1
          and (status = 'confirmed' or (status = 'pending_payment' and hold_expires_at > now()))`,
      [input.sessionId],
    );
    const taken = takenRows.rows[0]?.taken ?? 0;
    const available = session.capacity - taken;
    if (available < input.participantsCount) {
      throw new ReservationError(
        available > 0 ? `Só restam ${available} vaga(s) nesta sessão.` : 'Esta sessão está esgotada.',
        'NO_CAPACITY',
      );
    }

    const holdExpiresAt = computeHoldExpiry();
    const totalPriceCents = session.price_cents * input.participantsCount;

    const inserted = await client.query<{ id: string }>(
      `insert into reservations
         (session_id, experience_id, journey, status, participants_count, total_price_cents,
          hold_expires_at, locale, contact_name, contact_phone, contact_email, terms_accepted_at, notes)
       values ($1,$2,$3,'pending_payment',$4,$5,$6,$7,$8,$9,$10,$11,$12)
       returning id`,
      [
        input.sessionId, session.experience_id, session.journey, input.participantsCount, totalPriceCents,
        holdExpiresAt.toISOString(), input.locale, input.contactName.trim(), input.contactPhone, input.contactEmail,
        input.termsAcceptedAt, input.notes,
      ],
    );
    const reservationId = inserted.rows[0]!.id;

    for (const p of input.participants) {
      if (!p.fullName?.trim()) throw new ReservationError('Nome de cada participante é obrigatório.', 'INVALID_INPUT');
      await client.query(
        `insert into participants (reservation_id, full_name, is_minor, birth_date) values ($1,$2,$3,$4)`,
        [reservationId, p.fullName.trim(), p.isMinor, p.birthDate],
      );
    }

    return { reservationId, totalPriceCents, holdExpiresAt };
  });
}

export interface CreateDirectRequestInput {
  /** Obrigatório para "treinar" (trava vaga real numa turma/sessão). */
  sessionId: string | null;
  /** Obrigatório quando sessionId é null (ex.: "particular", sem agenda fixa). */
  experienceSlug: string | null;
  participantsCount: number;
  locale: 'pt' | 'en';
  contactName: string;
  contactPhone: string | null;
  contactEmail: string | null;
  notes: string | null;
}

export interface CreateDirectRequestResult {
  reservationId: string;
  status: 'confirmed' | 'quote_requested';
}

/**
 * Treinar e Particular: solicitação sem Pix (ver api/requests.ts).
 *
 * - Com `sessionId` (Treinar): trava a vaga na turma como
 *   `createReservationWithHold`, mas confirma direto — não há cobrança
 *   nesta etapa, então não existe "aguardando pagamento".
 * - Sem `sessionId` (Particular): não há vaga pra travar, é sempre um
 *   pedido de orçamento (`quote_requested`) — a equipe do clube responde
 *   por fora com o valor.
 */
export async function createDirectRequest(input: CreateDirectRequestInput): Promise<CreateDirectRequestResult> {
  if (!Number.isInteger(input.participantsCount) || input.participantsCount <= 0) {
    throw new ReservationError('Número de participantes inválido.', 'INVALID_INPUT');
  }
  if (!input.contactName?.trim()) {
    throw new ReservationError('Nome de contato é obrigatório.', 'INVALID_INPUT');
  }

  if (input.sessionId) {
    return withTransaction(async (client) => {
      const sessionRows = await client.query(
        `select s.id, s.experience_id, s.capacity, s.status, s.starts_at, e.journey
           from sessions s
           join experiences e on e.id = s.experience_id
          where s.id = $1
          for update of s`,
        [input.sessionId],
      );
      const session = sessionRows.rows[0];
      if (!session) throw new ReservationError('Turma não encontrada.', 'NOT_FOUND');
      if (session.status === 'cancelled') throw new ReservationError('Esta turma foi cancelada.', 'CANCELLED');
      if (isSessionInPast(new Date(session.starts_at))) {
        throw new ReservationError('Esta turma já aconteceu.', 'PAST_SESSION');
      }

      const takenRows = await client.query<{ taken: number }>(
        `select coalesce(sum(participants_count), 0)::int as taken
           from reservations
          where session_id = $1
            and (status = 'confirmed' or (status = 'pending_payment' and hold_expires_at > now()))`,
        [input.sessionId],
      );
      const taken = takenRows.rows[0]?.taken ?? 0;
      const available = session.capacity - taken;
      if (available < input.participantsCount) {
        throw new ReservationError(
          available > 0 ? `Só restam ${available} vaga(s) nesta turma.` : 'Esta turma está esgotada.',
          'NO_CAPACITY',
        );
      }

      const inserted = await client.query<{ id: string }>(
        `insert into reservations
           (session_id, experience_id, journey, status, participants_count, locale, contact_name, contact_phone, contact_email, notes)
         values ($1,$2,$3,'confirmed',$4,$5,$6,$7,$8,$9)
         returning id`,
        [
          input.sessionId, session.experience_id, session.journey, input.participantsCount,
          input.locale, input.contactName.trim(), input.contactPhone, input.contactEmail, input.notes,
        ],
      );
      return { reservationId: inserted.rows[0]!.id, status: 'confirmed' };
    });
  }

  if (!input.experienceSlug) {
    throw new ReservationError('experienceSlug é obrigatório quando não há sessionId.', 'INVALID_INPUT');
  }
  const expRows = await query<{ id: string; journey: string }>(
    `select id, journey from experiences where slug = $1 and active = true`,
    [input.experienceSlug],
  );
  const experience = expRows[0];
  if (!experience) throw new ReservationError('Experiência não encontrada.', 'NOT_FOUND');

  const inserted = await query<{ id: string }>(
    `insert into reservations
       (session_id, experience_id, journey, status, participants_count, locale, contact_name, contact_phone, contact_email, notes)
     values (null,$1,$2,'quote_requested',$3,$4,$5,$6,$7,$8)
     returning id`,
    [
      experience.id, experience.journey, input.participantsCount,
      input.locale, input.contactName.trim(), input.contactPhone, input.contactEmail, input.notes,
    ],
  );
  return { reservationId: inserted[0]!.id, status: 'quote_requested' };
}

/** Cancela uma reserva própria — só funciona enquanto ainda está
 *  aguardando pagamento (não deixa cancelar uma já confirmada por aqui). */
export async function cancelPendingReservation(reservationId: string): Promise<boolean> {
  const rows = await query<{ id: string }>(
    `update reservations set status = 'cancelled'
      where id = $1 and status = 'pending_payment'
      returning id`,
    [reservationId],
  );
  return rows.length > 0;
}

export interface MercadoPagoPaymentLike {
  id: number | string;
  status: string;
  transaction_amount: number;
}

export type PaymentApplyResult =
  | { confirmed: true; reason?: 'already_confirmed' }
  | { confirmed: false; reason: 'amount_mismatch' | 'reservation_not_found' | 'payment_not_found' | 'no_action' };

/**
 * Aplica o status mais recente de um pagamento (já re-buscado na API do
 * Mercado Pago, nunca confiando só no corpo do webhook) à reserva
 * correspondente. Só confirma se o pagamento está 'approved' E o valor
 * bate exatamente com o esperado.
 */
export async function applyPaymentStatus(reservationId: string, payment: MercadoPagoPaymentLike): Promise<PaymentApplyResult> {
  return withTransaction(async (client) => {
    const payRows = await client.query(
      `select id from payments where reservation_id = $1 and provider_payment_id = $2`,
      [reservationId, String(payment.id)],
    );
    if (!payRows.rows[0]) return { confirmed: false, reason: 'payment_not_found' };

    await client.query(
      `update payments set status = $1, raw_last_status = $2 where reservation_id = $3 and provider_payment_id = $4`,
      [payment.status, JSON.stringify(payment), reservationId, String(payment.id)],
    );

    const resRows = await client.query(
      `select total_price_cents, status from reservations where id = $1 for update`,
      [reservationId],
    );
    const reservation = resRows.rows[0];
    if (!reservation) return { confirmed: false, reason: 'reservation_not_found' };
    if (reservation.status === 'confirmed') return { confirmed: true, reason: 'already_confirmed' };

    if (payment.status === 'approved') {
      const expectedCents = Math.round(payment.transaction_amount * 100);
      if (expectedCents !== reservation.total_price_cents) {
        return { confirmed: false, reason: 'amount_mismatch' };
      }
      await client.query(`update reservations set status = 'confirmed' where id = $1`, [reservationId]);
      return { confirmed: true };
    }

    if (payment.status === 'rejected' && reservation.status === 'pending_payment') {
      await client.query(`update reservations set status = 'rejected' where id = $1`, [reservationId]);
    } else if (payment.status === 'cancelled' && reservation.status === 'pending_payment') {
      await client.query(`update reservations set status = 'cancelled' where id = $1`, [reservationId]);
    }
    return { confirmed: false, reason: 'no_action' };
  });
}
