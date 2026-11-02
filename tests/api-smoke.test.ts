import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { VercelRequest, VercelResponse } from '../lib/http';

/**
 * Testes de "fumaça": sem Supabase/Mercado Pago reais, o que dá pra
 * verificar de verdade é que os endpoints não quebram (exceção não
 * tratada, 500 genérico) quando as credenciais ainda não existem — devem
 * responder 503/405 de forma previsível. Isso NÃO substitui testar contra
 * credenciais de sandbox reais (ver docs/SETUP.md); é só a garantia de que
 * "sem configurar nada, o endpoint não derruba a função".
 */

function mockReqRes(overrides: Partial<VercelRequest> = {}) {
  const res: Partial<VercelResponse> = {
    statusCode: 200,
    headers: {},
    setHeader: vi.fn(),
  };
  res.status = vi.fn((code: number) => {
    (res as any).statusCode = code;
    return res as VercelResponse;
  });
  const jsonBody: { value: unknown } = { value: undefined };
  res.json = vi.fn((body: unknown) => {
    jsonBody.value = body;
    return res as VercelResponse;
  });
  const req: Partial<VercelRequest> = { method: 'POST', query: {}, body: {}, headers: {}, ...overrides };
  return { req: req as VercelRequest, res: res as VercelResponse, jsonBody };
}

beforeEach(() => {
  vi.resetModules();
  delete process.env.MP_ACCESS_TOKEN;
  delete process.env.MP_WEBHOOK_SECRET;
  delete process.env.PUBLIC_BASE_URL;
  delete process.env.SUPABASE_DB_URL;
});

describe('POST /api/reservations/create sem credenciais', () => {
  it('responde 503 server_not_configured em vez de quebrar', async () => {
    const { default: handler } = await import('../api/reservations/create');
    const { req, res, jsonBody } = mockReqRes({ method: 'POST', body: { sessionId: 'x' } });
    await handler(req, res);
    expect(res.status).toHaveBeenCalledWith(503);
    expect((jsonBody.value as any).error).toBe('server_not_configured');
  });

  it('rejeita método errado antes de tudo', async () => {
    const { default: handler } = await import('../api/reservations/create');
    const { req, res } = mockReqRes({ method: 'GET' });
    await handler(req, res);
    expect(res.status).toHaveBeenCalledWith(405);
  });
});

describe('POST /api/webhooks/mercadopago sem credenciais', () => {
  it('responde 503 em vez de tentar validar assinatura sem segredo', async () => {
    const { default: handler } = await import('../api/webhooks/mercadopago');
    const { req, res, jsonBody } = mockReqRes({ method: 'POST', body: { data: { id: '123' } } });
    await handler(req, res);
    expect(res.status).toHaveBeenCalledWith(503);
    expect((jsonBody.value as any).error).toBe('server_not_configured');
  });
});

describe('GET /api/availability', () => {
  it('responde 400 sem o parâmetro experience', async () => {
    const { default: handler } = await import('../api/availability');
    const { req, res, jsonBody } = mockReqRes({ method: 'GET', query: {} });
    await handler(req, res);
    expect(res.status).toHaveBeenCalledWith(400);
    expect((jsonBody.value as any).error).toBe('missing_experience');
  });

  it('rejeita método errado', async () => {
    const { default: handler } = await import('../api/availability');
    const { req, res } = mockReqRes({ method: 'POST', query: { experience: 'primeira' } });
    await handler(req, res);
    expect(res.status).toHaveBeenCalledWith(405);
  });
});
