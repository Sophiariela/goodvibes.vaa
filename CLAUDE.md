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

- `src/assets/js/booking.js` — jornada "Experimentar", cartão de 6 etapas.
  Lê `GVV_CONFIG` (`bookingMode`, `apiBase`, `seats`) e `I18N.bk`/
  `I18N.demoExperiences` do `<script id="i18n">`.
- `src/assets/js/wa-widget.js` — pop-up do WhatsApp, abre automaticamente
  uma vez por visita, **nunca enquanto `[data-booking]` está visível na
  tela** (checagem síncrona de geometria em `bookingOnScreen()`, não só
  `IntersectionObserver` — evita corrida entre o gatilho "saiu do hero" e o
  observer do cartão ainda não ter processado a posição nova).
- `build.py`: `contact_fields()` adiciona nome/WhatsApp aos formulários de
  Treinar/Particular quando `booking_mode != "off"`; `form_shell()` troca o
  texto de privacidade e remove o ícone do WhatsApp do botão nesse caso
  também (o envio não é mais necessariamente uma conversa de WhatsApp).
- Todo texto novo (passos, erros, Pix, pop-up) vem de `booking_content.py`
  (`BOOKING`, `WA_WIDGET`, `DEMO_EXPERIENCES`), importado por `build.py` e
  mesclado em `CONTENT[locale]["i18n"]` — mesmo padrão de sempre, nunca
  texto solto em JS.

## Backend de reservas (live)

Ver README.md § "Backend de reservas" e `docs/SETUP.md`. Em desenvolvimento,
ainda sem credenciais reais configuradas — nenhum endpoint `/api` deve ser
anunciado como funcional antes de testado contra Supabase/Mercado Pago de
verdade.
