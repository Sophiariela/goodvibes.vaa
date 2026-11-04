# Setup — sistema de reservas

Passo a passo para configurar as três contas externas necessárias. Nenhum
código roda de verdade sem isso — são pré-requisitos, não opcionais.

## 1. Supabase

1. Crie uma conta em [supabase.com](https://supabase.com) e um novo projeto
   (plano gratuito serve para começar).
2. Escolha uma região próxima do Brasil (ex.: `sa-east-1`, São Paulo) para
   reduzir latência.
3. Guarde a senha do banco gerada na criação — você vai precisar dela para
   montar a connection string.
4. Em **Project Settings → API**, copie:
   - `Project URL` → vai em `SUPABASE_URL`
   - `service_role` key (na aba "Project API keys", **não** a `anon`) →
     vai em `SUPABASE_SERVICE_ROLE_KEY`. Essa chave dá acesso total ao
     banco — trate como senha, nunca cole em chat, print ou código
     commitado.
5. Em **Project Settings → Database → Connection string**, copie a URI no
   formato "URI" (não "Session pooler" nem "Transaction pooler" — a
   aplicação precisa de conexão direta para transações com
   `SELECT ... FOR UPDATE`) → vai em `SUPABASE_DB_URL`.
6. Rode `db/schema.sql` no **SQL Editor** do painel do Supabase (cole o
   conteúdo do arquivo e execute) para criar as tabelas.

## 2. Mercado Pago

1. Crie (ou use) uma conta Mercado Pago em nome do clube, com dados
   bancários reais para receber os valores dos passeios.
2. Acesse [developers.mercadopago.com](https://www.mercadopago.com.br/developers/panel) → **Suas integrações** → crie uma aplicação.
3. Comece pelas **Credenciais de teste** (sandbox) — é com elas que eu vou
   integrar e testar primeiro, sem movimentar dinheiro real:
   - `Access Token` de teste → vai em `MP_ACCESS_TOKEN`
4. Configure o **Webhook** da aplicação apontando para
   `https://<seu-domínio>/api/webhooks/mercadopago` (em teste local, use
   uma URL temporária tipo `ngrok`/`vercel dev --listen`). O Mercado Pago
   mostra uma **chave secreta de assinatura** ao criar o webhook → vai em
   `MP_WEBHOOK_SECRET`.
5. Só depois que o fluxo completo for validado com pagamentos de teste
   (Pix simulado do ambiente sandbox), trocamos `MP_ACCESS_TOKEN` pela
   credencial de **produção** — nunca antes disso.

## 3. Vercel

As env vars podem ser configuradas de duas formas:

- **Você mesma, pelo painel**: Project Settings → Environment Variables,
  cole cada valor de `.env.example` (nunca comite `.env.local`).
- **Por mim, via CLI**: me passe os valores e eu rodo
  `vercel env add <NOME>` para cada um (já tenho a CLI conectada ao
  projeto `goodvibes.vaa`). Se preferir não compartilhar as chaves comigo
  diretamente, use a primeira opção.

Depois de configurar, um novo deploy é necessário para as funções em
`/api` lerem as variáveis (`git push` já dispara isso automaticamente, como
já configurado).

## 4. Rodando localmente

```bash
npm install
cp .env.example .env.local   # preencha com os valores de teste
vercel dev                    # serve o site estático + as funções /api juntos
```

## 5. Dados que faltam cadastrar no banco (antes de trocar para "live")

O site (`src/assets/js/booking.js`) já fala o protocolo real da API — ele só
precisa que as linhas abaixo existam em `experiences`/`sessions` pra cada
jornada funcionar. Sem isso, trocar `SITE["booking_mode"]` pra `"live"`
deixa as três abas de agendamento sem nenhum cartão (não quebra, só fica
vazio — ver `T.no_dates`).

**Importante**: os `slug` abaixo precisam bater exatamente com os `id` que
já existem em `booking_content.py` (`DEMO_EXPERIENCES`/`TRAINING_SCHEDULE`)
— é assim que o front sabe qual experiência buscar em
`/api/availability?experience=<slug>`.

### Experimentar (`pricing_mode = 'fixed'`, Pix automático)

| slug | nome | preço sugerido (ilustrativo) |
|---|---|---|
| `primeira` | Primeira experiência | R$ 100 |
| `nascer` | Nascer do sol | R$ 120 |
| `por` | Pôr do sol | R$ 120 |
| `turismo` | Turismo náutico | R$ 150 |

Pra cada uma, além da linha em `experiences`, criar as linhas em `sessions`
com `starts_at` real (data/hora de cada saída) e `capacity` — é isso que
preenche o calendário.

### Treinar (`pricing_mode = 'quote'`, sem Pix — `/api/requests` confirma direto)

Cronograma atualmente ilustrativo (gerado com seed fixa em
`booking_content.py`, `_generate_training_schedule` — troque pelos horários
reais do clube quando definidos; os `slug` abaixo são só os que existem
*hoje*, mudam se a função for editada):

| slug | nome | dia da semana | hora | capacidade | instrutor |
|---|---|---|---|---|---|
| `treino-0` | Treino regular | domingo | 07:00 | 8 | Nala |
| `treino-1` | Técnica de remada | terça, quinta | 18:00 | 10 | Nala |
| `treino-2` | Condicionamento físico | segunda, quarta, sexta | 06:00 | 10 | Jesse |
| `treino-3` | Treino de resistência | sábado | 08:00 | 6 | Jesse |

Como são turmas recorrentes, o ideal é um job/seed que recria as linhas de
`sessions` toda semana (fora do escopo deste build — hoje é cadastro
manual). Cada reserva de Treinar trava uma vaga real na sessão
(`createDirectRequest` em `lib/reservations.ts`) e confirma na hora, sem
cobrança.

### Particular (`pricing_mode = 'quote'`, sem sessão fixa)

| slug | nome |
|---|---|
| `particular` | Experiência particular / grupos / eventos |

Só uma linha em `experiences` (sem `sessions` — é sempre pedido de
orçamento, `POST /api/requests` com `journey: 'particular'`).

### Novo endpoint: `POST /api/requests`

Cobre Treinar e Particular (ver `api/requests.ts`) — nunca gera cobrança.
Treinar trava a vaga na sessão e já confirma (`status: 'confirmed'`);
Particular grava um pedido de orçamento (`status: 'quote_requested'`) pra
equipe responder por fora com o valor.

### Novo endpoint: `POST /api/subscribers` — pop-up de newsletter

Sem seed necessário — a tabela `subscribers` (ver `db/schema.sql`) já está
pronta assim que `SUPABASE_DB_URL` existir. O pop-up (`src/assets/js/
newsletter.js`) funciona em qualquer `booking_mode`, inclusive `"off"`.

## 6. Administração — como gerenciar cada parte hoje

| O que | Como administrar hoje |
|---|---|
| Produtos, fotos, preços, categorias, tamanhos/cores, estoque | Editar `products.py` (na raiz do projeto) e rodar `python3 build.py` — mesmo padrão de `PHOTOS`/`MODALITIES`. Nunca inventar preço/estoque: usar `None`/`"unknown"` até confirmar. |
| Campanha do pop-up (ligar/desligar, trocar texto) | Editar `CAMPAIGN` em `newsletter_content.py` — ver aviso sobre `type: "raffle"` lá dentro antes de mexer. |
| E-mails cadastrados e consentimentos | **Supabase → Table Editor → `subscribers`** — já vem com busca, filtro e exportação prontos, sem precisar de um painel próprio. Nunca expor esses dados fora do painel do Supabase (acesso restrito à equipe do clube). |
| Reservas e solicitações | Mesma tabela `reservations`/`payments` já documentada acima — idem, via Table Editor do Supabase. |

Um painel administrativo dedicado (fora do Supabase) é um upgrade futuro —
não foi construído nesta etapa porque exigiria autenticação própria, o que
é um projeto à parte e mais arriscado de apressar.

## O que eu preciso que você me confirme, além das credenciais

- Preço por participante de cada tipo de experiência em "Experimentar"
  (primeira experiência, nascer do sol, pôr do sol, turismo náutico).
- Horários fixos oferecidos (dias da semana + hora) para eu cadastrar as
  primeiras sessões de Experimentar e Treinar (o cronograma de Treinar
  hoje é ilustrativo — ver seção 5 acima).
- Preços dos planos de "Treinar" e como o Gympass/TotalPass deve aparecer
  no fluxo (eles não pagam Pix).
- Confirmação do modelo de orçamento→pagamento para "Particular" (descrito
  no plano de arquitetura).
