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

## Backend de reservas

Ver README.md § "Backend de reservas" e `docs/SETUP.md`. Em desenvolvimento,
ainda sem credenciais reais configuradas — nenhum endpoint `/api` deve ser
anunciado como funcional antes de testado contra Supabase/Mercado Pago de
verdade.
