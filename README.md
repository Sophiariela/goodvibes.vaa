# Good Vibes Va'a — site

Site institucional e de conversão do clube de canoa havaiana Good Vibes Va'a (Praia da Preguiça, Salvador).

## Stack e por quê

Site estático gerado por um script Python sem dependências. Uma landing page de uma marca local não precisa de framework, banco de dados ou build de JavaScript: HTML pronto carrega mais rápido, indexa melhor e pode ser hospedado de graça (Netlify, Cloudflare Pages, Vercel, GitHub Pages).

```
build.py                 conteúdo PT/EN + templates + geração do site
src/assets/css/site.css  design system (tokens, componentes, seções)
src/assets/js/site.js    navegação, formulários, ponto de integração
src/assets/fonts/        Archivo (texto/nav) + Fraunces (marca/títulos), auto-hospedadas (licença OFL)
src/assets/img/          fotos oficiais (ver lista abaixo)
dist/                    site pronto para publicar (gerado)
```

Para gerar: `python3 build.py`. Publique a pasta `dist/`.

### Deploy
Hospedado na Vercel, conectado a este repositório. Todo push na branch `main` dispara um deploy automático de produção.

### Idiomas e rotas
- Português em `/`, inglês em `/en/`. Cada idioma é uma página HTML completa, com `lang`, `canonical`, `hreflang`, Open Graph e JSON-LD próprios. Não há troca de texto por JavaScript.
- Todo o texto fica em `CONTENT['pt']` e `CONTENT['en']` no `build.py`.
- Rotas: `/` e `/en/` (institucional), `/produtos/` e `/en/produtos/` (loja), `/privacidade/` e `/en/privacidade/` (LGPD). O slug da rota (`produtos`, `privacidade`) é o mesmo nas duas línguas — só o texto visível muda, mesmo padrão das âncoras internas (`#particular` etc.).
- `page_header()`/`page_footer()`/`page_scripts()` em `build.py` são compartilhados por todas as páginas — nav, rodapé, pop-up de WhatsApp e de newsletter aparecem em qualquer rota. `nav_items_html()` decide se um link de âncora é hash puro (na própria home, pro JS de abas) ou link absoluto de volta pra home (`/#experimentar`) nas outras páginas.

### Loja — `/produtos`

- Catálogo em `products.py` (raiz do projeto): nome, descrição, categoria, preço, tamanhos, cores e estoque por peça, PT/EN. **Trocar/adicionar produto é editar uma entrada ali** — mesmo padrão de `PHOTOS`/`MODALITIES`. Preço `None` e estoque `"unknown"` até o clube confirmar (nunca inventados).
- `src/assets/js/products.js` — abre um modal de detalhes ao clicar num cartão (`render_produtos` em `build.py` gera os cartões; os dados completos vêm de `I18N.products`). Tamanho/cor só aparecem quando a lista do produto não está vazia. O botão "Comprar pelo WhatsApp" monta a mensagem com o nome da peça e a variação escolhida.
- Na home, a antiga seção "Good Vibes fora da água" virou uma chamada compacta (`.shop-teaser`) que leva pra `/produtos` — texto em `shop_teaser_title`/`shop_teaser_text`/`shop_teaser_cta` no `CONTENT`.

### Pop-up de newsletter

- `src/assets/js/newsletter.js` — aparece em qualquer página (sitewide), depois de ~25s **ou** ao detectar intenção de saída (mouse saindo por cima da janela), o que vier primeiro. Nunca na primeira tela.
- Não repete: quem já se cadastrou não vê mais (localStorage permanente); quem fechou sem cadastrar fica sem ver por 7 dias (localStorage com validade) — ver `SNOOZE_DAYS` no arquivo.
- Consentimento de marketing é um checkbox **separado**, nunca marcado por padrão, com link pra `/privacidade/` — sem ele marcado, o cadastro não é enviado.
- Proteção contra spam sem coletar IP (minimização de dados — ver `/privacidade/`): campo honeypot escondido + tempo mínimo de preenchimento, os dois validados de novo no servidor (`api/subscribers.ts`).
- Textos em `newsletter_content.py` (`NEWSLETTER`, PT/EN) — mesmo padrão de `booking_content.py`.
- Cadastros vão pra tabela `subscribers` no Supabase (ver `db/schema.sql`) via `POST /api/subscribers` — e-mail duplicado responde "já cadastrado" (200), nunca cria linha repetida.

### Campanha do pop-up (desligada por padrão)

`CAMPAIGN` em `newsletter_content.py`: `"enabled": False` por padrão — o
pop-up mostra só o cadastro simples. Ligar com `"type": "early_access"` ou
`"coupon"` troca o título/texto do pop-up por um benefício garantido a
quem se cadastra. **`"type": "raffle"` (sorteio) é bloqueado em
`build.py` (`resolve_campaign`) a não ser que `"legal_cleared": True`** —
sorteio exige regulamento e autorizações conforme a legislação brasileira
de promoções comerciais; não marcar `legal_cleared` sem isso estar pronto
de verdade.

### Reserva e formulários — `SITE["booking_mode"]`

O comportamento das três jornadas (experimentar, treinar, particular) depende
de uma única chave em `build.py`:

| Modo | O que acontece |
|---|---|
| `"off"` | Formulário de sempre: abre o WhatsApp do clube com a mensagem pronta. Nenhum dado sai do navegador da pessoa. |
| `"demo"` | **Só para apresentação interna.** Experiências, horários e vagas vem de `booking_content.py` (`DEMO_EXPERIENCES`), ilustrativos, com aviso visível em toda etapa. "Simular pagamento aprovado" confirma a reserva sem cobrar nada de verdade. Treinar/Particular mostram uma confirmação na tela, sem enviar a solicitação a lugar nenhum de verdade. |
| `"live"` | Usa o backend real em `SITE["api_base"]` (ver seção de backend abaixo) — disponibilidade, Pix e confirmação de verdade. |

**⚠️ Nunca publicar o site em produção com `booking_mode = "demo"`.** É um
modo de demonstração com dados fictícios; existe só para apresentar o fluxo
antes do backend estar pronto. Hoje o repositório está em `"demo"` — trocar
para `"off"` ou `"live"` antes de divulgar o link publicamente.

- `src/assets/js/booking.js` — **sistema único** de agendamento, usado
  pelas três jornadas (Experimentar, Treinar, Particular): calendário
  horizontal (próximos 14 dias) + cartões de atividade (nome, horário,
  duração, instrutor, vagas, preço, botão "Reservar") + modal de reserva.
  Uma instância por painel (`[data-booking][data-modality="..."]`), mesma
  casca visual, comportamento por `flow` (ver `booking_content.py`,
  `MODALITIES`):
  - `calendar+pix` (Experimentar) — participantes → termo → Pix → confirmação.
  - `calendar+request` (Treinar) — participantes/contato → confirmação
    direta, sem cobrança (a vaga é travada na hora).
  - `quote` (Particular) — sem calendário, um cartão fixo que abre o
    formulário de orçamento (sem vaga, sem pagamento).
  Modal com foco preso (Tab não escapa), `Esc` fecha, clique fora fecha.
- `src/assets/js/wa-widget.js` — pop-up do WhatsApp (ver seção própria
  abaixo).
- Textos de PT/EN do fluxo de reserva e do pop-up ficam em
  `booking_content.py` (`BOOKING`, `WA_WIDGET`, `MODALITIES`), importado
  por `build.py` — mesmo padrão de `CONTENT['pt']`/`CONTENT['en']`, nunca
  troca de texto via JS solto. O cronograma de Treinar em `MODALITIES` é
  ilustrativo (gerado com seed fixa, estável entre builds) até o clube
  confirmar os horários reais — ver `docs/SETUP.md` § 5.

### Pop-up do WhatsApp
- Botão redondo fixo no canto inferior direito (`src/assets/js/wa-widget.js`
  + `.wa-widget`/`.wa-card`/`.wa-fab` em `site.css`). Abre um cartão com a
  mensagem da equipe, campo de texto e "Continuar no WhatsApp".
- Abre sozinho uma vez por visita (8s ou ao sair do hero ao rolar), nunca
  enquanto o cartão de reserva (`[data-booking]`) está visível na tela, e
  não reabre sozinho depois de fechado (controlado por `sessionStorage`).
- Todo botão "Fale com a equipe" do site (`data-wa-open`) abre esse pop-up
  em vez de navegar para o WhatsApp direto — o `href` continua lá como
  reforço para quando JavaScript está desligado.
- No mobile, a barra fixa inferior mostra só "Reservar"; o botão do
  WhatsApp fica ao lado, sem sobrepor (`--dock-fab-space` em `site.css`
  reserva o espaço).

## Backend de reservas (em andamento)

Sistema de disponibilidade, reservas e pagamento Pix (Mercado Pago) sendo
construído em `/api` (Vercel Serverless Functions) + Supabase Postgres, ao
lado do site estático — sem alterar a stack do front.
`/api/reservations/*` cobre Experimentar (com Pix); `/api/requests` cobre
Treinar e Particular (sem cobrança — ver `docs/SETUP.md` § 5). Ver:

- `docs/SETUP.md` — como configurar Supabase, Mercado Pago e Vercel.
- `db/schema.sql` — schema do banco.
- `.env.example` — variáveis necessárias.
- `npm test` — testes da lógica de disponibilidade/webhook (`lib/`, `tests/`).

Nenhuma etapa é anunciada como pronta antes de rodar de verdade contra
credenciais reais (de teste) — ver o plano de arquitetura para o roteiro
completo.

## Antes de publicar

### 1. Fotografias oficiais

Todo espaço de foto do site é uma entrada no dicionário `PHOTOS`, no topo do
`build.py`: arquivo, alt em PT, alt em EN e `focus` (enquadramento/
object-position dentro do quadro). **Trocar uma foto é editar uma linha
em `PHOTOS` — nada mais no resto do código precisa mudar.** Se o arquivo
referenciado não existir em `src/assets/img/`, o espaço mostra a descrição
do que deve entrar ali (atributo `data-slot`); ao adicionar o arquivo com
o nome certo, a foto aparece sozinha no próximo `python3 build.py`.

| Chave em PHOTOS | Conteúdo | Tamanho sugerido |
|---|---|---|
| hero | Equipe remando ao amanhecer ou pôr do sol | 2400×1600 |
| captain_jesse, captain_nala | Retratos dos capitães | 1200×1200 |
| community_1 … community_4 | Comunidade, Outubro Rosa, 1 ano, canoa no mar | 1200×900 |
| product_1 … product_5 | Peças Moda Good Vibes | 1200×1200 |
| — | Logo circular do clube (`logo.png`, fora do PHOTOS — ver `<img class="brand-logo">`) | 480×480 |
| — | Imagem de compartilhamento (`og.jpg`, só em meta tag, fora do PHOTOS) | 1200×630 |

Exporte em JPG ou WebP com qualidade ~80, idealmente abaixo de 300 KB (o
hero pode chegar a 350 KB). Corrija a rotação pelo EXIF antes de exportar.
Se uma foto nova tiver texto ou arte sobreposta (ex.: post do Instagram com
título/preço), prefira recortar isso fora antes de usar — o `focus` ajusta
o enquadramento dentro do quadro, mas não remove texto de dentro da
própria imagem.

### 2. Conteúdo a confirmar com o clube
- Trocar `SITE["booking_mode"]` de `"demo"` para `"off"` ou `"live"` antes de publicar (ver seção de reserva acima).
- Valores, durações e horários de passeios e aulas (o site diz "sob consulta").
- Política de remarcação por condições do mar (FAQ).
- Idade mínima e regras para crianças; se é preciso saber nadar.
- Quais planos Gympass/TotalPass são aceitos.
- Ponto de encontro exato na Praia da Preguiça.
- Preços, tamanhos, cores e estoque real dos produtos — editar `products.py` (hoje todos com preço "sob consulta" e estoque "a confirmar", de propósito, até o clube informar os valores reais).
- Mini bio dos capitães (opcional).
- Depoimentos escritos: só publicar com autorização (estrutura comentada na seção Comunidade).
- Revisão jurídica do texto de `/privacidade/` (`privacy_sections` no `CONTENT`) antes de tratar como política de privacidade oficial — hoje é um resumo honesto, não um documento validado por advogado.

### 3. Depois de publicar
- Enviar `sitemap.xml` no Google Search Console.
- Criar/atualizar o Perfil da Empresa no Google com o link do site.
- Trocar o link da bio do Instagram para o site.
