/**
 * POST /api/webhooks/mercadopago
 *
 * 1. Valida a assinatura (x-signature / x-request-id) — recusa qualquer
 *    notificação que não prove que veio do Mercado Pago.
 * 2. Idempotência: se já processamos este evento exato, responde 200 sem
 *    reprocessar.
 * 3. Rebusca o pagamento DIRETO na API do Mercado Pago — nunca confia no
 *    corpo da notificação como fonte de verdade de status/valor.
 * 4. Só confirma a reserva se o pagamento está 'approved' e o valor bate.
 * 5. Sempre responde 200 quando conseguiu processar (mesmo que a decisão
 *    de negócio tenha sido "não confirmar") — isso evita retry infinito do
 *    Mercado Pago. Erros de verdade (assinatura inválida, payload sem
 *    data.id) retornam 4xx; falhas internas inesperadas retornam 200 com o
 *    erro registrado em webhook_events, para investigação manual — não
 *    queremos um erro transitório nosso virando reentrega infinita.
 *
 * IMPORTANTE: a forma exata do payload (data.id vs query string, nome das
 * actions) segue a documentação pública, mas só será validada de verdade
 * contra uma notificação real de sandbox quando houver credenciais de
 * teste — ver docs/SETUP.md e o aviso em lib/mercadopago-webhook.ts.
 */

import type { VercelRequest, VercelResponse } from '../../lib/http.js';
import { requireMethod } from '../../lib/http.js';
import { verifyMercadoPagoSignature } from '../../lib/mercadopago-webhook.js';
import { getPayment } from '../../lib/mercadopago.js';
import { applyPaymentStatus } from '../../lib/reservations.js';
import { query } from '../../lib/db.js';

function extractDataId(req: VercelRequest): string | null {
  const fromQuery = req.query['data.id'];
  if (typeof fromQuery === 'string' && fromQuery) return fromQuery;
  const fromBody = req.body?.data?.id;
  if (fromBody) return String(fromBody);
  // Formato antigo de IPN, só por garantia.
  const legacyId = req.query['id'];
  if (typeof legacyId === 'string' && req.query['topic'] === 'payment') return legacyId;
  return null;
}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!requireMethod(req, res, 'POST')) return;

  const secret = process.env.MP_WEBHOOK_SECRET;
  const accessToken = process.env.MP_ACCESS_TOKEN;
  if (!secret || !accessToken) {
    console.error('Webhook do Mercado Pago recebido sem MP_WEBHOOK_SECRET/MP_ACCESS_TOKEN configurados.');
    res.status(503).json({ error: 'server_not_configured' });
    return;
  }

  const dataId = extractDataId(req);
  if (!dataId) {
    res.status(400).json({ error: 'missing_data_id' });
    return;
  }

  const xSignature = req.headers['x-signature'];
  const xRequestId = req.headers['x-request-id'];
  const valid = verifyMercadoPagoSignature({
    xSignature: Array.isArray(xSignature) ? xSignature[0] : xSignature,
    xRequestId: Array.isArray(xRequestId) ? xRequestId[0] : xRequestId,
    dataId,
    secret,
  });
  if (!valid) {
    console.warn('Webhook do Mercado Pago com assinatura inválida, recusado.', { dataId });
    res.status(401).json({ error: 'invalid_signature' });
    return;
  }

  const action = typeof req.body?.action === 'string' ? req.body.action : 'unknown';
  const eventId = `${dataId}:${action}`;

  const existing = await query<{ status: string }>(
    `select status from webhook_events where provider = 'mercadopago' and event_id = $1`,
    [eventId],
  );
  if (existing[0]?.status === 'processed') {
    res.status(200).json({ status: 'already_processed' });
    return;
  }
  if (!existing[0]) {
    await query(
      `insert into webhook_events (provider, event_id, payload, status) values ('mercadopago', $1, $2, 'received')`,
      [eventId, JSON.stringify(req.body ?? {})],
    );
  }

  try {
    const payment = await getPayment(dataId, accessToken);
    const reservationId = payment.external_reference;
    if (!reservationId) {
      throw new Error(`Pagamento ${dataId} sem external_reference — não dá pra ligar a uma reserva.`);
    }

    const result = await applyPaymentStatus(reservationId, {
      id: payment.id,
      status: payment.status,
      transaction_amount: payment.transaction_amount,
    });

    await query(
      `update webhook_events set processed_at = now(), status = 'processed' where provider = 'mercadopago' and event_id = $1`,
      [eventId],
    );

    res.status(200).json({ status: 'ok', confirmed: result.confirmed, reason: 'reason' in result ? result.reason : undefined });
  } catch (err) {
    console.error('Erro processando webhook do Mercado Pago', { dataId, err });
    await query(
      `update webhook_events set status = 'error', error = $2 where provider = 'mercadopago' and event_id = $1`,
      [eventId, err instanceof Error ? err.message : String(err)],
    ).catch(() => {});
    // 200 proposital: erro já está registrado em webhook_events pra
    // reprocessamento manual; devolver 4xx/5xx aqui só faria a Mercado
    // Pago reentregar o mesmo evento indefinidamente.
    res.status(200).json({ status: 'error_logged' });
  }
}
