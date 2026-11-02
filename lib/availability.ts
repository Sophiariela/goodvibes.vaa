/**
 * Lógica pura de disponibilidade e holds. Sem I/O, sem banco — só as regras
 * de negócio, pra serem testadas isoladamente e reaproveitadas tanto pela
 * API (api/availability, api/reservations/create) quanto por testes de
 * concorrência.
 *
 * A fonte da verdade de "cabe ou não cabe" continua sendo a query SQL com
 * SELECT ... FOR UPDATE (ver db/schema.sql e api/reservations/create.ts) —
 * estas funções descrevem a MESMA regra em TypeScript para: (a) calcular o
 * que mostrar na tela antes de tentar reservar, e (b) ser testável sem
 * precisar de um Postgres rodando.
 */

export type SessionStatus = 'open' | 'cancelled';

export type ReservationStatus =
  | 'quote_requested'
  | 'quote_sent'
  | 'pending_payment'
  | 'confirmed'
  | 'expired'
  | 'cancelled'
  | 'rejected';

export interface ReservationForAvailability {
  status: ReservationStatus;
  participantsCount: number;
  holdExpiresAt: Date | null;
}

export type AvailabilityLabel = 'disponivel' | 'quase_esgotado' | 'esgotado' | 'cancelado';

const LOW_THRESHOLD = 2;

/** Uma reserva "conta" contra a capacidade se está confirmada, ou se ainda
 *  está com o hold de pagamento válido (não vencido). */
export function reservationCountsTowardCapacity(r: ReservationForAvailability, now: Date): boolean {
  if (r.status === 'confirmed') return true;
  if (r.status === 'pending_payment') return r.holdExpiresAt !== null && r.holdExpiresAt.getTime() > now.getTime();
  return false;
}

export function seatsTaken(reservations: ReservationForAvailability[], now: Date = new Date()): number {
  return reservations
    .filter((r) => reservationCountsTowardCapacity(r, now))
    .reduce((sum, r) => sum + r.participantsCount, 0);
}

export function seatsAvailable(capacity: number, reservations: ReservationForAvailability[], now: Date = new Date()): number {
  return capacity - seatsTaken(reservations, now);
}

export function availabilityLabel(
  sessionStatus: SessionStatus,
  capacity: number,
  reservations: ReservationForAvailability[],
  now: Date = new Date(),
): AvailabilityLabel {
  if (sessionStatus === 'cancelled') return 'cancelado';
  const free = seatsAvailable(capacity, reservations, now);
  if (free <= 0) return 'esgotado';
  if (free <= LOW_THRESHOLD) return 'quase_esgotado';
  return 'disponivel';
}

/**
 * Decide se uma nova tentativa de reserva de `requested` participantes cabe.
 * Usada tanto para validação otimista no cliente (via GET /api/availability)
 * quanto, de forma equivalente, dentro da transação travada no servidor.
 */
export function canReserve(
  capacity: number,
  reservations: ReservationForAvailability[],
  requested: number,
  now: Date = new Date(),
): boolean {
  if (requested <= 0) return false;
  return seatsAvailable(capacity, reservations, now) >= requested;
}

export const HOLD_DURATION_MINUTES = 15;

export function computeHoldExpiry(now: Date = new Date()): Date {
  return new Date(now.getTime() + HOLD_DURATION_MINUTES * 60_000);
}

/** Uma sessão não pode ser reservada se o horário dela já passou. */
export function isSessionInPast(startsAt: Date, now: Date = new Date()): boolean {
  return startsAt.getTime() <= now.getTime();
}
