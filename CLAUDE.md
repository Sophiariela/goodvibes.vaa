# Good Vibes Va'a — guia para trabalhar neste repositório

Site estático (Python → HTML/CSS/JS puro, sem framework) do clube de canoa
havaiana Good Vibes Va'a. Ver README.md para visão geral, stack e deploy.

## Fotos (`PHOTOS` em build.py)

Todo espaço de foto do site é uma entrada no dicionário `PHOTOS`, perto do
topo do `build.py`:

```python
PHOTOS = {
    "hero": {
        "file": "hero.jpg",
        "alt_pt": "...",
        "alt_en": "...",
        "focus": "center",
    },
    ...
}
```

- **Trocar uma foto** = editar `file` (e `alt_pt`/`alt_en` se a cena mudou)
  de uma entrada. Nada mais no resto do código precisa mudar.
- **`focus`** é o `object-position` CSS da foto dentro do quadro (ver
  `.media img` em `site.css`, que lê `var(--focus, center)`). Só ajuste
  quando o enquadramento padrão ("center") cortar um rosto ou detalhe
  importante — é inline por imagem (`style="--focus:..."`), nunca afeta
  outras fotos.
- A função `media(photo_key, locale, slot, prefix, ...)` em `build.py` é o
  único lugar que lê `PHOTOS` e gera o `<figure><img>`. Se o arquivo
  referenciado não existir em `src/assets/img/`, o `<img>` se remove
  sozinho (`onerror`) e o `data-slot` mostra a descrição do que falta.
- Arquivo que deixar de ser referenciado em `PHOTOS` deve ser removido de
  `src/assets/img/` (e `dist/assets/img/` no próximo build) — não deixar
  fotos órfãs no projeto.
- `logo.png` (marca no header/footer) e `og.jpg` (compartilhamento, só em
  meta tag) ficam fora de `PHOTOS` de propósito — não passam pelo
  componente `media()`.

## Paleta (site inteiro)

O site usa **somente** as dez cores oficiais do clube, declaradas como
paleta crua no topo do `site.css`: Forest `#123D2B`, Forest escuro
`#0C2A1E`, Ivory `#F4F0E6`, Ivory 2 `#EAE4D4`, Ocean `#147B91`, Ocean
escuro `#0F5F70`, Sand `#D5A83C`, Sand escuro `#C2952B`, Charcoal
`#202B28`, Stone `#5E6863`. **Nenhum branco puro e nenhum azul-céu** —
cartões e superfícies claras são Ivory, e todo tom intermediário sai de
transparência sobre essas cores, nunca de um hex novo.

Três exceções são funcionais, não decorativas, e não devem ser
"corrigidas": `--c-bad` (erro de formulário precisa ler como erro), o
verde `#25D366` do WhatsApp (marca de terceiro) e o fundo branco real do
QR do Pix (leitor de QR exige branco).

Regras de contraste que já custaram medição (ver `tools/audit.mjs`, que
reprova abaixo de 4.5:1):

- Texto sobre Sand é sempre Charcoal.
- Ocean puro como texto de 11–13px sobre Ivory dá 4.32:1 e **reprova**.
  O acento de texto em contexto claro é Ocean escuro (`--c-gold-ink`,
  6.5:1); sobre fundo escuro o acento volta a ser Sand (5.2:1).
- O anel de foco é o token `--focus-ring`: Ocean escuro no claro, Sand no
  escuro. Sand sobre Ivory daria 2.3:1, abaixo dos 3:1 que o WCAG pede
  para indicador de foco. Todo bloco escuro que não usa `.band-dark`
  (`.hero`, `.header`, `.mobile-nav`, `.footer`, `.shop-teaser-panel`,
  `.bk-modal-head`) redeclara `--focus-ring` para Sand.

## Home — ordem das seções

```
menu → hero → faixa de credibilidade → "O que oferecemos" → quadro de
reservas → "Por que remar com a gente" → comunidade e capitães →
chamada da loja → local e mapa → dúvidas → chamada final → rodapé
```

A ordem é definida pelo `body` da `render()` — ver README § "Home". Os
quatro cartões de "O que oferecemos" apontam para as âncoras das jornadas
e o `initTabs` abre a aba certa; o pop-up de newsletter **não** aparece na
home (`page_footer()` só emite o `div.nl-widget` fora dela).

## Navegação e rodapé

A navegação inteira vive num **painel lateral (menu hambúrguer) em todas as
larguras** — não existe mais barra horizontal de links no desktop. Os seis
itens saem de `CONTENT[...]["nav"]`, lidos pelo menu E pelo rodapé:
item começando com `#` é âncora da home, qualquer outro valor é slug de
rota (ver `nav_href()`).

- O painel nasce com `inert` no HTML e `initMenu()` (site.js) tira/põe o
  atributo. **Sem JS ele continua inalcançável e a navegação da página é a
  do rodapé** — que lista os mesmos seis itens de propósito.
- `visibility` na transição do painel usa `0s linear .34s` ao fechar e
  `0s` ao abrir. Com a duração igual à do `transform`, o elemento ainda
  conta como invisível no instante em que o painel abre e `.focus()` não
  pega — o foco ficaria no botão, atrás do overlay. Não unificar.
- O rodapé **não mostra telefone em lugar nenhum**: atendimento passa pela
  página `/contato/`. O Instagram é só o ícone (alvo de 52px, rótulo no
  `aria-label`), nunca o endereço escrito. O crédito da Aster
  (`asterops.co`) fica na barra inferior.

## Contato (`/contato`) e `POST /api/contact`

O formulário grava em `contact_messages` (ver `lib/contact.ts`) — **o site
não dispara e-mail**. Isso é decisão, não pendência: sem endereço oficial
do clube e sem provedor contratado, inventar credencial seria mentira.
Quando houver, somar o envio a `saveContactMessage` não muda o contrato da
API nem o formulário.

**Regra crítica: o formulário nunca mostra sucesso sem o servidor ter
confirmado.** Sem `SUPABASE_DB_URL` o endpoint responde 503 e a tela diz
que o canal ainda não está ativo, apontando o WhatsApp ao lado. A lista de
assuntos aceitos (`CONTACT_SUBJECTS` em `lib/contact.ts`) espelha
`ct_subjects` em `build.py` — mudar um lado sem o outro quebra o envio.

## Páginas institucionais (`legal_content.py`)

Quatro documentos (privacidade, termos, diretrizes, reservas) saem do mesmo
`render_legal()`. Cada um tem `draft`: enquanto `True`, a página mostra
aviso de rascunho, recebe `noindex` e **fica fora do sitemap** — existe e é
navegável, mas nunca se apresenta como política em vigor. Seções marcadas
com `pendente=True` descrevem o que falta decidir e ganham a etiqueta "a
definir"; **nunca transformar um pendente em regra sem o clube confirmar** —
prazo de cancelamento, reembolso, uso de imagem e foro têm efeito jurídico
e comercial real.

## Loja (`/produtos`)

As categorias dos chips de filtro saem de `products.py` (nenhuma inventada)
e o filtro só esconde cartão. Os cartões "Em breve" são **espaço vazio
reservado**, sem nome, preço ou disponibilidade — não preencher com peça
fictícia. A loja não tem checkout: a compra passa pelo WhatsApp.

## Build

`python3 build.py` gera `dist/` a partir de `CONTENT['pt']`/`CONTENT['en']`
(texto) e `PHOTOS` (fotos). Rodar depois de qualquer mudança em `build.py`
ou nos arquivos de `src/`. Nunca editar `dist/` diretamente — é gerado.

## Reserva no site (`SITE["booking_mode"]`)

**⚠️ Regra crítica: nunca publicar/divulgar o site com `booking_mode =
"demo"`.** Demo é só para apresentação — experiências, vagas e preços são
fictícios (`booking_content.py`), "Simular pagamento aprovado" confirma sem
cobrar nada de verdade. Antes de divulgar o link publicamente, trocar para
`"off"` (volta ao WhatsApp) ou `"live"` (backend real em `SITE["api_base"]`
— ver seção de backend abaixo). Hoje o repositório está em `"off"`: as três
jornadas voltam ao formulário que abre o WhatsApp com a solicitação pronta.

- `src/assets/js/booking.js` — sistema único (calendário + cartões + modal)
  reaproveitado pelas três jornadas. `initBooking()` roda uma instância por
  `[data-booking][data-modality]` (`build.py` renderiza um desses em cada
  painel quando `booking_mode != "off"`). `initModality()` lê `modality.flow`
  (`calendar+pix` | `calendar+request` | `quote`, de `MODALITIES` em
  `booking_content.py`) pra decidir que passos o modal mostra — participantes
  → termo → Pix → confirmação (Experimentar); contato → confirmação direta
  sem cobrança (Treinar, trava vaga real na hora); orçamento → confirmação
  (Particular, sem calendário). `demoApi()`/`liveApi()` são os únicos pontos
  que sabem a diferença entre dado ilustrativo e o contrato real de
  `/api/availability`, `/api/reservations/create` e `/api/requests` — o
  resto do componente (render, validação, modal) é o mesmo nos dois modos.
  Lê `GVV_CONFIG` (`bookingMode`, `apiBase`, `seats`) e `I18N.bk`/
  `I18N.modalities` do `<script id="i18n">` (`modalities` já vem com a URL
  da foto do instrutor resolvida por `resolve_modalities()` em `build.py`).
- `src/assets/js/wa-widget.js` — pop-up do WhatsApp, abre automaticamente
  uma vez por visita, **nunca enquanto algum `[data-booking]` está visível
  na tela** (checagem síncrona de geometria em `bookingOnScreen()`, feita
  contra TODOS os `[data-booking]` da página — há um por jornada agora —
  não só `IntersectionObserver` — evita corrida entre o gatilho "saiu do
  hero" e o observer do cartão ainda não ter processado a posição nova).
- `build.py`: `contact_fields()`/formulário simples só existem mais no modo
  `"off"` (WhatsApp direto); em `"demo"`/`"live"` as três jornadas renderizam
  o mesmo `<div class="bk" data-booking data-modality="...">`. `form_shell()`
  troca o texto de privacidade e remove o ícone do WhatsApp do botão quando
  o envio não é mais necessariamente uma conversa de WhatsApp.
- Backend "live" para Treinar/Particular: `POST /api/requests` (não usa Pix)
  → `lib/reservations.ts`, `createDirectRequest()` — trava vaga real numa
  sessão pra Treinar (mesma lógica de `SELECT ... FOR UPDATE` de
  Experimentar, só que confirma direto); grava pedido de orçamento sem
  sessão pra Particular. Exige linhas em `experiences`/`sessions` cujo
  `slug` bate com os `id` de `MODALITIES` — ver `docs/SETUP.md` § 5.
- Todo texto novo (passos, erros, Pix, cartões, pop-up) vem de
  `booking_content.py` (`BOOKING`, `WA_WIDGET`, `MODALITIES`), importado por
  `build.py` e mesclado em `CONTENT[locale]["i18n"]` — mesmo padrão de
  sempre, nunca texto solto em JS. `MODALITIES["treinar"]` vem de
  `_generate_training_schedule()`, com seed fixa (`random.Random(7)`) —
  estável entre builds, troque pelos horários reais quando o clube
  confirmar.

## Backend de reservas (live)

Ver README.md § "Backend de reservas" e `docs/SETUP.md`. Em desenvolvimento,
ainda sem credenciais reais configuradas — nenhum endpoint `/api` deve ser
anunciado como funcional antes de testado contra Supabase/Mercado Pago de
verdade.

**Imports em `api/**/*.ts` e `lib/*.ts` precisam da extensão `.js` nos
caminhos relativos** (`from '../lib/db.js'`, nunca `'../lib/db'`) — o
runtime Node/ESM da Vercel (`"type": "module"` no `package.json`) exige
isso; TypeScript e Vitest toleram sem a extensão, então esse tipo de erro
só aparece em produção (`FUNCTION_INVOCATION_FAILED` nos logs) — já
aconteceu uma vez nesse projeto, ver histórico do commit que corrigiu.

## Loja (`/produtos`) e pop-up de newsletter

Ver README.md § "Loja" e § "Pop-up de newsletter" para a visão geral. Pontos
que não são óbvios lendo só o código:

- `products.py`, `newsletter_content.py` seguem o mesmo padrão de
  `booking_content.py`/`PHOTOS` — conteúdo editável em Python, nunca texto
  solto em JS ou HTML hardcoded.
- `page_header()`/`page_footer()`/`page_scripts()`/`nav_items_html()`/
  `lang_switch_html()` em `build.py` são compartilhados entre `render()`
  (home), `render_produtos()` e `render_privacy()` — qualquer mudança de
  header/rodapé/nav deve passar por essas funções, não duplicar markup
  numa página só.
- **Dois overlays com atributo `hidden` sempre presentes no DOM**
  (`.pmodal-overlay`, `.nl-overlay`) **precisam da regra
  `[hidden] { display: none }` explícita no CSS** — `display: flex` na
  classe base tem a mesma especificidade do `[hidden]` da UA stylesheet e
  vence por ordem de cascata, deixando o overlay cobrindo (e bloqueando
  cliques em) a página inteira mesmo "escondido". Já causou um bug real
  nesta etapa (pop-up de newsletter bloqueando a home inteira assim que o
  JS rodava) — testado e corrigido; não remover essas duas regras.
- `resolve_campaign()` em `build.py` é a única porta de saída de
  `CAMPAIGN` pro JS — bloqueia `type: "raffle"` sem `legal_cleared: True`
  mesmo que alguém esqueça de checar isso na hora de editar
  `newsletter_content.py`. Não remover essa checagem nem replicar a lógica
  de campanha em outro lugar.
- `api/subscribers.ts`: proteção contra spam é honeypot + tempo mínimo de
  preenchimento, de propósito sem IP (minimização de dados, ver
  `/privacidade/`). Duplicata de e-mail nunca é erro — é
  `status: 'already_subscribed'`, 200.
