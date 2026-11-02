/**
 * Validação de assinatura de webhooks do Mercado Pago.
 *
 * Referência: https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/additional-content/notifications/webhooks#editor_5
 * O Mercado Pago envia dois headers na notificação:
 *   x-signature:   "ts=1704908010,v1=618c85345248dd820d9c0..."
 *   x-request-id:  "d1f0b1b0-..."
 * E o corpo (ou query string, dependendo do tipo de notificação) traz
 * `data.id` com o id do recurso (ex.: id do pagamento).
 *
 * O "manifesto" assinado é a string literal:
 *   id:{data.id};request-id:{x-request-id};ts:{ts};
 * (id em minúsculas quando alfanumérico — payments usa id numérico, mas a
 * doc recomenda lowercase defensivamente). HMAC-SHA256 desse manifesto com
 * o segredo do webhook deve bater com o `v1` do header, comparado em tempo
 * constante.
 *
 * IMPORTANTE: esta implementação foi escrita a partir da documentação
 * oficial, mas ainda não foi validada contra uma notificação real do
 * Mercado Pago (preciso das credenciais de teste + um webhook configurado
 * para isso — ver docs/SETUP.md). Antes de confiar nisso em produção,
 * preciso reproduzir uma notificação de teste de verdade e confirmar que a
 * assinatura bate.
 */

import { createHmac, timingSafeEqual } from 'node:crypto';

export interface ParsedSignatureHeader {
  ts: string;
  v1: string;
}

export function parseSignatureHeader(xSignature: string): ParsedSignatureHeader | null {
  const parts = Object.fromEntries(
    xSignature
      .split(',')
      .map((p) => p.trim())
      .filter(Boolean)
      .map((p) => {
        const idx = p.indexOf('=');
        return [p.slice(0, idx).trim(), p.slice(idx + 1).trim()];
      }),
  );
  if (!parts.ts || !parts.v1) return null;
  return { ts: parts.ts, v1: parts.v1 };
}

export function buildSignatureManifest(dataId: string, requestId: string, ts: string): string {
  return `id:${dataId.toLowerCase()};request-id:${requestId};ts:${ts};`;
}

export interface VerifyWebhookSignatureInput {
  xSignature: string | null | undefined;
  xRequestId: string | null | undefined;
  dataId: string;
  secret: string;
}

export function verifyMercadoPagoSignature(input: VerifyWebhookSignatureInput): boolean {
  const { xSignature, xRequestId, dataId, secret } = input;
  if (!xSignature || !xRequestId || !secret) return false;

  const parsed = parseSignatureHeader(xSignature);
  if (!parsed) return false;

  const manifest = buildSignatureManifest(dataId, xRequestId, parsed.ts);
  const expected = createHmac('sha256', secret).update(manifest).digest('hex');

  const a = Buffer.from(expected, 'hex');
  const b = Buffer.from(parsed.v1, 'hex');
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
