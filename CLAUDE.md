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
— ver seção de backend abaixo). Hoje o repositório está em `"demo"`.

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
