# Good Vibes Va'a — site

Site institucional e de conversão do clube de canoa havaiana Good Vibes Va'a (Praia da Preguiça, Salvador).

## Stack e por quê

Site estático gerado por um script Python sem dependências. Uma landing page de uma marca local não precisa de framework, banco de dados ou build de JavaScript: HTML pronto carrega mais rápido, indexa melhor e pode ser hospedado de graça (Netlify, Cloudflare Pages, Vercel, GitHub Pages).

```
build.py                 conteúdo PT/EN + templates + geração do site
src/assets/css/site.css  design system (tokens, componentes, seções)
src/assets/js/site.js    navegação, formulários, ponto de integração
src/assets/fonts/        Archivo variável, auto-hospedada (licença OFL)
src/assets/img/          fotos oficiais (ver lista abaixo)
dist/                    site pronto para publicar (gerado)
```

Para gerar: `python3 build.py`. Publique a pasta `dist/`.

### Deploy
Hospedado na Vercel, conectado a este repositório. Todo push na branch `main` dispara um deploy automático de produção.

### Idiomas
- Português em `/`, inglês em `/en/`. Cada idioma é uma página HTML completa, com `lang`, `canonical`, `hreflang`, Open Graph e JSON-LD próprios. Não há troca de texto por JavaScript.
- Todo o texto fica em `CONTENT['pt']` e `CONTENT['en']` no `build.py`.

### Formulários e integrações
- As três jornadas (experimentar, treinar, particular) têm formulários separados. Hoje, cada envio abre o WhatsApp do clube com a mensagem já preenchida.
- Para ligar um sistema de reservas ou pagamentos, defina `request_endpoint` em `SITE` no `build.py`. O JS passa a enviar `POST` JSON `{ journey, locale, fields }` para esse endereço, sem mudar o HTML.
- Nada no site simula disponibilidade, pagamento ou confirmação.

## Antes de publicar

### 1. Fotografias oficiais
Coloque os arquivos em `src/assets/img/` com estes nomes. Cada espaço sem foto mostra a descrição do que deve entrar ali; ao adicionar o arquivo, a foto aparece automaticamente.

| Arquivo | Conteúdo | Tamanho sugerido |
|---|---|---|
| hero.jpg | Equipe remando ao amanhecer ou pôr do sol | 2400×1600 |
| clube.jpg | Canoas na areia da Praia da Preguiça | 2400×1000 |
| experimentar.jpg | Turma no passeio | 1200×1500 |
| particular.jpg | Grupo privado na canoa | 1200×1500 |
| captain-jesse.jpg, captain-nala.jpg | Retratos dos capitães | 1200×1500 |
| comunidade-1.jpg … comunidade-5.jpg | Comunidade, Outubro Rosa, 1 ano | 1200×900 |
| produto-1.jpg … produto-5.jpg | Peças Moda Good Vibes | 1200×1500 |
| final.jpg | Canoa no mar ao pôr do sol | 2400×1200 |
| og.jpg | Imagem de compartilhamento | 1200×630 |
| logo.png | Logo circular do clube | 160×160 |

Exporte em JPG ou WebP com qualidade ~80 (ou passe por squoosh.app). O hero deve ficar abaixo de 350 KB.

### 2. Conteúdo a confirmar com o clube
- Domínio definitivo (`base_url` no `build.py`; hoje está `example.com`).
- Valores, durações e horários de passeios e aulas (o site diz "sob consulta").
- Política de remarcação por condições do mar (FAQ).
- Idade mínima e regras para crianças; se é preciso saber nadar.
- Quais planos Gympass/TotalPass são aceitos.
- Ponto de encontro exato na Praia da Preguiça.
- Nomes e preços dos produtos.
- Mini bio dos capitães (opcional).
- Depoimentos escritos: só publicar com autorização (estrutura comentada na seção Comunidade).

### 3. Depois de publicar
- Enviar `sitemap.xml` no Google Search Console.
- Criar/atualizar o Perfil da Empresa no Google com o link do site.
- Trocar o link da bio do Instagram para o site.
