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

## O que eu preciso que você me confirme, além das credenciais

- Preço por participante de cada tipo de experiência em "Experimentar"
  (primeira experiência, nascer do sol, pôr do sol, turismo náutico).
- Horários fixos oferecidos (dias da semana + hora) para eu cadastrar as
  primeiras sessões.
- Preços dos planos de "Treinar" e como o Gympass/TotalPass deve aparecer
  no fluxo (eles não pagam Pix).
- Confirmação do modelo de orçamento→pagamento para "Particular" (descrito
  no plano de arquitetura).
