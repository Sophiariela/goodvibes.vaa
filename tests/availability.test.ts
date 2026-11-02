import { describe, it, expect } from 'vitest';
import {
  seatsAvailable,
  canReserve,
  availabilityLabel,
  labelFromSeatsAvailable,
  reservationCountsTowardCapacity,
  isSessionInPast,
  computeHoldExpiry,
  HOLD_DURATION_MINUTES,
  type ReservationForAvailability,
} from '../lib/availability';

const now = new Date('2026-06-01T12:00:00Z');

function res(partial: Partial<ReservationForAvailability>): ReservationForAvailability {
  return {
    status: 'confirmed',
    participantsCount: 1,
    holdExpiresAt: null,
    ...partial,
  };
}

describe('reservationCountsTowardCapacity', () => {
  it('conta reservas confirmadas', () => {
    expect(reservationCountsTowardCapacity(res({ status: 'confirmed' }), now)).toBe(true);
  });

  it('conta pending_payment com hold ainda válido', () => {
    const r = res({ status: 'pending_payment', holdExpiresAt: new Date(now.getTime() + 60_000) });
    expect(reservationCountsTowardCapacity(r, now)).toBe(true);
  });

  it('NÃO conta pending_payment com hold vencido', () => {
    const r = res({ status: 'pending_payment', holdExpiresAt: new Date(now.getTime() - 1000) });
    expect(reservationCountsTowardCapacity(r, now)).toBe(false);
  });

  it('não conta reservas expiradas, canceladas ou rejeitadas', () => {
    for (const status of ['expired', 'cancelled', 'rejected'] as const) {
      expect(reservationCountsTowardCapacity(res({ status }), now)).toBe(false);
    }
  });
});

describe('seatsAvailable / canReserve', () => {
  it('capacidade cheia quando não há reservas', () => {
    expect(seatsAvailable(6, [], now)).toBe(6);
  });

  it('desconta participantes de reservas confirmadas', () => {
    const reservations = [res({ participantsCount: 2 }), res({ participantsCount: 3 })];
    expect(seatsAvailable(6, reservations, now)).toBe(1);
  });

  it('impede reserva maior que o restante', () => {
    const reservations = [res({ participantsCount: 5 })];
    expect(canReserve(6, reservations, 2, now)).toBe(false);
    expect(canReserve(6, reservations, 1, now)).toBe(true);
  });

  it('a última vaga só pode ir para uma de duas tentativas simultâneas (simulado)', () => {
    // Simula a checagem otimista que o servidor faria para duas requisições
    // concorrentes contra o MESMO snapshot de reservas (sem lock real — o
    // lock de verdade é no Postgres). Isso documenta a regra; o teste de
    // concorrência de fato roda contra um Postgres real na Etapa 3.
    const reservations = [res({ participantsCount: 5 })]; // 1 vaga livre de 6
    const requestA = canReserve(6, reservations, 1, now);
    const requestB = canReserve(6, reservations, 1, now);
    // Sem lock, as duas veriam "cabe" no mesmo snapshot — por isso a soma
    // real de participantes após ambas seria validada de novo no servidor
    // dentro da transação travada antes de confirmar. Este teste documenta
    // por que o lock é necessário, não substitui o teste de concorrência real.
    expect(requestA && requestB).toBe(true);
    const bothAccepted = [res({ participantsCount: 5 }), res({ participantsCount: 1 }), res({ participantsCount: 1 })];
    expect(seatsAvailable(6, bothAccepted, now)).toBeLessThan(0); // overbooking se não houver lock
  });

  it('não permite reservar 0 ou valores negativos', () => {
    expect(canReserve(6, [], 0, now)).toBe(false);
    expect(canReserve(6, [], -1, now)).toBe(false);
  });
});

describe('availabilityLabel', () => {
  it('cancelado tem prioridade sobre contagem de vagas', () => {
    expect(availabilityLabel('cancelled', 6, [], now)).toBe('cancelado');
  });

  it('disponível quando sobra mais que o limiar de quase-esgotado', () => {
    expect(availabilityLabel('open', 6, [res({ participantsCount: 1 })], now)).toBe('disponivel');
  });

  it('quase esgotado com 1 ou 2 vagas livres', () => {
    expect(availabilityLabel('open', 6, [res({ participantsCount: 4 })], now)).toBe('quase_esgotado');
    expect(availabilityLabel('open', 6, [res({ participantsCount: 5 })], now)).toBe('quase_esgotado');
  });

  it('esgotado quando não sobra vaga', () => {
    expect(availabilityLabel('open', 6, [res({ participantsCount: 6 })], now)).toBe('esgotado');
  });
});

describe('labelFromSeatsAvailable', () => {
  it('cancelado tem prioridade sobre qualquer contagem', () => {
    expect(labelFromSeatsAvailable('cancelled', 5)).toBe('cancelado');
  });
  it('esgotado com 0 ou negativo', () => {
    expect(labelFromSeatsAvailable('open', 0)).toBe('esgotado');
    expect(labelFromSeatsAvailable('open', -1)).toBe('esgotado');
  });
  it('quase esgotado com 1 ou 2', () => {
    expect(labelFromSeatsAvailable('open', 1)).toBe('quase_esgotado');
    expect(labelFromSeatsAvailable('open', 2)).toBe('quase_esgotado');
  });
  it('disponível acima do limiar', () => {
    expect(labelFromSeatsAvailable('open', 3)).toBe('disponivel');
  });
  it('bate com availabilityLabel para o mesmo cenário', () => {
    const reservations = [res({ participantsCount: 4 })];
    expect(availabilityLabel('open', 6, reservations, now)).toBe(labelFromSeatsAvailable('open', seatsAvailable(6, reservations, now)));
  });
});

describe('isSessionInPast', () => {
  it('rejeita sessão exatamente agora ou no passado', () => {
    expect(isSessionInPast(now, now)).toBe(true);
    expect(isSessionInPast(new Date(now.getTime() - 1), now)).toBe(true);
  });

  it('aceita sessão no futuro', () => {
    expect(isSessionInPast(new Date(now.getTime() + 1), now)).toBe(false);
  });
});

describe('computeHoldExpiry', () => {
  it(`expira ${HOLD_DURATION_MINUTES} minutos à frente`, () => {
    const expiry = computeHoldExpiry(now);
    expect(expiry.getTime() - now.getTime()).toBe(HOLD_DURATION_MINUTES * 60_000);
  });
});
