/**
 * Tipos mínimos para as funções serverless da Vercel (pasta /api), sem
 * depender do pacote @vercel/node — que no momento traz várias
 * vulnerabilidades transitivas (fastify/busboy, undici, ajv, path-to-regexp)
 * só para alguns tipos de IDE. O runtime da Vercel já injeta `query`,
 * `body`, `.status()`, `.json()` etc. nos objetos nativos do Node
 * (IncomingMessage/ServerResponse) independente de importarmos o pacote —
 * estes tipos só descrevem essa forma pro TypeScript.
 */

import type { IncomingMessage, ServerResponse } from 'node:http';

export interface VercelRequest extends IncomingMessage {
  query: Partial<Record<string, string | string[]>>;
  cookies: Partial<Record<string, string>>;
  body: any;
}

export interface VercelResponse extends ServerResponse {
  status(code: number): VercelResponse;
  json(body: unknown): VercelResponse;
  send(body: unknown): VercelResponse;
}

export type Handler = (req: VercelRequest, res: VercelResponse) => Promise<void> | void;

export function methodNotAllowed(res: VercelResponse, allowed: string[]): void {
  res.setHeader('Allow', allowed.join(', '));
  res.status(405).json({ error: 'method_not_allowed' });
}

export function requireMethod(req: VercelRequest, res: VercelResponse, method: string): boolean {
  if (req.method !== method) {
    methodNotAllowed(res, [method]);
    return false;
  }
  return true;
}
