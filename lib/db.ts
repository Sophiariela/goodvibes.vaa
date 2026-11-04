/**
 * Acesso ao Postgres do Supabase via conexão direta (não PostgREST), porque
 * a trava de concorrência que impede overbooking depende de uma transação
 * de verdade com `SELECT ... FOR UPDATE` (ver lib/reservations.ts) — algo
 * que a API REST automática do Supabase não expõe.
 *
 * `pg` é a única dependência de runtime deste projeto além do que o Node já
 * tem embutido — mantendo a filosofia "sem dependências" do site estático
 * na medida do que é tecnicamente necessário para fazer reservas seguras.
 */

import { Pool, type PoolClient } from 'pg';

/** Lançado quando SUPABASE_DB_URL não está configurada — distinto de um
 *  erro real de banco, pra endpoints responderem 503 "falta configurar"
 *  em vez de 500 "algo quebrou". */
export class DbNotConfiguredError extends Error {
  constructor() {
    super('SUPABASE_DB_URL não configurada — ver docs/SETUP.md.');
    this.name = 'DbNotConfiguredError';
  }
}

let pool: Pool | null = null;

function getPool(): Pool {
  if (pool) return pool;
  const connectionString = process.env.SUPABASE_DB_URL;
  if (!connectionString) {
    throw new DbNotConfiguredError();
  }
  pool = new Pool({
    connectionString,
    max: 5,
    idleTimeoutMillis: 10_000,
    connectionTimeoutMillis: 5_000,
    ssl: { rejectUnauthorized: true },
  });
  return pool;
}

/** Roda `fn` dentro de uma transação (BEGIN/COMMIT/ROLLBACK) com um único
 *  client dedicado — nunca misture isto com chamadas soltas a `query()`
 *  para a mesma operação lógica, ou o lock de linha não vale nada. */
export async function withTransaction<T>(fn: (client: PoolClient) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {});
    throw err;
  } finally {
    client.release();
  }
}

/** Query avulsa fora de transação — para leituras simples ou updates que não
 *  dependem de um lock prévio na mesma operação. */
export async function query<T extends Record<string, any> = any>(text: string, params?: unknown[]): Promise<T[]> {
  const res = await getPool().query(text, params);
  return res.rows as T[];
}
