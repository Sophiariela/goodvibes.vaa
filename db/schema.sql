-- ============================================================================
-- Good Vibes Va'a — schema do sistema de reservas
-- Supabase Postgres. Rodar no SQL Editor do projeto (ou via `psql`/migration).
--
-- Decisões importantes:
--   * Nenhuma política de RLS pública é criada. Toda a aplicação acessa o
--     banco pela service role (dentro das funções serverless da Vercel),
--     que ignora RLS por padrão no Supabase. Não há cliente anônimo falando
--     direto com o banco.
--   * Disponibilidade nunca é um contador armazenado — é sempre calculada a
--     partir das reservas (`session_availability`, no fim do arquivo), para
--     nunca dessincronizar. A trava de concorrência de verdade acontece em
--     `SELECT ... FOR UPDATE` dentro da transação que cria a reserva (ver
--     docs/SETUP.md e api/reservations/create.ts), não aqui no schema.
--   * Datas de sessão ficam em `timestamptz` (UTC no banco); a conversão
--     para o fuso de Salvador (America/Bahia, UTC-3, sem horário de verão)
--     acontece na camada de API/frontend.
-- ============================================================================

create extension if not exists pgcrypto; -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- experiences — catálogo: um registro por tipo de jornada/produto vendável
-- ---------------------------------------------------------------------------
create table if not exists experiences (
  id               uuid primary key default gen_random_uuid(),
  journey          text not null check (journey in ('experimentar', 'treinar', 'particular')),
  slug             text not null unique,
  name_pt          text not null,
  name_en          text not null,
  description_pt   text,
  description_en   text,
  capacity_default integer not null default 6 check (capacity_default > 0),
  price_cents      integer check (price_cents is null or price_cents >= 0),
  pricing_mode     text not null check (pricing_mode in ('fixed', 'quote')),
  active           boolean not null default true,
  created_at       timestamptz not null default now()
);

comment on table experiences is 'Catálogo de produtos reserváveis. pricing_mode=quote (ex.: Particular) não tem price_cents fixo — o valor é definido por reserva em reservations.total_price_cents.';

-- ---------------------------------------------------------------------------
-- sessions — instâncias com data/hora e capacidade real (passeios e turmas)
-- ---------------------------------------------------------------------------
create table if not exists sessions (
  id            uuid primary key default gen_random_uuid(),
  experience_id uuid not null references experiences(id) on delete restrict,
  starts_at     timestamptz not null,
  capacity      integer not null check (capacity > 0),
  status        text not null default 'open' check (status in ('open', 'cancelled')),
  created_by    text,
  created_at    timestamptz not null default now()
);

create index if not exists idx_sessions_experience_starts on sessions (experience_id, starts_at);

comment on table sessions is 'Status "low"/"full"/"esgotado" são derivados na view session_availability, não armazenados aqui — só "open" (normal) e "cancelled" (cancelado pelo admin) são estados reais.';

-- ---------------------------------------------------------------------------
-- reservations
-- ---------------------------------------------------------------------------
create table if not exists reservations (
  id                 uuid primary key default gen_random_uuid(),
  session_id         uuid references sessions(id) on delete restrict,
  experience_id      uuid not null references experiences(id) on delete restrict,
  journey            text not null check (journey in ('experimentar', 'treinar', 'particular')),
  status             text not null default 'pending_payment' check (status in (
                        'quote_requested',  -- Particular: orçamento pedido, sem valor ainda
                        'quote_sent',       -- Particular: equipe definiu o valor, aguardando pagamento
                        'pending_payment',  -- vaga segurada (hold), aguardando confirmação do Pix
                        'confirmed',        -- pagamento aprovado e validado no servidor
                        'expired',          -- hold venceu sem pagamento
                        'cancelled',        -- cancelada (cliente ou admin)
                        'rejected'          -- pagamento rejeitado pela Mercado Pago
                      )),
  participants_count integer not null check (participants_count > 0),
  total_price_cents  integer check (total_price_cents is null or total_price_cents >= 0),
  hold_expires_at    timestamptz,
  locale             text not null check (locale in ('pt', 'en')),
  contact_name       text not null,
  contact_phone      text,
  contact_email      text,
  terms_accepted_at  timestamptz,
  notes              text,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index if not exists idx_reservations_session_status on reservations (session_id, status);
create index if not exists idx_reservations_experience_status on reservations (experience_id, status);

comment on column reservations.session_id is 'Nulo para reservas "particular" ainda em fase de orçamento (antes de uma data ser fechada).';

-- ---------------------------------------------------------------------------
-- participants
-- ---------------------------------------------------------------------------
create table if not exists participants (
  id             uuid primary key default gen_random_uuid(),
  reservation_id uuid not null references reservations(id) on delete cascade,
  full_name      text not null,
  is_minor       boolean not null default false,
  birth_date     date,
  notes          text
);

create index if not exists idx_participants_reservation on participants (reservation_id);

-- ---------------------------------------------------------------------------
-- payments
-- ---------------------------------------------------------------------------
create table if not exists payments (
  id                  uuid primary key default gen_random_uuid(),
  reservation_id      uuid not null references reservations(id) on delete cascade,
  provider            text not null default 'mercadopago',
  provider_payment_id text,
  status              text not null default 'pending',
  amount_cents        integer not null check (amount_cents >= 0),
  qr_code             text,
  qr_code_base64      text,
  expires_at          timestamptz,
  raw_last_status     jsonb,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create unique index if not exists uq_payments_provider_payment_id
  on payments (provider, provider_payment_id)
  where provider_payment_id is not null;
create index if not exists idx_payments_reservation on payments (reservation_id);

-- ---------------------------------------------------------------------------
-- webhook_events — auditoria + idempotência das notificações recebidas
-- ---------------------------------------------------------------------------
create table if not exists webhook_events (
  id           uuid primary key default gen_random_uuid(),
  provider     text not null,
  event_id     text not null,
  payload      jsonb,
  processed_at timestamptz,
  status       text not null default 'received' check (status in ('received', 'processed', 'ignored', 'error')),
  error        text,
  created_at   timestamptz not null default now()
);

create unique index if not exists uq_webhook_events_provider_event
  on webhook_events (provider, event_id);

-- ---------------------------------------------------------------------------
-- updated_at automático
-- ---------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_reservations_updated_at on reservations;
create trigger trg_reservations_updated_at
  before update on reservations
  for each row execute function set_updated_at();

drop trigger if exists trg_payments_updated_at on payments;
create trigger trg_payments_updated_at
  before update on payments
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- Segurança: RLS habilitado, sem policies (deny-all para anon/authenticated;
-- service_role sempre ignora RLS no Supabase, então a aplicação continua
-- funcionando normalmente através das funções serverless).
-- ---------------------------------------------------------------------------
alter table experiences     enable row level security;
alter table sessions        enable row level security;
alter table reservations    enable row level security;
alter table participants    enable row level security;
alter table payments        enable row level security;
alter table webhook_events  enable row level security;

-- ---------------------------------------------------------------------------
-- session_availability — view de leitura. NÃO usar para decidir se uma
-- reserva cabe (há uma corrida entre ler a view e inserir a reserva) — a
-- checagem que previne overbooking de verdade é feita dentro da transação
-- de criação da reserva, com `SELECT ... FOR UPDATE` na linha da sessão.
-- Esta view serve para listar horários/vagas na tela e no admin.
-- ---------------------------------------------------------------------------
create or replace view session_availability as
select
  s.id as session_id,
  s.experience_id,
  s.starts_at,
  s.capacity,
  s.status as session_status,
  coalesce(sum(r.participants_count) filter (
    where r.status = 'confirmed'
       or (r.status = 'pending_payment' and r.hold_expires_at > now())
  ), 0)::integer as seats_taken,
  (s.capacity - coalesce(sum(r.participants_count) filter (
    where r.status = 'confirmed'
       or (r.status = 'pending_payment' and r.hold_expires_at > now())
  ), 0))::integer as seats_available
from sessions s
left join reservations r on r.session_id = s.id
group by s.id;

comment on view session_availability is 'seats_available <= 0 => esgotado; seats_available entre 1 e 2 => "quase esgotado" (regra de UI, não armazenada); session_status=cancelled => sempre tratar como indisponível independente de seats_available.';
