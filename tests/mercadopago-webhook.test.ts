import { describe, it, expect } from 'vitest';
import { createHmac } from 'node:crypto';
import {
  parseSignatureHeader,
  buildSignatureManifest,
  verifyMercadoPagoSignature,
} from '../lib/mercadopago-webhook';

/**
 * NOTA: estes são testes de auto-consistência (assino com o segredo e
 * confirmo que a mesma função valida) — garantem que a implementação do
 * algoritmo documentado está correta e que qualquer adulteração é
 * rejeitada. NÃO substituem validar contra uma notificação real do
 * Mercado Pago sandbox, que só posso fazer com credenciais de teste (ver
 * docs/SETUP.md). Marcar como "testado end-to-end" só depois disso.
 */

function sign(secret: string, dataId: string, requestId: string, ts: string): string {
  const manifest = buildSignatureManifest(dataId, requestId, ts);
  const v1 = createHmac('sha256', secret).update(manifest).digest('hex');
  return `ts=${ts},v1=${v1}`;
}

describe('parseSignatureHeader', () => {
  it('lê ts e v1 do header', () => {
    expect(parseSignatureHeader('ts=123,v1=abcdef')).toEqual({ ts: '123', v1: 'abcdef' });
  });

  it('tolera espaços ao redor dos pares', () => {
    expect(parseSignatureHeader('ts=123, v1=abcdef ')).toEqual({ ts: '123', v1: 'abcdef' });
  });

  it('retorna null se faltar ts ou v1', () => {
    expect(parseSignatureHeader('ts=123')).toBeNull();
    expect(parseSignatureHeader('v1=abcdef')).toBeNull();
    expect(parseSignatureHeader('')).toBeNull();
  });
});

describe('buildSignatureManifest', () => {
  it('monta o manifesto no formato documentado, id em minúsculas', () => {
    expect(buildSignatureManifest('ABC123', 'req-1', '1700000000')).toBe('id:abc123;request-id:req-1;ts:1700000000;');
  });
});

describe('verifyMercadoPagoSignature', () => {
  const secret = 'test-secret-do-clube';
  const dataId = '123456789';
  const requestId = 'req-abc-123';
  const ts = '1700000000';

  it('aceita uma assinatura válida', () => {
    const xSignature = sign(secret, dataId, requestId, ts);
    expect(verifyMercadoPagoSignature({ xSignature, xRequestId: requestId, dataId, secret })).toBe(true);
  });

  it('rejeita quando o segredo é diferente', () => {
    const xSignature = sign('outro-segredo', dataId, requestId, ts);
    expect(verifyMercadoPagoSignature({ xSignature, xRequestId: requestId, dataId, secret })).toBe(false);
  });

  it('rejeita quando o dataId foi adulterado após assinar', () => {
    const xSignature = sign(secret, dataId, requestId, ts);
    expect(verifyMercadoPagoSignature({ xSignature, xRequestId: requestId, dataId: '999999999', secret })).toBe(false);
  });

  it('rejeita quando o x-request-id não bate', () => {
    const xSignature = sign(secret, dataId, requestId, ts);
    expect(verifyMercadoPagoSignature({ xSignature, xRequestId: 'outro-id', dataId, secret })).toBe(false);
  });

  it('rejeita header ausente ou malformado', () => {
    expect(verifyMercadoPagoSignature({ xSignature: null, xRequestId: requestId, dataId, secret })).toBe(false);
    expect(verifyMercadoPagoSignature({ xSignature: 'lixo', xRequestId: requestId, dataId, secret })).toBe(false);
    expect(verifyMercadoPagoSignature({ xSignature: sign(secret, dataId, requestId, ts), xRequestId: null, dataId, secret })).toBe(false);
  });

  it('rejeita quando falta o segredo (nunca aceitar silenciosamente)', () => {
    const xSignature = sign(secret, dataId, requestId, ts);
    expect(verifyMercadoPagoSignature({ xSignature, xRequestId: requestId, dataId, secret: '' })).toBe(false);
  });
});
