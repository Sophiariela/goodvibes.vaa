/**
 * Cliente mínimo da API REST do Mercado Pago — sem o SDK oficial (pacote
 * `mercadopago`), usando `fetch` nativo do Node, pra não trazer dependência
 * de runtime extra só pra duas chamadas HTTP.
 *
 * IMPORTANTE: não testado contra a API real ainda (preciso de um Access
 * Token de teste — ver docs/SETUP.md). A forma dos campos (transaction_data,
 * point_of_interaction etc.) segue a documentação pública de "Pagamentos
 * Pix" da Mercado Pago; confirmar contra uma resposta real antes de confiar
 * cegamente em produção.
 */

const MP_API = 'https://api.mercadopago.com';

export class MercadoPagoError extends Error {
  constructor(message: string, public status: number, public body: string) {
    super(message);
    this.name = 'MercadoPagoError';
  }
}

export interface CreatePixPaymentInput {
  amountCents: number;
  description: string;
  payerEmail: string;
  /** Usado para casar o webhook com a nossa reserva (reservations.id). */
  externalReference: string;
  notificationUrl: string;
}

export interface PixPaymentResult {
  id: number;
  status: string;
  qrCode: string;
  qrCodeBase64: string;
  expiresAt: string | null;
  raw: unknown;
}

export async function createPixPayment(
  input: CreatePixPaymentInput,
  accessToken: string,
  idempotencyKey: string,
): Promise<PixPaymentResult> {
  const res = await fetch(`${MP_API}/v1/payments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Idempotency-Key': idempotencyKey,
    },
    body: JSON.stringify({
      transaction_amount: Math.round(input.amountCents) / 100,
      description: input.description,
      payment_method_id: 'pix',
      payer: { email: input.payerEmail },
      external_reference: input.externalReference,
      notification_url: input.notificationUrl,
    }),
  });

  const text = await res.text();
  if (!res.ok) {
    throw new MercadoPagoError(`Falha ao criar pagamento Pix (HTTP ${res.status})`, res.status, text);
  }

  const data = JSON.parse(text);
  const txData = data?.point_of_interaction?.transaction_data ?? {};
  return {
    id: data.id,
    status: data.status,
    qrCode: txData.qr_code ?? '',
    qrCodeBase64: txData.qr_code_base64 ?? '',
    expiresAt: data.date_of_expiration ?? null,
    raw: data,
  };
}

/** Sempre a fonte da verdade do status de um pagamento — nunca confiar só
 *  no corpo do webhook. */
export async function getPayment(paymentId: string | number, accessToken: string): Promise<any> {
  const res = await fetch(`${MP_API}/v1/payments/${paymentId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const text = await res.text();
  if (!res.ok) {
    throw new MercadoPagoError(`Falha ao consultar pagamento ${paymentId} (HTTP ${res.status})`, res.status, text);
  }
  return JSON.parse(text);
}
