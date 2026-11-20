#!/usr/bin/env python3
"""
Gerador estático do site Good Vibes Va'a.

Uma única fonte de conteúdo (CONTENT['pt'] e CONTENT['en']) gera:
  dist/index.html        -> português (pt-BR), URL /
  dist/en/index.html     -> inglês, URL /en/
  dist/sitemap.xml, dist/robots.txt, dist/404.html
  dist/assets/...        -> CSS, JS e imagens

Uso:  python3 build.py
Sem dependências além do Python 3.8+.
"""
import json
import shutil
from html import escape
from pathlib import Path

from booking_content import MODALITIES, BOOKING, WA_WIDGET
from products import PRODUCTS
from legal_content import LEGAL
from newsletter_content import NEWSLETTER, CAMPAIGN

# ---------------------------------------------------------------------------
# Configuração do negócio. Tudo que é dado comercial fica aqui.
# ---------------------------------------------------------------------------
SITE = {
    # TROCAR pelo domínio definitivo antes de publicar (usado em canonical, OG e sitemap)
    "base_url": "https://goodvibesvaa.vercel.app",
    "name": "Good Vibes Va'a",
    "whatsapp": "5571999789710",
    "whatsapp_display": "(71) 99978-9710",
    "instagram": "https://www.instagram.com/goodvibes.vaa/",
    "instagram_handle": "@goodvibes.vaa",
    "captains": [
        {"name": "Jesse Coutinho", "handle": "jesse_coutinho", "photo": "captain_jesse"},
        {"name": "Nala Rodrigues", "handle": "nalarodrigues", "photo": "captain_nala"},
    ],
    "maps_embed": "https://www.google.com/maps?q=Praia+da+Pregui%C3%A7a,+Salvador,+BA&output=embed",
    "maps_link": "https://www.google.com/maps/search/?api=1&query=Praia+da+Pregui%C3%A7a+Salvador+BA",
    # Modo do sistema de reservas (ver src/assets/js/booking.js):
    #   "demo" -> dados ilustrativos, aviso visível, nada é cobrado de verdade.
    #   "live" -> usa o backend em api_base (contrato no README/docs/SETUP.md).
    #   "off"  -> volta ao formulário de WhatsApp de cada jornada.
    # NUNCA publicar em "demo": é só para apresentação interna.
    "booking_mode": "off",
    "api_base": "",
    "booking_seats": 6,
}

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

# ---------------------------------------------------------------------------
# Fotos — uma entrada por espaço de foto do site. Trocar uma foto é trocar
# o "file" de uma linha aqui; nada mais no resto do build.py precisa mudar.
# "focus" é o object-position da foto dentro do quadro (ver .media img no
# site.css) — "center" serve pra quase tudo; só ajuste quando um rosto ou
# detalhe importante for cortado pelo enquadramento quadrado/retangular.
# ---------------------------------------------------------------------------
PHOTOS = {
    "hero": {
        "file": "hero.jpg",
        "alt_pt": "Equipe Good Vibes Va'a remando uma canoa havaiana ao amanhecer na Baía de Todos-os-Santos",
        "alt_en": "Good Vibes Va'a crew paddling an outrigger canoe at sunrise on the Bay of All Saints",
        "focus": "center",
    },
    "captain_jesse": {
        "file": "captain-jesse.jpg",
        "alt_pt": "Retrato de Jesse Coutinho, capitão do Good Vibes Va'a",
        "alt_en": "Portrait of Jesse Coutinho, Good Vibes Va'a captain",
        "focus": "center",
    },
    "captain_nala": {
        "file": "captain-nala.jpg",
        "alt_pt": "Retrato de Nala Rodrigues, capitã do Good Vibes Va'a",
        "alt_en": "Portrait of Nala Rodrigues, Good Vibes Va'a captain",
        "focus": "center",
    },
    "community_1": {
        "file": "comunidade-1.jpg",
        "alt_pt": "Equipe Good Vibes Va'a comemorando em grupo, abraçados, após o treino",
        "alt_en": "Good Vibes Va'a crew celebrating together, arms around each other, after training",
        "focus": "center",
    },
    "community_2": {
        "file": "comunidade-2.jpg",
        "alt_pt": "Abraço entre integrantes da equipe durante a campanha Outubro Rosa",
        "alt_en": "Crew members hugging during the Pink October campaign",
        "focus": "center",
    },
    "community_3": {
        "file": "comunidade-3.jpg",
        "alt_pt": "Integrante da equipe na comemoração de 1 ano do clube, de olhos fechados e braços erguidos",
        "alt_en": "Crew member at the club's 1-year anniversary celebration, eyes closed, arms raised",
        "focus": "center",
    },
    "community_4": {
        "file": "comunidade-canoa.jpg",
        "alt_pt": "Equipe remando em canoa havaiana no mar",
        "alt_en": "Crew paddling an outrigger canoe at sea",
        "focus": "center 60%",
    },
    "product_1": {
        "file": "produto-1.jpg",
        "alt_pt": "Camisa UV Atleta Good Vibes Va'a sobre a areia da praia",
        "alt_en": "Good Vibes Va'a Atleta UV shirt on the beach sand",
        "focus": "center",
    },
    "product_2": {
        "file": "produto-2.jpg",
        "alt_pt": "Sacola Good Vibes Va'a sobre a areia da praia",
        "alt_en": "Good Vibes Va'a drawstring bag on the beach sand",
        "focus": "center",
    },
    "product_3": {
        "file": "produto-3.jpg",
        "alt_pt": "Viseira Good Vibes Va'a sobre a areia da praia",
        "alt_en": "Good Vibes Va'a visor on the beach sand",
        "focus": "center",
    },
    "product_4": {
        "file": "produto-4.jpg",
        "alt_pt": "Boné Good Vibes Va'a sobre a areia da praia",
        "alt_en": "Good Vibes Va'a cap on the beach sand",
        "focus": "center",
    },
    "product_5": {
        "file": "produto-5.jpg",
        "alt_pt": "Camisa de algodão comemorativa Good Vibes Va'a sobre a areia da praia",
        "alt_en": "Good Vibes Va'a commemorative cotton shirt on the beach sand",
        "focus": "center",
    },
}

# ---------------------------------------------------------------------------
# Conteúdo por idioma
# Regra editorial: nada de preços, horários, durações, regras ou depoimentos
# inventados. O que depende do clube aparece como "a equipe confirma" e está
# listado no README (checklist de conteúdo).
# ---------------------------------------------------------------------------
CONTENT = {
    "pt": {
        "bk": BOOKING["pt"],
        "wa": WA_WIDGET["pt"],
        "lang": "pt-BR",
        "og_locale": "pt_BR",
        "path": "/",
        "title": "Good Vibes Va'a — Canoa havaiana na Praia da Preguiça, Salvador",
        "description": "Clube de canoa havaiana na Praia da Preguiça, em Salvador. Passeios no nascer e no pôr do sol, aulas, planos de treino e experiências particulares na Baía de Todos-os-Santos.",
        "skip": "Pular para o conteúdo",
        "brand_sub": "Clube de canoa havaiana",
        # Menu (hambúrguer) e rodapé leem a MESMA lista. Item que começa
        # com "#" é âncora da home; o resto é slug de rota ("produtos",
        # "contato") — ver nav_items_html().
        "nav": [("agendar", "Reservar"), ("#clube", "O Clube"), ("#comunidade", "Comunidade Local"), ("#experiencias", "Experiências"), ("#faq", "Dúvidas"), ("produtos", "Produtos")],
        "nav_produtos": "Produtos",
        "menu_word": "Menu",
        "menu_label": "Menu de navegação",
        "menu_cta": "Reservar uma remada",
        "menu_contact": "Contato",
        "lang_label": "Idioma",
        "cta_team": "Fale com a equipe",
        "menu_open": "Abrir menu",
        "menu_close": "Fechar menu",
        "hero_place": "Praia da Preguiça, Salvador",
        # A manchete do hero tem duas linhas dentro do mesmo <h1>: a palavra
        # gigante (hero_word) e a frase da marca (hero_title) logo abaixo.
        "hero_word": "Reme!",
        "hero_title": "Encontre seu ritmo no mar.",
        "hero_sub": "Experiências, aulas e uma comunidade conectada pela canoa havaiana na Baía de Todos-os-Santos.",
        "hero_cta1": "Reservar passeio",
        "hero_play": "Veja no Instagram",
        "hero_play_aria": "Ver os vídeos do clube no Instagram",
        "hero_slot": "Foto oficial: equipe remando ao amanhecer na Baía de Todos-os-Santos · 2400×1600 · hero.jpg",
        "hero_alt": "Equipe Good Vibes Va'a remando uma canoa havaiana ao amanhecer na Baía de Todos-os-Santos",

        # Faixa de credibilidade logo abaixo do hero.
        "credibility_label": "Onde estamos e como participar",
        "credibility": ["Gympass", "TotalPass", "Praia da Preguiça", "Salvador · Bahia"],
        # Prefixo dos slots de foto gerados a partir do próprio título do
        # cartão (ver media() — o slot só aparece se o arquivo faltar).
        "photo_slot_prefix": "Foto oficial:",

        "about_statement": "Na canoa, ninguém rema sozinho. Cada remada depende do ritmo de quem está ao lado, e é isso que transforma uma aula em comunidade.",
        "kicker_journeys": "Experiências",
        "kicker_club": "O clube",
        "kicker_community": "Comunidade",
        "kicker_shop": "Moda Good Vibes",
        "kicker_info": "Onde e como",
        "kicker_closing": "Reserve sua remada",
        "kicker_legal": "Documento",
        "journeys_title": "Três formas de entrar no mar.",
        "journeys_lead": "Escolha o caminho que combina com você. Cada um tem sua própria conversa com a equipe.",
        "journeys": [
            ("#experimentar", "Quero experimentar", "Passeios e primeira remada, no nascer ou no pôr do sol.", "Ver passeios"),
            ("#treinar", "Quero treinar", "Aulas avulsas, planos mensais e check-in com Gympass e TotalPass.", "Ver planos"),
            ("#particular", "Quero uma experiência particular", "Grupos, aniversários, empresas e saídas privadas.", "Pedir orçamento"),
        ],

        # Faixa "O que oferecemos": quatro cartões sobre a fotografia. Cada
        # cartão aponta para a jornada de reserva correspondente — a aba
        # certa abre sozinha (ver initTabs em site.js).
        "offers_title": "O que oferecemos",
        "offers_lead": "Da primeira remada aos treinos com a equipe. Horários e valores são confirmados pela equipe no momento da reserva.",
        "offers_cta": "Ver datas e reservar",
        "offer_cards": [
            ("#experimentar", "hero", "Nascer e pôr do sol", "Passeio · valores sob consulta", "A cidade vista de dentro da baía, no começo ou no fim do dia."),
            ("#experimentar", "community_4", "Primeira remada", "Iniciantes · com capitão", "Técnica e segurança na areia, depois o mar. Não precisa ter experiência."),
            ("#treinar", "community_1", "Treinos e planos", "Avulsa · mensal · Gympass e TotalPass", "Rotina de treino com a equipe e acompanhamento dos capitães."),
            ("#particular", "community_3", "Particular", "Grupos · aniversários · empresas", "A canoa só para o seu grupo, com roteiro combinado com a equipe."),
        ],

        # "Por que remar com a gente" — o primeiro item de cada tupla é a
        # chave do ícone em gota (ver ICONS_REASON em build.py).
        "reasons_title": "Por que remar com a gente",
        "reasons_lead": "Um clube de canoa havaiana com capitães, equipe e um dos cenários mais bonitos de Salvador.",
        "reasons": [
            ("captain", "Capitães no comando", "Jesse e Nala conduzem cada saída, da areia até o retorno."),
            ("shield", "Segurança primeiro", "Instruções de remada e de segurança antes de entrar no mar."),
            ("pin", "Melhor localização", "Praia da Preguiça, de frente para a Baía de Todos-os-Santos."),
            ("crew", "Comunidade", "Treinos, eventos e um ano de histórias no mar."),
        ],

        # Carrossel de momentos (as mesmas quatro fotos da antiga faixa).
        "moments_label": "Momentos do clube",
        "moments": [
            ("community_1", "Depois do treino", "A equipe reunida na areia da Preguiça."),
            ("community_2", "Outubro Rosa", "Remada pela conscientização."),
            ("community_3", "1 ano de Good Vibes", "Um ano de histórias no mar."),
            ("product_2", "Moda Good Vibes", "A identidade do clube fora da água."),
        ],
        "carousel_prev": "Ver momentos anteriores",
        "carousel_next": "Ver próximos momentos",

        "a_kicker": "Quero experimentar",
        "a_title": "Sua primeira vez na canoa havaiana.",
        "a_lead": "Não é preciso ter experiência. Os capitães explicam a técnica, o ritmo e a segurança antes de entrar no mar.",
        "a_offers": [
            ("Primeira experiência", "Para quem nunca remou. Uma introdução ao esporte com orientação do capitão."),
            ("Nascer do sol", "Saída cedo, mar calmo e a cidade acordando vista da baía."),
            ("Pôr do sol", "O fim de tarde de Salvador visto de dentro da Baía de Todos-os-Santos."),
            ("Turismo náutico", "Para visitantes que querem conhecer a orla e a história da cidade pelo mar."),
        ],
        "a_note": "<strong>Duração, horários e valores</strong> variam conforme a experiência e as condições do mar. A equipe confirma tudo pelo WhatsApp antes da sua reserva.",
        "a_form_title": "Solicitar reserva",
        "a_form_intro": "Sua solicitação vai pronta para o WhatsApp da equipe, que confirma a reserva.",
        "a_wa_intro": "Olá, Good Vibes Va'a! Gostaria de solicitar uma reserva de passeio:",
        "a_options": [("primeira", "Primeira experiência"), ("nascer", "Passeio no nascer do sol"), ("por", "Passeio no pôr do sol"), ("turismo", "Turismo náutico")],

        # --- Reserva de "Experimentar" no modo "off" -----------------------
        # Composição única e centralizada: cabeçalho curto, cartões de
        # experiência, formulário objetivo e um único CTA. Os textos longos
        # que antes ficavam soltos na tela (a_lead/a_note) agora vivem no
        # accordion "Antes de remar" — nada foi apagado, só recolhido.
        "a_head_title": "Sua primeira vez na canoa.",
        "a_head_sub": "Escolha sua experiência, a data e venha viver Salvador de um jeito diferente.",
        # (valor, nome, descrição curta) — o valor casa com "a_options", que
        # continua sendo o vocabulário da jornada em todos os modos.
        "a_cards": [
            ("primeira", "Primeira Experiência", "Uma introdução à canoa havaiana, ideal para iniciantes."),
            ("nascer", "Nascer do Sol", "Remada nas primeiras horas da manhã."),
            ("por", "Pôr do Sol", "Uma experiência ao final da tarde, com Salvador e a Baía de Todos-os-Santos como cenário."),
            ("turismo", "Turismo Náutico", "A orla e a história da cidade vistas de dentro do mar."),
        ],
        "a_cards_legend": "Escolha sua experiência",
        "a_cta": "Solicitar reserva",
        "a_before_title": "Antes de remar",
        "a_before": [
            "Não é preciso ter experiência: os capitães explicam a técnica e o ritmo antes de entrar no mar.",
            "Toda saída começa com orientação de segurança na areia, com o capitão.",
            "Leve roupa leve, protetor solar, água e uma muda de roupa seca.",
            "Duração, horários e valores variam conforme a experiência e as condições do mar — a equipe confirma tudo pelo WhatsApp.",
        ],
        "f_email": "E-mail",
        "f_optional": "opcional",
        "f_group_size": "Tamanho do grupo",

        # --- Página /agendar/ — descoberta por carrossel ------------------
        # Uma experiência por vez: o visitante navega as três jornadas no
        # carrossel e só então entra no fluxo daquela escolha. Os campos de
        # cada fluxo saem de "xp_config" e são os mesmos vocabulários das
        # jornadas (a_options, b_options, c_options…) — nada inventado aqui.
        "agendar_path": "/agendar/",
        "agendar_title": "Agendar sua remada — Good Vibes Va'a",
        "agendar_description": "Escolha sua experiência na canoa havaiana — primeira remada, treino ou saída privada — e envie sua solicitação para a equipe do clube.",
        "agendar_kicker": "Reservas",
        "agendar_h1": "Qual experiência você quer viver?",
        "agendar_hint": "Arraste ou use as setas para ver as três experiências.",
        "xp_cards": [
            ("experimentar", "community_4", "Quero experimentar",
             "Primeira remada ou passeio na canoa havaiana."),
            ("treinar", "community_1", "Quero treinar",
             "Treinos regulares, aulas avulsas e planos."),
            ("particular", "community_3", "Quero uma experiência particular",
             "Grupos, eventos, aniversários e saídas privadas."),
        ],
        "xp_explore": "Explorar experiência",
        "xp_steps": ["Configurar", "Data", "Seus dados", "Confirmar"],
        "xp_back_all": "Ver todas as experiências",
        "xp_next": "Continuar",
        "xp_prev": "Voltar",
        "xp_prev_label": "Experiência anterior",
        "xp_next_label": "Próxima experiência",
        "xp_review_title": "Confirme sua solicitação",
        "xp_review_lead": "Confira os dados antes de enviar. A equipe confirma a reserva pelo WhatsApp.",
        "xp_edit": "Alterar",
        "xp_date_title": "Quando você quer remar?",
        "xp_date_title_treinar": "Quando você quer começar?",
        "xp_contact_title": "Como falamos com você?",
        "xp_submit": "Solicitar reserva",
        "xp_resumed": "Retomamos de onde você parou.",

        "f_name": "Seu nome",
        "f_experience": "Experiência",
        "f_date": "Data desejada",
        "f_people": "Número de pessoas",
        "f_notes": "Observações",
        "f_notes_hint": "Idade de crianças, se é sua primeira vez, dúvidas.",
        "f_choose": "Selecione",
        "f_more": "Adicionar observação",
        "tab_short": ["Experimentar", "Treinar", "Particular"],
        "f_submit": "Enviar pelo WhatsApp",
        "f_privacy": "Seus dados são usados só para responder a esta solicitação, pela conversa de WhatsApp que você mesmo envia.",
        "f_privacy_site": "Seus dados são usados só para responder a esta solicitação, pelo WhatsApp informado.",

        "bring_title": "O que levar",
        "bring": ["Roupa de banho", "Protetor solar", "Água", "Boné ou viseira", "Bolsa estanque para o celular"],

        "team_title": "Quem rema com você.",
        "team_lead": "Os capitães conduzem cada saída, das primeiras orientações na areia até o retorno.",
        "captain_role": "Capitão",
        "captain_role_f": "Capitã",
        "captain_slot": "Foto oficial: retrato do(a) capitão(ã) na canoa · 1200×1500",

        "community_title": "Uma comunidade que se encontra no mar.",
        "community_lead": "Treinos ao amanhecer, ações como o Outubro Rosa e um ano de histórias contadas por quem rema com a gente.",
        "community_cta": "Ver depoimentos no Instagram",
        "community_note": "Depoimentos em vídeo de quem já remou com o clube estão no nosso Instagram.",

        "b_kicker": "Quero treinar",
        "b_title": "Planos e formas de participar.",
        "b_lead": "Para quem quer fazer da canoa havaiana parte da rotina, evoluir na técnica e treinar com a equipe.",
        "plans": [
            ("Aula avulsa", "Para conhecer o treino do clube ou complementar sua rotina.", "Valores sob consulta"),
            ("Plano mensal", "Treinos recorrentes com a equipe, acompanhamento dos capitães e participação na comunidade.", "Valores sob consulta"),
            ("Gympass e TotalPass", "Faça check-in com o seu plano. Confirme com a equipe quais planos são elegíveis.", "Pelo seu aplicativo"),
        ],
        "b_note": "<strong>Horários de treino</strong>: a grade atual é enviada pela equipe no WhatsApp.",
        "b_form_title": "Quero treinar com o clube",
        "b_form_intro": "A equipe responde com horários, valores e como se matricular.",
        "b_wa_intro": "Olá, Good Vibes Va'a! Quero treinar com o clube:",
        "b_options": [("avulsa", "Aula avulsa"), ("mensal", "Plano mensal"), ("app", "Gympass ou TotalPass")],
        "f_modality": "Modalidade",
        "f_period": "Período preferido",
        "f_periods": [("manha", "Manhã"), ("tarde", "Fim da tarde"), ("flex", "Tanto faz")],
        "f_experience_level": "Você já remou?",
        "f_levels": [("nunca", "Nunca remei"), ("algumas", "Algumas vezes"), ("pratico", "Já pratico")],

        "c_kicker": "Quero uma experiência particular",
        "c_title": "A canoa só para o seu grupo.",
        "c_lead": "Saídas exclusivas para celebrar, integrar equipes ou viver o mar com quem você escolher.",
        "formats": [
            ("Grupos", "Amigos, famílias e grupos de viagem."),
            ("Aniversários", "Uma comemoração no mar, no nascer ou no pôr do sol."),
            ("Eventos corporativos", "Integração de equipes e ações de bem-estar para empresas."),
            ("Experiências privadas", "Saída exclusiva, com roteiro conversado com a equipe."),
        ],
        "c_form_title": "Solicitar orçamento",
        "c_form_intro": "A equipe responde com formato, disponibilidade e valores.",
        "c_wa_intro": "Olá, Good Vibes Va'a! Gostaria de um orçamento para uma experiência particular:",
        "c_options": [("grupo", "Grupo"), ("aniversario", "Aniversário"), ("corporativo", "Evento corporativo"), ("privada", "Experiência privada")],
        "f_type": "Tipo de experiência",
        "f_company": "Empresa (opcional)",
        "f_details": "Conte mais",
        "f_details_hint": "Ocasião, horário preferido, se o grupo já remou.",
        "f_submit_quote": "Pedir orçamento pelo WhatsApp",

        "shop_title": "Good Vibes fora da água.",
        "shop_lead": "Peças da linha Moda Good Vibes para levar a identidade do clube para o dia a dia.",
        "shop_slot": "Foto oficial do produto · 1200×1500 · produto-{n}.jpg",
        "shop_cta": "Pedir peças pelo WhatsApp",
        "shop_wa": "Olá, Good Vibes Va'a! Gostaria de saber sobre os produtos da Moda Good Vibes.",

        "shop_teaser_title": "Leve a Good Vibes com você.",
        "shop_teaser_text": "Conheça nossa coleção e leve um pouco da energia do mar para o seu dia a dia.",
        "shop_teaser_cta": "EXPLORAR PRODUTOS",

        # Loja: apresentação, categorias (filtro real, lido de products.py),
        # espaços de peça futura e coleções. Nada aqui inventa produto,
        # preço ou disponibilidade — "Em breve" é etiqueta de espaço vazio.
        "shop_intro_kicker": "A loja do clube",
        "shop_intro_title": "Feito para remar, usado todo dia.",
        "shop_intro_text": "A linha Moda Good Vibes nasce do uso: camisa que aguenta sol e sal, boné que não voa na remada, sacola que volta molhada da praia. Cada peça é produzida em pequenas levas para a comunidade do clube.",
        "shop_cat_label": "Categorias",
        "shop_cat_all": "Tudo",
        "shop_soon_badge": "Em breve",
        "shop_soon_title": "Nova peça",
        "shop_soon_text": "Espaço reservado para a próxima leva da linha. Quando a peça for confirmada pelo clube, ela aparece aqui.",
        "shop_collections_kicker": "Coleções",
        "shop_collections_title": "O que já existe e o que vem pela frente.",
        "shop_collections": [
            ("Linha Good Vibes", "Vestuário e acessórios do dia a dia do clube, com a logo circular.", "product_1", False),
            ("Comemorativa", "A camisa de algodão feita para marcar o primeiro ano do clube.", "product_5", False),
            ("Próxima coleção", "Em produção. A equipe confirma peças, tamanhos e valores antes de publicar.", "product_3", True),
        ],
        "shop_howto_title": "Como comprar hoje",
        "shop_howto_text": "A loja ainda não tem pagamento online. Escolha a peça, fale com a equipe pelo WhatsApp e ela confirma disponibilidade, tamanho e valor antes de qualquer pagamento.",
        "produtos_path": "/produtos/",
        "produtos_title": "Produtos — Loja Good Vibes Va'a",
        "produtos_description": "Peças oficiais da linha Moda Good Vibes Va'a: camisas, boné, viseira e sacola com a identidade do clube.",
        "produtos_price_request": "Sob consulta",
        "produtos_stock": {"available": "Disponível", "low": "Últimas unidades", "out": "Esgotado", "unknown": "Disponibilidade a confirmar"},
        "produtos_size_label": "Tamanho",
        "produtos_color_label": "Cor",
        "produtos_buy_cta": "Comprar pelo WhatsApp",
        "produtos_close": "Fechar detalhes",
        "produtos_wa_intro": "Olá, Good Vibes Va'a! Tenho interesse nesta peça: {product}",
        "produtos_empty": "Em breve, novas peças por aqui.",

        "contato_path": "/contato/",
        "contato_title": "Contato — Good Vibes Va'a",
        "contato_description": "Fale com a equipe do Good Vibes Va'a: envie uma mensagem pelo formulário, chame no WhatsApp ou mande uma mensagem pelo Instagram.",
        "contato_h1": "Vamos conversar?",
        "contato_lead": "Estamos aqui para ajudar você a viver a experiência Good Vibes.",
        "contato_kicker": "Atendimento",
        "contato_mail_title": "Enviar uma mensagem",
        "contato_mail_text": "Conte o que você precisa e a equipe responde no e-mail que você informar.",
        "contato_wa_title": "WhatsApp",
        "contato_wa_text": "Para quem prefere conversar na hora — é o canal mais rápido para dúvidas de reserva.",
        "contato_wa_cta": "Abrir conversa no WhatsApp",
        "contato_other_title": "Outros canais",
        "contato_other_text": "O clube também responde às mensagens diretas do Instagram, onde ficam os vídeos e as novidades das saídas.",
        "contato_other_cta": "Mensagem no Instagram",
        "contato_hours_title": "Antes de escrever",
        "contato_hours_text": "Horários, valores e vagas mudam conforme o mar e a agenda do clube — a equipe confirma tudo na resposta. Dúvidas frequentes já respondidas estão na home.",
        "contato_hours_cta": "Ver dúvidas frequentes",
        "privacy_path": "/privacidade/",
        "legal_back": "Voltar ao início",
        "legal_draft_label": "Rascunho",
        "legal_draft_note": "Documento em elaboração: ainda não foi validado pelo clube nem revisado juridicamente. Não vale como política em vigor.",
        "legal_pending": "a definir",
        "legal_pending_aria": "Ponto ainda em aberto",
        "legal_index": "Nesta página",
        "legal_docs_title": "Documentos do clube",

        "ct_name": "Nome completo",
        "ct_email": "E-mail",
        "ct_subject": "Assunto",
        "ct_message": "Mensagem",
        "ct_submit": "Enviar mensagem",
        "ct_privacy": "Usamos seus dados só para responder a esta mensagem. Ver a política de privacidade.",
        "ct_subjects": [("reserva", "Reserva de experiência"), ("treino", "Aulas e treinos"), ("particular", "Grupos e empresas"), ("produtos", "Produtos"), ("outro", "Outro assunto")],

        "place_title": "Praia da Preguiça, Salvador.",
        "place_lead": "As saídas acontecem na Praia da Preguiça, de frente para a Baía de Todos-os-Santos.",
        "place_items": [
            ("Ponto de encontro", "Praia da Preguiça, Salvador, Bahia. O ponto exato é enviado na confirmação."),
            ("Contato", SITE["whatsapp_display"] + " (WhatsApp)"),
            ("Instagram", SITE["instagram_handle"]),
        ],
        "place_maps": "Abrir no Google Maps",
        "map_title": "Mapa da Praia da Preguiça, Salvador",

        "faq_title": "Dúvidas frequentes.",
        "faq_lead": "Não encontrou sua resposta? Fale com a equipe.",
        "faq": [
            ("Preciso ter experiência para remar?", "Não. A primeira experiência é pensada para quem nunca remou, e os capitães orientam técnica e segurança antes da saída."),
            ("Como faço uma reserva?", "Envie sua solicitação pelo formulário ou direto no WhatsApp. A reserva é confirmada pela equipe, que informa horário, valores e ponto de encontro."),
            ("Vocês aceitam Gympass e TotalPass?", "Sim. Confirme com a equipe quais planos e modalidades são elegíveis para check-in."),
            ("O que acontece se o mar não estiver bom?", "A equipe acompanha as condições do mar antes de cada saída e entra em contato para combinar uma nova data quando necessário."),
            ("O que levar?", "Roupa de banho, protetor solar, água, boné ou viseira e uma bolsa estanque para o celular."),
            ("Posso levar crianças?", "Fale com a equipe informando a idade das crianças para saber quais experiências são indicadas."),
            ("Vocês fazem eventos para empresas?", "Sim. Use o formulário de experiência particular para pedir um orçamento."),
        ],

        "final_title": "O mar está esperando.",
        "final_lead": "Escolha sua experiência ou fale direto com a equipe.",

        "footer_about": "Clube de canoa havaiana na Praia da Preguiça, de frente para a Baía de Todos-os-Santos. Passeios, aulas e treinos para quem nunca remou e para quem já compete.",
        "footer_brand_cta": "Reservar uma experiência",
        "footer_nav": "Navegue",
        "footer_service": "Atendimento",
        "footer_service_text": "Dúvidas sobre experiências, reservas ou produtos? A equipe responde pela página de contato.",
        "footer_service_cta": "Falar com a equipe",
        "footer_ig_label": "Instagram do Good Vibes Va'a",
        "footer_location_label": "Onde remamos",
        "footer_location": "Praia da Preguiça · Salvador · Bahia",
        "footer_location_cta": "Como chegar",
        "footer_credit": "Site por",
        "footer_follow": "Acompanhe",
        "footer_rights": "Todos os direitos reservados.",
        "dock_book": "Reservar",
        "i18n": {
            "locale": "pt",
            "menuOpen": "Abrir menu",
            "menuClose": "Fechar menu",
            "required": "Preencha este campo.",
            "datePast": "Escolha uma data a partir de hoje.",
            "minPeople": "Informe pelo menos 1 pessoa.",
            "openedWhatsapp": "Abrimos o WhatsApp com sua solicitação. É só enviar a mensagem.",
            "sent": "Solicitação enviada. A equipe vai responder em breve.",
            "sendError": "Não foi possível enviar agora. Tente de novo ou fale com a equipe pelo WhatsApp.",
            "invalidEmail": "Informe um e-mail válido.",
            "contact": {
                "sending": "Enviando…",
                "ok": "Mensagem enviada. A equipe responde no e-mail que você informou.",
                "offline": "O envio por e-mail ainda não está ativo neste site. Fale com a equipe pelo WhatsApp — o botão está logo ao lado.",
                "error": "Não foi possível enviar agora. Tente de novo em instantes ou fale com a equipe pelo WhatsApp.",
            },
            # Calendário visual da reserva (datepicker.js). Os nomes de mês e
            # as iniciais de semana vêm daqui, não de toLocaleDateString: o
            # texto do site sempre sai do HTML, nunca da runtime do navegador.
            "cal": {
                "months": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                           "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
                "weekdays": ["D", "S", "T", "Q", "Q", "S", "S"],
                "weekdaysFull": ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
                "prev": "Mês anterior",
                "next": "Próximo mês",
                "choose": "Escolha uma data",
            },
            "bk": BOOKING["pt"],
            "wa": WA_WIDGET["pt"],
        },
        "not_found_title": "Página não encontrada.",
        "not_found_lead": "O endereço pode ter mudado. Volte para o início e escolha sua experiência.",
        "not_found_cta": "Voltar ao início",
    },

    "en": {
        "bk": BOOKING["en"],
        "wa": WA_WIDGET["en"],
        "lang": "en",
        "og_locale": "en_US",
        "path": "/en/",
        "title": "Good Vibes Va'a — Outrigger canoe club at Praia da Preguiça, Salvador",
        "description": "Outrigger canoe (va'a) club at Praia da Preguiça in Salvador, Brazil. Sunrise and sunset paddles, classes, training plans and private experiences on the Bay of All Saints.",
        "skip": "Skip to content",
        "brand_sub": "Outrigger canoe club",
        "nav": [("agendar", "Book"), ("#clube", "The Club"), ("#comunidade", "Local Community"), ("#experiencias", "Experiences"), ("#faq", "FAQ"), ("produtos", "Products")],
        "nav_produtos": "Products",
        "menu_word": "Menu",
        "menu_label": "Navigation menu",
        "menu_cta": "Book a paddle",
        "menu_contact": "Contact",
        "lang_label": "Language",
        "cta_team": "Talk to the team",
        "menu_open": "Open menu",
        "menu_close": "Close menu",
        "hero_place": "Praia da Preguiça, Salvador, Brazil",
        "hero_word": "Paddle!",
        "hero_title": "Find your rhythm at sea.",
        "hero_sub": "Paddling experiences, classes and a community brought together by the outrigger canoe on the Bay of All Saints.",
        "hero_cta1": "Book a paddle",
        "hero_play": "Watch on Instagram",
        "hero_play_aria": "Watch the club's videos on Instagram",
        "hero_slot": "Official photo: crew paddling at sunrise on the Bay of All Saints · 2400×1600 · hero.jpg",
        "hero_alt": "Good Vibes Va'a crew paddling an outrigger canoe at sunrise on the Bay of All Saints",

        "credibility_label": "Where we are and how to join",
        "credibility": ["Gympass", "TotalPass", "Praia da Preguiça", "Salvador · Bahia"],
        "photo_slot_prefix": "Official photo:",

        "about_statement": "In a canoe, nobody paddles alone. Every stroke depends on the rhythm of the person beside you, and that is what turns a class into a community.",
        "kicker_journeys": "Experiences",
        "kicker_club": "The club",
        "kicker_community": "Community",
        "kicker_shop": "Moda Good Vibes",
        "kicker_info": "Where and how",
        "kicker_closing": "Book your paddle",
        "kicker_legal": "Document",
        "journeys_title": "Three ways onto the water.",
        "journeys_lead": "Pick the path that fits you. Each one starts its own conversation with the team.",
        "journeys": [
            ("#experimentar", "I want to try it", "Paddles and your first session, at sunrise or sunset.", "See paddles"),
            ("#treinar", "I want to train", "Drop-in classes, monthly plans and Gympass or TotalPass check-in.", "See plans"),
            ("#particular", "I want a private experience", "Groups, birthdays, companies and private outings.", "Request a quote"),
        ],

        "offers_title": "What we offer",
        "offers_lead": "From your first stroke to training with the crew. Times and prices are confirmed by the team when you book.",
        "offers_cta": "See dates and book",
        "offer_cards": [
            ("#experimentar", "hero", "Sunrise and sunset", "Paddle · prices on request", "The city seen from inside the bay, at the start or the end of the day."),
            ("#experimentar", "community_4", "First paddle", "Beginners · with a captain", "Technique and safety on the sand, then the sea. No experience needed."),
            ("#treinar", "community_1", "Training and plans", "Drop-in · monthly · Gympass and TotalPass", "A training routine with the crew and guidance from the captains."),
            ("#particular", "community_3", "Private", "Groups · birthdays · companies", "The canoe just for your group, with a route agreed with the team."),
        ],

        "reasons_title": "Why paddle with us",
        "reasons_lead": "An outrigger canoe club with captains, a crew and one of the most beautiful settings in Salvador.",
        "reasons": [
            ("captain", "Captains in charge", "Jesse and Nala lead every outing, from the sand to the return."),
            ("shield", "Safety first", "Paddling and safety instructions before you head out."),
            ("pin", "Best location", "Praia da Preguiça, facing the Bay of All Saints."),
            ("crew", "Community", "Training sessions, events and a year of stories at sea."),
        ],

        "moments_label": "Club moments",
        "moments": [
            ("community_1", "After training", "The crew together on the sand at Preguiça."),
            ("community_2", "Pink October", "A paddle for awareness."),
            ("community_3", "One year of Good Vibes", "A year of stories at sea."),
            ("product_2", "Moda Good Vibes", "The club's identity beyond the water."),
        ],
        "carousel_prev": "See previous moments",
        "carousel_next": "See next moments",

        "a_kicker": "I want to try it",
        "a_title": "Your first time in an outrigger canoe.",
        "a_lead": "No experience needed. The captains walk you through technique, timing and safety before you head out.",
        "a_offers": [
            ("First-time session", "For people who have never paddled. An introduction to the sport, guided by a captain."),
            ("Sunrise paddle", "An early start, calm water and the city waking up, seen from the bay."),
            ("Sunset paddle", "Salvador's late afternoon, seen from inside the Bay of All Saints."),
            ("Sea tour", "For visitors who want to see the city's waterfront and history from the water."),
        ],
        "a_note": "<strong>Duration, times and prices</strong> depend on the experience and sea conditions. The team confirms everything on WhatsApp before your booking.",
        "a_form_title": "Request a booking",
        "a_form_intro": "Your request goes straight to the team on WhatsApp, who confirm your booking.",
        "a_wa_intro": "Hi Good Vibes Va'a! I'd like to request a paddle booking:",
        "a_options": [("primeira", "First-time session"), ("nascer", "Sunrise paddle"), ("por", "Sunset paddle"), ("turismo", "Sea tour")],

        # --- "I want to try it" booking, mode "off" ------------------------
        # Ver a nota em português: mesma composição centralizada, com o texto
        # longo recolhido no accordion "Before you paddle".
        "a_head_title": "Your first time in the canoe.",
        "a_head_sub": "Choose your experience, pick a date and come see Salvador from the water.",
        "a_cards": [
            ("primeira", "First-Time Session", "An introduction to the outrigger canoe, made for beginners."),
            ("nascer", "Sunrise", "A paddle in the first hours of the morning."),
            ("por", "Sunset", "A late-afternoon outing, with Salvador and the Bay of All Saints as the backdrop."),
            ("turismo", "Sea Tour", "The city's waterfront and history, seen from the water."),
        ],
        "a_cards_legend": "Choose your experience",
        "a_cta": "Request a booking",
        "a_before_title": "Before you paddle",
        "a_before": [
            "No experience needed: the captains walk you through technique and timing before you head out.",
            "Every outing starts with a safety briefing on the sand, with the captain.",
            "Bring light clothes, sunscreen, water and a dry change of clothes.",
            "Duration, times and prices depend on the experience and sea conditions — the team confirms everything on WhatsApp.",
        ],
        "f_email": "Email",
        "f_optional": "optional",
        "f_group_size": "Group size",

        # --- /agendar/ page — ver a nota em português no bloco "pt" -------
        # O slug é igual nos dois idiomas, como todas as rotas do site.
        "agendar_path": "/en/agendar/",
        "agendar_title": "Book your paddle — Good Vibes Va'a",
        "agendar_description": "Choose your outrigger canoe experience — first paddle, training or a private outing — and send your request to the club team.",
        "agendar_kicker": "Bookings",
        "agendar_h1": "Which experience do you want?",
        "agendar_hint": "Swipe or use the arrows to see all three experiences.",
        "xp_cards": [
            ("experimentar", "community_4", "I want to try it",
             "Your first paddle or an outing in the canoe."),
            ("treinar", "community_1", "I want to train",
             "Regular training, drop-in classes and plans."),
            ("particular", "community_3", "I want a private experience",
             "Groups, events, birthdays and private outings."),
        ],
        "xp_explore": "Explore experience",
        "xp_steps": ["Set up", "Date", "Your details", "Confirm"],
        "xp_back_all": "See all experiences",
        "xp_next": "Continue",
        "xp_prev": "Back",
        "xp_prev_label": "Previous experience",
        "xp_next_label": "Next experience",
        "xp_review_title": "Confirm your request",
        "xp_review_lead": "Check your details before sending. The team confirms the booking on WhatsApp.",
        "xp_edit": "Change",
        "xp_date_title": "When do you want to paddle?",
        "xp_date_title_treinar": "When do you want to start?",
        "xp_contact_title": "How do we reach you?",
        "xp_submit": "Request a booking",
        "xp_resumed": "We picked up where you left off.",

        "f_name": "Your name",
        "f_experience": "Experience",
        "f_date": "Preferred date",
        "f_people": "Number of people",
        "f_notes": "Notes",
        "f_notes_hint": "Children's ages, whether it's your first time, questions.",
        "f_choose": "Select",
        "f_more": "Add a note",
        "tab_short": ["Try it", "Train", "Private"],
        "f_submit": "Send on WhatsApp",
        "f_privacy": "Your details are only used to answer this request, through the WhatsApp message you send yourself.",
        "f_privacy_site": "Your details are only used to answer this request, on the WhatsApp number you provided.",

        "bring_title": "What to bring",
        "bring": ["Swimwear", "Sunscreen", "Water", "Cap or visor", "Dry bag for your phone"],

        "team_title": "Who paddles with you.",
        "team_lead": "The captains lead every outing, from the first briefing on the sand to the return.",
        "captain_role": "Captain",
        "captain_role_f": "Captain",
        "captain_slot": "Official photo: captain's portrait in the canoe · 1200×1500",

        "community_title": "A community that meets at sea.",
        "community_lead": "Sunrise training, campaigns like Pink October and a year of stories told by the people who paddle with us.",
        "community_cta": "Watch testimonials on Instagram",
        "community_note": "Video testimonials from people who have paddled with the club are on our Instagram.",

        "b_kicker": "I want to train",
        "b_title": "Plans and ways to take part.",
        "b_lead": "For anyone who wants outrigger paddling in their routine, to improve their technique and to train with the crew.",
        "plans": [
            ("Drop-in class", "Try the club's training or add it to your routine.", "Prices on request"),
            ("Monthly plan", "Regular training with the crew, coaching from the captains and a place in the community.", "Prices on request"),
            ("Gympass and TotalPass", "Check in with your plan. Ask the team which plans are eligible.", "Through your app"),
        ],
        "b_note": "<strong>Training times</strong>: the team sends the current schedule on WhatsApp.",
        "b_form_title": "I want to train with the club",
        "b_form_intro": "The team replies with times, prices and how to sign up.",
        "b_wa_intro": "Hi Good Vibes Va'a! I'd like to train with the club:",
        "b_options": [("avulsa", "Drop-in class"), ("mensal", "Monthly plan"), ("app", "Gympass or TotalPass")],
        "f_modality": "Option",
        "f_period": "Preferred time",
        "f_periods": [("manha", "Morning"), ("tarde", "Late afternoon"), ("flex", "Either")],
        "f_experience_level": "Have you paddled before?",
        "f_levels": [("nunca", "Never"), ("algumas", "A few times"), ("pratico", "I paddle regularly")],

        "c_kicker": "I want a private experience",
        "c_title": "The canoe, just for your group.",
        "c_lead": "Private outings to celebrate, bring a team together or enjoy the sea with the people you choose.",
        "formats": [
            ("Groups", "Friends, families and travel groups."),
            ("Birthdays", "A celebration at sea, at sunrise or sunset."),
            ("Corporate events", "Team building and wellbeing activities for companies."),
            ("Private experiences", "An exclusive outing, planned with the team."),
        ],
        "c_form_title": "Request a quote",
        "c_form_intro": "The team replies with format, availability and prices.",
        "c_wa_intro": "Hi Good Vibes Va'a! I'd like a quote for a private experience:",
        "c_options": [("grupo", "Group"), ("aniversario", "Birthday"), ("corporativo", "Corporate event"), ("privada", "Private experience")],
        "f_type": "Type of experience",
        "f_company": "Company (optional)",
        "f_details": "Tell us more",
        "f_details_hint": "Occasion, preferred time, whether the group has paddled before.",
        "f_submit_quote": "Request a quote on WhatsApp",

        "shop_title": "Good Vibes beyond the water.",
        "shop_lead": "Pieces from the Moda Good Vibes line that carry the club's identity into everyday life.",
        "shop_slot": "Official product photo · 1200×1500 · produto-{n}.jpg",
        "shop_cta": "Order on WhatsApp",
        "shop_wa": "Hi Good Vibes Va'a! I'd like to know about the Moda Good Vibes products.",

        "shop_teaser_title": "Take Good Vibes with you.",
        "shop_teaser_text": "Discover our collection and carry a bit of the sea's energy into your day.",
        "shop_teaser_cta": "EXPLORE PRODUCTS",

        "shop_intro_kicker": "The club shop",
        "shop_intro_title": "Made for paddling, worn every day.",
        "shop_intro_text": "The Moda Good Vibes line comes out of use: a shirt that holds up to sun and salt, a cap that doesn't fly off mid-stroke, a bag that comes home wet from the beach. Each piece is made in small runs for the club's community.",
        "shop_cat_label": "Categories",
        "shop_cat_all": "All",
        "shop_soon_badge": "Coming soon",
        "shop_soon_title": "New piece",
        "shop_soon_text": "A slot held for the next run of the line. Once the club confirms the piece, it shows up here.",
        "shop_collections_kicker": "Collections",
        "shop_collections_title": "What exists today, and what's coming.",
        "shop_collections": [
            ("Good Vibes line", "Everyday apparel and accessories for club life, with the circular logo.", "product_1", False),
            ("Commemorative", "The cotton shirt made to mark the club's first year.", "product_5", False),
            ("Next collection", "In production. The team confirms pieces, sizes and prices before publishing.", "product_3", True),
        ],
        "shop_howto_title": "How to buy today",
        "shop_howto_text": "The shop has no online payment yet. Pick a piece, message the team on WhatsApp, and they confirm availability, size and price before any payment.",
        "produtos_path": "/en/produtos/",
        "produtos_title": "Products — Good Vibes Va'a Shop",
        "produtos_description": "Official pieces from the Moda Good Vibes Va'a line: shirts, cap, visor and drawstring bag with the club's identity.",
        "produtos_price_request": "Price on request",
        "produtos_stock": {"available": "Available", "low": "Only a few left", "out": "Sold out", "unknown": "Availability to be confirmed"},
        "produtos_size_label": "Size",
        "produtos_color_label": "Color",
        "produtos_buy_cta": "Buy on WhatsApp",
        "produtos_close": "Close details",
        "produtos_wa_intro": "Hi Good Vibes Va'a! I'm interested in this item: {product}",
        "produtos_empty": "New pieces coming soon.",

        "contato_path": "/en/contato/",
        "contato_title": "Contact — Good Vibes Va'a",
        "contato_description": "Talk to the Good Vibes Va'a team: send a message through the form, reach out on WhatsApp, or message us on Instagram.",
        "contato_h1": "Let's talk.",
        "contato_lead": "We're here to help you live the Good Vibes experience.",
        "contato_kicker": "Support",
        "contato_mail_title": "Send a message",
        "contato_mail_text": "Tell us what you need and the team will reply to the email address you provide.",
        "contato_wa_title": "WhatsApp",
        "contato_wa_text": "For anyone who prefers to talk right away — it's the fastest channel for booking questions.",
        "contato_wa_cta": "Open WhatsApp chat",
        "contato_other_title": "Other channels",
        "contato_other_text": "The club also replies to Instagram direct messages, where the videos and news from each outing live.",
        "contato_other_cta": "Message on Instagram",
        "contato_hours_title": "Before you write",
        "contato_hours_text": "Times, prices and available seats change with the sea and the club's schedule — the team confirms everything in their reply. Frequently asked questions are already answered on the home page.",
        "contato_hours_cta": "See the FAQ",
        "privacy_path": "/en/privacidade/",
        "legal_back": "Back to home",
        "legal_draft_label": "Draft",
        "legal_draft_note": "Document in progress: not yet validated by the club or legally reviewed. It does not constitute a policy in force.",
        "legal_pending": "to be defined",
        "legal_pending_aria": "Still an open point",
        "legal_index": "On this page",
        "legal_docs_title": "Club documents",

        "ct_name": "Full name",
        "ct_email": "Email",
        "ct_subject": "Subject",
        "ct_message": "Message",
        "ct_submit": "Send message",
        "ct_privacy": "We use your data only to reply to this message. See the privacy policy.",
        "ct_subjects": [("reserva", "Booking an experience"), ("treino", "Classes and training"), ("particular", "Groups and companies"), ("produtos", "Products"), ("outro", "Something else")],

        "place_title": "Praia da Preguiça, Salvador.",
        "place_lead": "Outings start from Praia da Preguiça, facing the Bay of All Saints.",
        "place_items": [
            ("Meeting point", "Praia da Preguiça, Salvador, Bahia. The exact spot is sent with your confirmation."),
            ("Contact", "+55 71 99978-9710 (WhatsApp)"),
            ("Instagram", SITE["instagram_handle"]),
        ],
        "place_maps": "Open in Google Maps",
        "map_title": "Map of Praia da Preguiça, Salvador",

        "faq_title": "Questions.",
        "faq_lead": "Didn't find your answer? Talk to the team.",
        "faq": [
            ("Do I need experience to paddle?", "No. The first-time session is designed for people who have never paddled, and the captains cover technique and safety before you head out."),
            ("How do I book?", "Send your request through the form or straight on WhatsApp. The team confirms your booking along with the time, price and meeting point."),
            ("Do you accept Gympass and TotalPass?", "Yes. Ask the team which plans and options are eligible for check-in."),
            ("What if the sea conditions are poor?", "The team checks sea conditions before every outing and will get in touch to arrange a new date if needed."),
            ("What should I bring?", "Swimwear, sunscreen, water, a cap or visor and a dry bag for your phone."),
            ("Can children join?", "Let the team know the children's ages to find out which experiences suit them."),
            ("Do you run corporate events?", "Yes. Use the private experience form to request a quote."),
        ],

        "final_title": "The sea is waiting.",
        "final_lead": "Choose your experience or talk to the team directly.",

        "footer_about": "Outrigger canoe club at Praia da Preguiça, facing the Bay of All Saints. Paddles, classes and training for first-timers and for people who already race.",
        "footer_brand_cta": "Book an experience",
        "footer_nav": "Explore",
        "footer_service": "Support",
        "footer_service_text": "Questions about experiences, bookings or products? The team replies through the contact page.",
        "footer_service_cta": "Talk to the team",
        "footer_ig_label": "Good Vibes Va'a on Instagram",
        "footer_location_label": "Where we paddle",
        "footer_location": "Praia da Preguiça · Salvador · Bahia",
        "footer_location_cta": "How to get there",
        "footer_credit": "Site by",
        "footer_follow": "Follow",
        "footer_rights": "All rights reserved.",
        "dock_book": "Book now",
        "i18n": {
            "locale": "en",
            "menuOpen": "Open menu",
            "menuClose": "Close menu",
            "required": "Please fill in this field.",
            "datePast": "Choose a date from today onwards.",
            "minPeople": "Enter at least 1 person.",
            "openedWhatsapp": "We opened WhatsApp with your request. Just send the message.",
            "sent": "Request sent. The team will reply soon.",
            "sendError": "We couldn't send it right now. Try again or message the team on WhatsApp.",
            "invalidEmail": "Enter a valid email address.",
            "contact": {
                "sending": "Sending…",
                "ok": "Message sent. The team will reply to the email address you gave us.",
                "offline": "Email sending isn't active on this site yet. Message the team on WhatsApp — the button is right next to this one.",
                "error": "We couldn't send it right now. Try again in a moment or message the team on WhatsApp.",
            },
            # Ver a nota em português no bloco "pt".
            "cal": {
                "months": ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"],
                "weekdays": ["S", "M", "T", "W", "T", "F", "S"],
                "weekdaysFull": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "prev": "Previous month",
                "next": "Next month",
                "choose": "Pick a date",
            },
            "bk": BOOKING["en"],
            "wa": WA_WIDGET["en"],
        },
        "not_found_title": "Page not found.",
        "not_found_lead": "The address may have changed. Go back to the home page and choose your experience.",
        "not_found_cta": "Back to home",
    },
}

# ---------------------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------------------
ICON_WA = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 1.9s.8 2.2.9 2.4c.1.1 1.6 2.5 3.9 3.5 1.5.6 2 .7 2.7.6.4-.1 1.3-.5 1.5-1 .2-.5.2-1 .1-1.1l-.5-.2Z"/></svg>'
ICON_ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 12h15M13 6l6 6-6 6"/></svg>'
ICON_IG = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3.5" y="3.5" width="17" height="17" rx="4.5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r=".9" fill="currentColor"/></svg>'

ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>'
ICON_PREV = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 5l-7 7 7 7"/></svg>'
ICON_NEXT = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 5l7 7-7 7"/></svg>'

# Ícones em gota de "Por que remar com a gente". A chave é a primeira
# posição de cada tupla de CONTENT[...]["reasons"].
ICONS_REASON = {
    "captain": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="7" r="3.5"/><path d="M5 20c.6-4 3.4-6 7-6s6.4 2 7 6"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    "crew": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="8" cy="9" r="3"/><circle cx="16" cy="9" r="3"/><path d="M2 20c.5-3 2.8-5 6-5s5.5 2 6 5M10 20c.5-3 2.8-5 6-5s5.5 2 6 5"/></svg>',
}


def e(s):
    return escape(str(s), quote=True)


def eyebrow(text, cls=""):
    """Olho editorial: versalete douradinho com filete curto à esquerda."""
    return f'<p class="eyebrow{(" " + cls) if cls else ""}">{e(text)}</p>'


def slug(text, fallback):
    """Âncora estável a partir de um título de seção (usada no índice da
    página de privacidade). Sem acento, sem pontuação, sempre minúscula."""
    import unicodedata
    norm = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    out = "".join(ch if ch.isalnum() else "-" for ch in norm.lower()).strip("-")
    while "--" in out:
        out = out.replace("--", "-")
    return out[:48] or fallback


def wa_link(text=None):
    url = f"https://wa.me/{SITE['whatsapp']}"
    if text:
        from urllib.parse import quote
        url += "?text=" + quote(text)
    return url


def media(photo_key, locale, slot, prefix, cls="", w=1600, h=1000, eager=False, light=False):
    """Slot de fotografia, lido do dicionário PHOTOS. Mostra a foto oficial
    se assets/img/<file> existir; caso contrário, o slot exibe a descrição
    da foto a inserir. Trocar a foto, o alt ou o enquadramento é editar a
    entrada correspondente em PHOTOS — nada aqui precisa mudar."""
    p = PHOTOS[photo_key]
    alt = p["alt_pt"] if locale == "pt" else p["alt_en"]
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    klass = "media" + (" media--light" if light else "") + (f" {cls}" if cls else "")
    return (
        f'<figure class="{klass}" data-slot="{e(slot)}">'
        f'<img src="{prefix}assets/img/{p["file"]}" alt="{e(alt)}" width="{w}" height="{h}" '
        f'style="--focus:{e(p["focus"])}" {loading} decoding="async" onerror="this.remove()">'
        f"</figure>"
    )


def resolve_modalities(code, prefix):
    """Injeta a URL da foto do instrutor (quando houver instructorKey) nas
    atividades de cada modalidade, pro JS do booking.js não precisar
    conhecer PHOTOS/prefix — só recebe uma URL pronta."""
    out = []
    for m in MODALITIES[code]:
        activities = []
        for a in m["activities"]:
            a2 = dict(a)
            key = a.get("instructorKey")
            if key and key in PHOTOS:
                a2["instructorPhoto"] = f'{prefix}assets/img/{PHOTOS[key]["file"]}'
            activities.append(a2)
        out.append({**m, "activities": activities})
    return out


def resolve_products(code, prefix):
    """Monta a lista de produtos pro HTML/JS da página /produtos: nome,
    descrição e categoria no idioma certo, foto resolvida via PHOTOS,
    preço formatado (ou "sob consulta" quando price_cents é None — nunca
    inventamos um valor)."""
    c = CONTENT[code]
    out = []
    for p in PRODUCTS:
        photo = PHOTOS.get(p["photo"], {})
        price_cents = p["price_cents"]
        price_label = (
            "R$ " + f"{price_cents / 100:.2f}".replace(".", ",")
            if price_cents is not None
            else c["produtos_price_request"]
        )
        out.append({
            "id": p["id"],
            "name": p["name"][code],
            "description": p["description"][code],
            "category": p["category"][code],
            "priceCents": price_cents,
            "priceLabel": price_label,
            "sizes": p["sizes"],
            "colors": [{"name": col[code], "hex": col["hex"]} for col in p["colors"]],
            "stock": p["stock"],
            "stockLabel": c["produtos_stock"][p["stock"]],
            "image": f'{prefix}assets/img/{photo.get("file", "")}',
            "imageAlt": photo.get(f"alt_{code}", p["name"][code]),
        })
    return out


def resolve_campaign(code):
    """Resolve a campanha ativa do pop-up de newsletter pro JS.

    "raffle" (sorteio/concorrer a prêmio) é tratado como DESLIGADO aqui a
    não ser que CAMPAIGN["legal_cleared"] esteja True de verdade — ver o
    aviso completo em newsletter_content.py. NÃO remover esta checagem."""
    if not CAMPAIGN["enabled"]:
        return {"enabled": False}
    if CAMPAIGN["type"] == "raffle" and not CAMPAIGN.get("legal_cleared"):
        return {"enabled": False}
    data = CAMPAIGN[code]
    return {
        "enabled": True,
        "type": CAMPAIGN["type"],
        "key": f'{CAMPAIGN["type"]}-{code}',
        "title": data["title"],
        "text": data["text"],
        "couponCode": data.get("coupon_code") or None,
    }


def resolve_xp(code, prefix):
    """Carga do carrossel de /agendar/ para experience.js.

    Entrega cartões com a URL da foto já resolvida e, por jornada, os
    campos do passo "Configurar". As opções são as mesmas listas que as
    jornadas sempre usaram (a_options, b_options, c_options, f_periods,
    f_levels) — a página nova não inventa vocabulário, só o reapresenta.
    O JS não conhece PHOTOS nem prefix: recebe tudo pronto.
    """
    c = CONTENT[code]

    def opts(pairs):
        return [{"value": v, "label": t} for v, t in pairs]

    cards = []
    for key, photo_key, title, desc in c["xp_cards"]:
        photo = PHOTOS[photo_key]
        cards.append({
            "key": key,
            "title": title,
            "desc": desc,
            "image": f'{prefix}assets/img/{photo["file"]}',
            "alt": photo[f"alt_{code}"],
            "focus": photo.get("focus", "center"),
        })

    # Cada jornada pede só o que lhe diz respeito — é isso que mantém a
    # tela de treino livre de texto sobre passeio turístico, e vice-versa.
    config = {
        "experimentar": [
            {"id": "tipo", "label": c["f_experience"], "type": "choice", "options": opts(c["a_options"])},
            {"id": "pessoas", "label": c["f_people"], "type": "number", "min": 1, "max": 60, "value": 1},
        ],
        "treinar": [
            {"id": "modalidade", "label": c["f_modality"], "type": "choice", "options": opts(c["b_options"])},
            {"id": "periodo", "label": c["f_period"], "type": "choice", "options": opts(c["f_periods"])},
            {"id": "nivel", "label": c["f_experience_level"], "type": "choice", "options": opts(c["f_levels"])},
        ],
        "particular": [
            {"id": "tipo", "label": c["f_type"], "type": "choice", "options": opts(c["c_options"])},
            {"id": "pessoas", "label": c["f_group_size"], "type": "number", "min": 2, "max": 200, "value": 6},
        ],
    }

    # A mensagem de WhatsApp de cada jornada continua sendo a de sempre.
    intro = {
        "experimentar": c["a_wa_intro"],
        "treinar": c["b_wa_intro"],
        "particular": c["c_wa_intro"],
    }

    return {
        "cards": cards,
        "config": config,
        "intro": intro,
        "steps": c["xp_steps"],
        "explore": c["xp_explore"],
        "backAll": c["xp_back_all"],
        "next": c["xp_next"],
        "prev": c["xp_prev"],
        "prevLabel": c["xp_prev_label"],
        "nextLabel": c["xp_next_label"],
        "reviewTitle": c["xp_review_title"],
        "reviewLead": c["xp_review_lead"],
        "edit": c["xp_edit"],
        "dateTitle": c["xp_date_title"],
        "dateTitleTreinar": c["xp_date_title_treinar"],
        "contactTitle": c["xp_contact_title"],
        "submit": c["xp_submit"],
        "resumed": c["xp_resumed"],
        "choose": c["f_choose"],
        "optional": c["f_optional"],
        "labels": {
            "experience": c["f_experience"],
            "date": c["f_date"],
            "name": c["f_name"],
            "email": c["f_email"],
            "phone": c["bk"]["phone"],
            "notes": c["f_notes"],
            "more": c["f_more"],
        },
    }


def nav_href(code, item, page):
    """Resolve um item de CONTENT[...]["nav"] para href.

    Item que começa com "#" é âncora da home: na própria home fica hash
    puro (o JS de abas depende disso, ver initTabs em site.js); nas outras
    rotas vira link absoluto de volta pra home (`/#reservar`). Qualquer
    outro valor é slug de rota ("produtos", "contato") e vira `/produtos/`
    no idioma certo."""
    root = "/" if code == "pt" else "/en/"
    if item.startswith("#"):
        return item if page == "home" else f"{root}{item}"
    return f"{root}{item}/"


def offer_href(code, anchor):
    """Cartões de "O que oferecemos" → /agendar/ já na jornada certa.

    Eles apontavam para as âncoras das abas na home (`#experimentar`);
    agora levam para a página de reserva com `?xp=`, que o experience.js
    lê para abrir aquele fluxo direto, sem passar pelo carrossel. Mantém
    o link útil sem JS: cai na página e o carrossel abre no primeiro.
    """
    root = "/" if code == "pt" else "/en/"
    return f"{root}agendar/?xp={anchor.lstrip('#')}"


def nav_items_html(code, page, cls=""):
    c = CONTENT[code]
    parts = []
    for item, label in c["nav"]:
        cur = ' aria-current="page"' if (not item.startswith("#") and item == page) else ""
        parts.append(f'<li><a{cls} href="{nav_href(code, item, page)}"{cur}>{e(label)}</a></li>')
    return "".join(parts)


def lang_switch_html(code, page, extra_style=""):
    c = CONTENT[code]
    pt_cur = code == "pt"
    other_root = "/en/" if code == "pt" else "/"
    page_suffix = "" if page == "home" else f"{page}/"
    style_attr = f' style="{extra_style}"' if extra_style else ""
    return (
        f'<nav class="lang-switch"{style_attr} aria-label="{e(c["lang_label"])}">'
        + ('<span aria-current="true"><b>PT</b></span>' if pt_cur else f'<a href="{other_root}{page_suffix}" hreflang="pt-BR" lang="pt-BR">PT</a>')
        + ('<span aria-current="true"><b>EN</b></span>' if not pt_cur else f'<a href="{other_root}{page_suffix}" hreflang="en" lang="en">EN</a>')
        + "</nav>"
    )


def page_header(code, prefix, page):
    """Cabeçalho: marca, idioma e botão de menu. A navegação inteira vive
    no painel lateral (menu hambúrguer) em TODAS as larguras — não há mais
    barra horizontal de links no desktop.

    O painel fica fora do <header> de propósito: o header usa
    backdrop-filter quando sólido, o que o transforma em bloco de contenção
    e quebraria um descendente `position: fixed`.

    Sem JavaScript o painel continua `inert` (inalcançável) e a navegação
    da página é a do rodapé, que lista os mesmos seis itens."""
    c = CONTENT[code]
    root = "/" if code == "pt" else "/en/"
    brand_href = "./" if page == "home" else root
    solid = "" if page == "home" else " is-solid"
    menu_items = nav_items_html(code, page)
    book_href = nav_href(code, "agendar", page)
    return f"""
<a class="skip" href="#conteudo">{e(c['skip'])}</a>
<header class="header{solid}">
  <div class="wrap wrap--wide">
    <a class="brand" href="{brand_href}" aria-label="{e(SITE['name'])}">
      <img class="brand-logo" src="{prefix}assets/img/logo.png" alt="" width="40" height="40" onerror="this.remove()">
      <span class="brand-word">Good Vibes Va'a<small>{e(c['brand_sub'])}</small></span>
    </a>
    <div class="header-actions">
      {lang_switch_html(code, page)}
      <button class="menu-btn" type="button" data-menu-toggle aria-expanded="false" aria-controls="menu-drawer" aria-label="{e(c['menu_open'])}">
        <span class="menu-btn-bars" aria-hidden="true"></span>
        <span class="menu-btn-word" aria-hidden="true">{e(c['menu_word'])}</span>
      </button>
    </div>
  </div>
</header>
<div class="menu-overlay" data-menu-overlay></div>
<div class="menu-drawer" id="menu-drawer" role="dialog" aria-modal="true" aria-label="{e(c['menu_label'])}" inert>
  <div class="menu-drawer-in">
    <div class="menu-drawer-head">
      <span class="eyebrow">{e(c['menu_label'])}</span>
      <button class="menu-close" type="button" data-menu-close aria-label="{e(c['menu_close'])}">
        <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 5l14 14M19 5L5 19"/></svg>
      </button>
    </div>
    <nav aria-label="{e(c['footer_nav'])}">
      <ul class="menu-list">{menu_items}</ul>
    </nav>
    <a class="btn btn--gold menu-book" href="{book_href}">{e(c['menu_cta'])}</a>
    <div class="menu-drawer-foot">
      <a class="menu-contact" href="{root}contato/">{e(c['menu_contact'])}</a>
      <div class="menu-drawer-foot-end">
        <a class="menu-ig" href="{SITE['instagram']}" target="_blank" rel="noopener" aria-label="{e(c['footer_ig_label'])}">{ICON_IG}</a>
        {lang_switch_html(code, page)}
      </div>
    </div>
  </div>
</div>"""


def legal_links_html(code, page):
    """Links dos quatro documentos do clube, na ordem do rodapé. Lê
    LEGAL — incluir um documento novo é adicionar uma entrada lá."""
    root = "/" if code == "pt" else "/en/"
    parts = []
    for key, doc in LEGAL.items():
        label = doc[code]["h1"].rstrip(".")
        cur = ' aria-current="page"' if page == key else ""
        parts.append(f'<a href="{root}{doc["slug"]}/"{cur}>{e(label)}</a>')
    return "".join(parts)


def page_footer(code, prefix, page):
    """Rodapé em quatro áreas (marca, navegação, atendimento, redes), faixa
    institucional discreta com a localização e barra inferior com os
    documentos do clube.

    O telefone não aparece em lugar nenhum do rodapé de propósito: o
    atendimento passa pela página de contato, que concentra formulário,
    WhatsApp e Instagram."""
    c = CONTENT[code]
    root = "/" if code == "pt" else "/en/"
    # O pop-up de newsletter sai da home: a home abre direto no quadro de
    # reservas e um overlay por cima dela competiria com a reserva.
    nl_widget = "" if page == "home" else '<div class="nl-widget" data-nl-widget></div>'
    dock_href = nav_href(code, "agendar", page)
    local_href = f"{root}#local" if page != "home" else "#local"
    return f"""
<footer class="footer">
  <div class="wrap wrap--wide">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="brand" href="{root}" aria-label="{e(SITE['name'])}">
          <img class="brand-logo" src="{prefix}assets/img/logo.png" alt="" width="40" height="40" onerror="this.remove()">
          <span class="brand-word">Good Vibes Va'a<small>{e(c['brand_sub'])}</small></span>
        </a>
        <p class="footer-about">{e(c['footer_about'])}</p>
        <a class="btn btn--gold btn--sm" href="{dock_href}">{e(c['footer_brand_cta'])}</a>
      </div>
      <div class="footer-col">
        <h2>{e(c['footer_nav'])}</h2>
        <ul>{nav_items_html(code, page)}</ul>
      </div>
      <div class="footer-col">
        <h2>{e(c['footer_service'])}</h2>
        <p class="footer-col-text">{e(c['footer_service_text'])}</p>
        <a class="link-arrow footer-service-cta" href="{root}contato/">{e(c['footer_service_cta'])}{ICON_ARROW}</a>
      </div>
      <div class="footer-col footer-social">
        <h2>{e(c['footer_follow'])}</h2>
        <a class="footer-ig" href="{SITE['instagram']}" target="_blank" rel="noopener" aria-label="{e(c['footer_ig_label'])}">{ICON_IG}</a>
      </div>
    </div>
    <div class="footer-place">
      <span class="footer-place-label">{e(c['footer_location_label'])}</span>
      <span class="footer-place-value">{e(c['footer_location'])}</span>
      <a class="footer-place-link" href="{local_href}">{e(c['footer_location_cta'])}</a>
    </div>
    <div class="footer-bottom">
      <nav class="footer-legal" aria-label="{e(c['legal_docs_title'])}">{legal_links_html(code, page)}</nav>
      <div class="footer-bottom-end">
        <span>© <span data-year></span> Good Vibes Va'a. {e(c['footer_rights'])}</span>
        <span class="footer-credit">{e(c['footer_credit'])} <a href="https://asterops.co/" target="_blank" rel="noopener">Aster</a></span>
      </div>
    </div>
  </div>
</footer>
<div class="dock" inert>
  <a class="btn btn--gold" href="{dock_href}">{e(c['dock_book'])}</a>
</div>
<div class="wa-widget" data-wa-widget data-default="{e(c['wa']['default'])}">
  <div class="wa-card" hidden>
    <div class="wa-head">
      <div><strong>{e(c['wa']['title'])}</strong><span>{e(c['wa']['status'])}</span></div>
      <button type="button" data-wa-close aria-label="{e(c['wa']['close'])}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 5l14 14M19 5L5 19"/></svg></button>
    </div>
    <p class="wa-msg">{e(c['wa']['msg'])}</p>
    <form data-wa-form>
      <textarea rows="2" placeholder="{e(c['wa']['placeholder'])}" aria-label="{e(c['wa']['placeholder'])}"></textarea>
      <button type="submit" class="btn btn--solid">{ICON_WA}{e(c['wa']['send'])}</button>
    </form>
  </div>
  <button type="button" class="wa-fab" data-wa-toggle aria-expanded="false" aria-label="{e(c['wa']['open'])}">{ICON_WA}</button>
</div>
{nl_widget}"""


def page_scripts(code, prefix):
    c = CONTENT[code]
    config = {
        "whatsapp": SITE["whatsapp"],
        "bookingMode": SITE["booking_mode"],
        "apiBase": SITE["api_base"],
        "seats": SITE["booking_seats"],
        "campaign": resolve_campaign(code),
    }
    i18n_data = dict(c["i18n"])
    i18n_data["modalities"] = resolve_modalities(code, prefix)
    nl_photo = PHOTOS["community_1"]
    i18n_data["newsletter"] = dict(NEWSLETTER[code])
    i18n_data["newsletter"]["image"] = f'{prefix}assets/img/{nl_photo["file"]}'
    i18n_data["products"] = resolve_products(code, prefix)
    i18n_data["produtos"] = {
        "sizeLabel": c["produtos_size_label"],
        "colorLabel": c["produtos_color_label"],
        "buyCta": c["produtos_buy_cta"],
        "close": c["produtos_close"],
        "waIntro": c["produtos_wa_intro"],
    }
    i18n_data["xp"] = resolve_xp(code, prefix)
    i18n_data["privacyHref"] = c["privacy_path"]
    i18n_data["produtosHref"] = c["produtos_path"]
    return f"""
<script type="application/json" id="i18n">{json.dumps(i18n_data, ensure_ascii=False)}</script>
<script>window.GVV_CONFIG = {json.dumps(config)};</script>
<script src="{prefix}assets/js/site.js" type="module"></script>"""


def field(fid, label, control, hint=None, full=False, error=True):
    h = f'<span class="hint" id="{fid}-hint">{e(hint)}</span>' if hint else ""
    err = f'<span class="field-error" id="{fid}-error" aria-live="polite"></span>' if error else ""
    return f'<div class="field{" field--full" if full else ""}"><label for="{fid}">{e(label)}</label>{h}{control}{err}</div>'


def select(fid, name, label, options, c, required=True):
    opts = f'<option value="">{e(c["f_choose"])}</option>' + "".join(
        f'<option value="{e(v)}">{e(t)}</option>' for v, t in options
    )
    req = " required" if required else ""
    return f'<select id="{fid}" name="{name}" data-label="{e(label)}"{req} aria-describedby="{fid}-error">{opts}</select>'


def text_input(fid, name, label, kind="text", required=True, extra="", hint=False):
    req = " required" if required else ""
    desc = f"{fid}-error" + (f" {fid}-hint" if hint else "")
    return f'<input id="{fid}" name="{name}" type="{kind}" data-label="{e(label)}"{req} aria-describedby="{desc}" {extra}>'


def textarea(fid, name, label, hint=False):
    desc = f' aria-describedby="{fid}-hint"' if hint else ""
    return f'<textarea id="{fid}" name="{name}" data-label="{e(label)}"{desc}></textarea>'


def render(code):
    c = CONTENT[code]
    other = "en" if code == "pt" else "pt"
    prefix = "" if code == "pt" else "../"
    base = SITE["base_url"].rstrip("/")
    canonical = base + c["path"]
    og_image = base + "/assets/img/og.jpg"

    # ---- head ----
    jsonld = {
        "@context": "https://schema.org",
        "@type": "SportsActivityLocation",
        "name": SITE["name"],
        "description": c["description"],
        "url": canonical,
        "telephone": "+" + SITE["whatsapp"],
        "image": og_image,
        "sameAs": [SITE["instagram"]],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Praia da Preguiça",
            "addressLocality": "Salvador",
            "addressRegion": "BA",
            "addressCountry": "BR",
        },
    }
    alternates = (
        f'<link rel="alternate" hreflang="pt-BR" href="{base}/">'
        f'<link rel="alternate" hreflang="en" href="{base}/en/">'
        f'<link rel="alternate" hreflang="x-default" href="{base}/">'
    )

    head = f"""<!doctype html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(c['title'])}</title>
<meta name="description" content="{e(c['description'])}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="theme-color" content="#0D3527">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(c['title'])}">
<meta property="og:description" content="{e(c['description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{c['og_locale']}">
<meta property="og:locale:alternate" content="{CONTENT[other]['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/manrope-latin-standard-normal.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/dmserifdisplay-latin-standard-normal.woff2" crossorigin>
<link rel="preload" as="image" href="{prefix}assets/img/hero.jpg" fetchpriority="high">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>"""

    # ---- header ----
    header = page_header(code, prefix, "home")

    # ---- hero ----
    # Composição de ticket de embarque: manchete grande ancorada à esquerda
    # e, no rodapé do hero, uma faixa horizontal de ponta a ponta com os
    # "fatos" — usa a largura inteira da tela no desktop em vez de empilhar
    # tudo numa coluna estreita à direita (a leitura de "celular ampliado"
    # que este redesenho veio corrigir).
    hero = f"""
<section class="hero" aria-labelledby="hero-title">
  {media('hero', code, c['hero_slot'], prefix, cls='hero-media', w=2400, h=1600, eager=True)}
  <div class="wrap wrap--wide hero-inner">
    <div class="hero-lead">
      <p class="eyebrow hero-place">{e(c['hero_place'])}</p>
      <h1 id="hero-title"><span class="hero-word">{e(c['hero_word'])}</span><span class="hero-h1-line">{e(c['hero_title'])}</span></h1>
      <p class="hero-sub">{e(c['hero_sub'])}</p>
      <div class="btn-row">
        <a class="btn btn--gold" href="{nav_href(code, "agendar", "home")}">{e(c['hero_cta1'])}</a>
        <a class="btn btn--line" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
      </div>
    </div>
    <div class="hero-play-col">
      <a class="hero-play" href="{SITE['instagram']}" target="_blank" rel="noopener" aria-label="{e(c['hero_play_aria'])}">{ICON_PLAY}</a>
      <p class="hero-play-label">{e(c['hero_play'])}</p>
    </div>
  </div>
  <svg class="hero-wave" viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M0 34 C 300 80 520 4 820 30 C 1080 52 1260 60 1440 26 L1440 80 L0 80Z"/></svg>
</section>"""

    # ---- Faixa de credibilidade ----
    cred_items = "".join(f"<li>{e(t)}</li>" for t in c["credibility"])
    credibility = f"""
<section class="credibility" aria-label="{e(c['credibility_label'])}">
  <div class="wrap wrap--wide"><ul>{cred_items}</ul></div>
</section>"""

    # ---- O que oferecemos: quatro cartões sobre a fotografia ----
    # Cada cartão é um link para a jornada de reserva correspondente; o JS
    # de abas (initTabs) intercepta o clique e abre a aba certa.
    offer_cards = "".join(
        f'<a class="offer-card" href="{offer_href(code, href)}">'
        + media(photo, code, f"{c['photo_slot_prefix']} {title}", prefix, cls="media--zoom", w=900, h=700)
        + f'<div class="offer-card-body"><h3 class="offer-card-title">{e(title)}</h3>'
        f'<span class="offer-card-meta">{e(meta)}</span><p>{e(text)}</p></div></a>'
        for href, photo, title, meta, text in c["offer_cards"]
    )
    offer = f"""
<section class="offer band-dark" id="experiencias" aria-labelledby="offers-title">
  {media('community_4', code, f"{c['photo_slot_prefix']} {c['offers_title']}", prefix, cls='offer-media', w=1600, h=1000)}
  <div class="wrap wrap--wide">
    <div class="section-head section-head--center">
      {eyebrow(c['kicker_journeys'])}
      <h2 class="h2" id="offers-title">{e(c['offers_title'])}</h2>
      <p class="lead">{e(c['offers_lead'])}</p>
    </div>
    <div class="offer-cards">{offer_cards}</div>
    <div class="offer-foot"><a class="btn btn--gold" href="{nav_href(code, "agendar", "home")}">{e(c['offers_cta'])}</a></div>
  </div>
</section>"""

    # ---- Por que remar com a gente (quatro razões em gota) ----
    reasons_html = "".join(
        f'<div class="reason"><div class="reason-drop" aria-hidden="true">{ICONS_REASON[key]}</div>'
        f"<h3>{e(t)}</h3><p>{e(d)}</p></div>"
        for key, t, d in c["reasons"]
    )
    reasons = f"""
<section class="section" id="clube" aria-labelledby="reasons-title">
  <div class="wrap wrap--wide">
    <div class="section-head section-head--center">
      {eyebrow(c['kicker_club'])}
      <h2 class="h2" id="reasons-title">{e(c['reasons_title'])}</h2>
      <p class="lead">{e(c['reasons_lead'])}</p>
    </div>
    <div class="reasons">{reasons_html}</div>
  </div>
</section>"""

    # ---- Comunidade e capitães + carrossel de momentos ----
    caps = ""
    for i, cap in enumerate(SITE["captains"]):
        fem = i == 1
        role = c["captain_role_f"] if fem else c["captain_role"]
        caps += f"""
        <figure class="captain">
          {media(cap['photo'], code, c['captain_slot'], prefix, cls='captain-media', w=600, h=600, light=True)}
          <figcaption><span class="meta">{e(role)}</span><strong>{e(cap['name'])}</strong>
            <a class="link" href="https://www.instagram.com/{cap['handle']}/" target="_blank" rel="noopener">@{e(cap['handle'])}</a></figcaption>
        </figure>"""
    moments = "".join(
        '<figure class="moment">'
        + media(photo, code, f"{c['photo_slot_prefix']} {title}", prefix, cls="media--zoom", w=900, h=620)
        + f"<figcaption><strong>{e(title)}</strong><span>{e(text)}</span></figcaption></figure>"
        for photo, title, text in c["moments"]
    )
    community = f"""
<section class="section community" id="comunidade" aria-labelledby="community-title">
  <div class="wrap wrap--wide">
    <div class="community-grid">
      <div class="community-col">
        {eyebrow(c['kicker_community'])}
        <h2 class="h2" id="community-title">{e(c['team_title'])}</h2>
        <p class="lead">{e(c['team_lead'])}</p>
        <p class="community-quote">{e(c['about_statement'])}</p>
        <a class="btn btn--line-dark" href="{SITE['instagram']}" target="_blank" rel="noopener">{ICON_IG}{e(c['community_cta'])}</a>
      </div>
      <div class="captains">{caps}
      </div>
    </div>
    <div class="carousel">
      <div class="carousel-track" id="momentos" tabindex="0" role="group" aria-label="{e(c['moments_label'])}">{moments}</div>
      <div class="carousel-nav">
        <button type="button" class="carousel-btn" data-carousel="momentos" data-dir="-1" aria-controls="momentos" aria-label="{e(c['carousel_prev'])}">{ICON_PREV}</button>
        <button type="button" class="carousel-btn" data-carousel="momentos" data-dir="1" aria-controls="momentos" aria-label="{e(c['carousel_next'])}">{ICON_NEXT}</button>
      </div>
    </div>
    <!-- Depoimentos escritos: publicar aqui apenas depoimentos reais, com autorização. -->
    <div class="testimonials"></div>
    <div class="community-foot">
      <p>{e(c['community_note'])}</p>
    </div>
  </div>
</section>"""

    # ---- Produtos (chamada para a loja em /produtos) ----
    # Divisão painel/fotografia em vez de texto centralizado sobre a imagem.
    teaser_photo = PRODUCTS[1]["photo"] if len(PRODUCTS) > 1 else PRODUCTS[0]["photo"]
    shop = f"""
<section class="shop-teaser" aria-labelledby="shop-teaser-title">
  <div class="shop-split">
    <div class="shop-teaser-panel">
      {eyebrow(c['kicker_shop'])}
      <h2 class="h2" id="shop-teaser-title">{e(c['shop_teaser_title'])}</h2>
      <p class="lead">{e(c['shop_teaser_text'])}</p>
      <a class="btn btn--gold" href="{c['produtos_path']}">{e(c['shop_teaser_cta'])}</a>
    </div>
    {media(teaser_photo, code, c['shop_slot'], prefix, cls='shop-teaser-media', w=1600, h=1200)}
  </div>
</section>"""

    # ---- Local: mapa e informações ----
    pitems = "".join(f"<div><dt>{e(t)}</dt><dd>{e(d)}</dd></div>" for t, d in c["place_items"])
    place = f"""
<section class="section info" id="local" aria-labelledby="place-title">
  <div class="wrap wrap--wide">
    {eyebrow(c['kicker_info'])}
    <div class="info-place">
      <h2 class="h2" id="place-title">{e(c['place_title'])}</h2>
      <div class="map"><iframe src="{SITE['maps_embed']}" title="{e(c['map_title'])}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>
      <dl class="place-list">{pitems}</dl>
      <a class="btn btn--line-dark" href="{SITE['maps_link']}" target="_blank" rel="noopener">{e(c['place_maps'])}</a>
    </div>
  </div>
</section>"""

    # ---- Dúvidas: título e chamada numa coluna, acordeão na outra ----
    qa = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in c["faq"])
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in c["faq"]
        ],
    }
    faq_section = f"""
<section class="section" id="faq" aria-labelledby="faq-title">
  <div class="wrap wrap--wide faq-split">
    <div class="faq-intro">
      <h2 class="h2" id="faq-title">{e(c['faq_title'])}</h2>
      <p class="lead">{e(c['faq_lead'])}</p>
      <a class="btn btn--gold" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
    </div>
    <div class="faq">{qa}</div>
  </div>
  <script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
</section>"""

    # ---- Chamada final: painel Forest + fotografia ----
    closing = f"""
<section class="closing" id="contato" aria-labelledby="closing-title">
  <div class="wrap wrap--wide">
    <div class="closing-split band-dark">
      <div class="closing-text">
        <p class="eyebrow">{e(c['hero_place'])}</p>
        <h2 class="closing-title" id="closing-title">{e(c['final_title'])}</h2>
        <p class="lead">{e(c['final_lead'])}</p>
        <div class="btn-row">
          <a class="btn btn--gold" href="{nav_href(code, "agendar", "home")}">{e(c['dock_book'])}</a>
          <a class="btn btn--line" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
        </div>
      </div>
      {media('community_2', code, f"{c['photo_slot_prefix']} {c['final_title']}", prefix, cls='closing-media', w=1200, h=1200)}
    </div>
  </div>
</section>"""

    # ---- footer ----
    footer = page_footer(code, prefix, "home")
    scripts = page_scripts(code, prefix)

    # Ordem das seções: menu -> hero -> faixa de credibilidade -> o que
    # oferecemos -> quadro de reservas -> por que remar com a gente ->
    # comunidade e capitães -> loja -> local -> dúvidas -> chamada final ->
    # rodapé.
    body = (
        "<body>" + header + '<main id="conteudo">'
        + hero + credibility + offer + reasons + community
        + shop + place + faq_section + closing
        + "</main>" + footer + scripts + "</body></html>"
    )
    return head + "\n" + body


def render_produtos(code):
    c = CONTENT[code]
    other = "en" if code == "pt" else "pt"
    prefix = "../" if code == "pt" else "../../"
    base = SITE["base_url"].rstrip("/")
    canonical = base + c["produtos_path"]
    og_image = base + "/assets/img/og.jpg"

    alternates = (
        f'<link rel="alternate" hreflang="pt-BR" href="{base}/produtos/">'
        f'<link rel="alternate" hreflang="en" href="{base}/en/produtos/">'
        f'<link rel="alternate" hreflang="x-default" href="{base}/produtos/">'
    )

    head = f"""<!doctype html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(c['produtos_title'])}</title>
<meta name="description" content="{e(c['produtos_description'])}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="theme-color" content="#0D3527">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(c['produtos_title'])}">
<meta property="og:description" content="{e(c['produtos_description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{c['og_locale']}">
<meta property="og:locale:alternate" content="{CONTENT[other]['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/manrope-latin-standard-normal.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/dmserifdisplay-latin-standard-normal.woff2" crossorigin>
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>"""

    header = page_header(code, prefix, "produtos")

    def product_card(p):
        cat = p["category"][code]
        price = (
            "R$ " + f"{p['price_cents'] / 100:.2f}".replace(".", ",")
            if p["price_cents"] is not None
            else c["produtos_price_request"]
        )
        stock_label = c["produtos_stock"][p["stock"]]
        return f"""
    <article class="pcard" data-cat="{e(cat)}">
      <button type="button" class="pcard-trigger" data-open-product="{e(p['id'])}" aria-haspopup="dialog">
        {media(p['photo'], code, p['name'][code], prefix, cls='pcard-media media--zoom', w=900, h=1125, light=True)}
        <span class="pcard-body">
          <span class="pcard-cat">{e(cat)}</span>
          <strong class="pcard-name">{e(p['name'][code])}</strong>
          <span class="pcard-foot"><span class="pcard-price">{e(price)}</span><span class="pcard-stock pcard-stock--{e(p['stock'])}">{e(stock_label)}</span></span>
        </span>
      </button>
    </article>"""

    # Espaços de peça futura: cartão sem produto, sem preço e sem
    # disponibilidade — só o lugar reservado na grade. NUNCA preencher
    # com peça fictícia; o clube confirma antes de virar produto real.
    soon_card = f"""
    <article class="pcard pcard--soon" data-cat="soon">
      <div class="pcard-soon-media" aria-hidden="true"><span class="pcard-soon-badge">{e(c['shop_soon_badge'])}</span></div>
      <div class="pcard-body">
        <strong class="pcard-name">{e(c['shop_soon_title'])}</strong>
        <p class="pcard-soon-text">{e(c['shop_soon_text'])}</p>
      </div>
    </article>"""

    cards = "".join(product_card(p) for p in PRODUCTS) + soon_card * 2
    grid = f'<div class="pgrid" data-pgrid>{cards}</div>' if PRODUCTS else f'<p class="meta">{e(c["produtos_empty"])}</p>'

    # Categorias reais, na ordem em que aparecem em products.py — nenhuma
    # categoria inventada e nenhuma vazia.
    cats = []
    for prod in PRODUCTS:
        name = prod["category"][code]
        if name not in cats:
            cats.append(name)
    chips = f'<button type="button" class="pchip" data-cat-filter="all" aria-pressed="true">{e(c["shop_cat_all"])}</button>'
    chips += "".join(
        f'<button type="button" class="pchip" data-cat-filter="{e(n)}" aria-pressed="false">{e(n)}</button>' for n in cats
    )

    collections = "".join(
        f"""
      <article class="pcol{' pcol--soon' if soon else ''}">
        {media(photo, code, title, prefix, cls='pcol-media media--zoom', w=900, h=700, light=True)}
        <div class="pcol-body">
          <strong>{e(title)}</strong>
          {f'<span class="pcol-badge">{e(c["shop_soon_badge"])}</span>' if soon else ''}
          <p>{e(text)}</p>
        </div>
      </article>"""
        for title, text, photo, soon in c["shop_collections"]
    )

    main_html = f"""
<section class="section--tight produtos-hero">
  <div class="wrap wrap--wide produtos-hero-grid">
    {eyebrow(c['shop_intro_kicker'])}
    <h1 class="display">{e(c['shop_title'])}</h1>
    <div class="produtos-hero-aside">
      <p class="lead">{e(c['shop_lead'])}</p>
      <a class="btn btn--line-dark" href="{wa_link(c['shop_wa'])}" target="_blank" rel="noopener">{ICON_WA}{e(c['shop_cta'])}</a>
    </div>
  </div>
</section>
<section class="section--tight produtos-intro">
  <div class="wrap wrap--wide produtos-intro-grid">
    <h2 class="h2">{e(c['shop_intro_title'])}</h2>
    <p class="lead">{e(c['shop_intro_text'])}</p>
  </div>
</section>
<section class="section produtos-grid" aria-labelledby="produtos-grid-title">
  <div class="wrap wrap--wide">
    <div class="pfilters">
      <h2 class="pfilters-label" id="produtos-grid-title">{e(c['shop_cat_label'])}</h2>
      <div class="pchips" role="group" aria-labelledby="produtos-grid-title">{chips}</div>
    </div>
    {grid}
  </div>
</section>
<section class="section produtos-cols band-dark" aria-labelledby="produtos-cols-title">
  <div class="wrap wrap--wide">
    <div class="section-head section-head--center">
      {eyebrow(c['shop_collections_kicker'])}
      <h2 class="h2" id="produtos-cols-title">{e(c['shop_collections_title'])}</h2>
    </div>
    <div class="pcols">{collections}</div>
  </div>
</section>
<section class="section--tight produtos-howto">
  <div class="wrap wrap--wide produtos-howto-in">
    <h2 class="h3">{e(c['shop_howto_title'])}</h2>
    <p class="lead">{e(c['shop_howto_text'])}</p>
    <a class="btn btn--gold" href="{wa_link(c['shop_wa'])}" target="_blank" rel="noopener">{ICON_WA}{e(c['shop_cta'])}</a>
  </div>
</section>
<div class="pmodal-overlay" data-pmodal-overlay hidden>
  <div class="pmodal" role="dialog" aria-modal="true" aria-labelledby="pmodal-title">
    <button type="button" class="pmodal-close" data-pmodal-close aria-label="{e(c['produtos_close'])}">
      <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 5l14 14M19 5L5 19"/></svg>
    </button>
    <div class="pmodal-body" data-pmodal-body></div>
  </div>
</div>"""

    footer = page_footer(code, prefix, "produtos")
    scripts = page_scripts(code, prefix)

    body = "<body>" + header + '<main id="conteudo">' + main_html + "</main>" + footer + scripts + "</body></html>"
    return head + "\n" + body


def render_contato(code):
    """Página de contato: formulário com envio real (POST /api/contact),
    WhatsApp e Instagram. Nenhum telefone aparece na interface — o botão
    do WhatsApp leva à conversa sem expor o número."""
    c = CONTENT[code]
    other = "en" if code == "pt" else "pt"
    prefix = "../" if code == "pt" else "../../"
    base = SITE["base_url"].rstrip("/")
    canonical = base + c["contato_path"]
    og_image = base + "/assets/img/og.jpg"
    root = "/" if code == "pt" else "/en/"

    alternates = (
        f'<link rel="alternate" hreflang="pt-BR" href="{base}/contato/">'
        f'<link rel="alternate" hreflang="en" href="{base}/en/contato/">'
        f'<link rel="alternate" hreflang="x-default" href="{base}/contato/">'
    )

    head = f"""<!doctype html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(c['contato_title'])}</title>
<meta name="description" content="{e(c['contato_description'])}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="theme-color" content="#123D2B">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(c['contato_title'])}">
<meta property="og:description" content="{e(c['contato_description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{c['og_locale']}">
<meta property="og:locale:alternate" content="{CONTENT[other]['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/manrope-latin-standard-normal.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/dmserifdisplay-latin-standard-normal.woff2" crossorigin>
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>"""

    header = page_header(code, prefix, "contato")

    fields = (
        field("ct-name", c["ct_name"], text_input("ct-name", "name", c["ct_name"], extra='autocomplete="name" maxlength="120"'), full=True)
        + field("ct-email", c["ct_email"], text_input("ct-email", "email", c["ct_email"], kind="email", extra='autocomplete="email" maxlength="254"'))
        + field("ct-subject", c["ct_subject"], select("ct-subject", "subject", c["ct_subject"], c["ct_subjects"], c))
        + field("ct-message", c["ct_message"], textarea("ct-message", "message", c["ct_message"]), full=True)
    )

    main_html = f"""
<section class="section--tight contato-hero">
  <div class="wrap wrap--wide contato-hero-grid">
    {eyebrow(c['contato_kicker'])}
    <h1 class="display">{e(c['contato_h1'])}</h1>
    <p class="lead">{e(c['contato_lead'])}</p>
  </div>
</section>
<section class="section contato">
  <div class="wrap wrap--wide contato-grid">
    <div class="contato-main">
      <form class="form contato-form" data-contact-form novalidate aria-labelledby="contato-form-title">
        <h2 class="h3" id="contato-form-title">{e(c['contato_mail_title'])}</h2>
        <p class="form-intro">{e(c['contato_mail_text'])}</p>
        <div class="fields">{fields}</div>
        <div class="nl-hp" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        <div class="form-actions">
          <button class="btn btn--gold" type="submit">{e(c['ct_submit'])}</button>
          <p class="form-status" role="status" aria-live="polite"></p>
        </div>
        <p class="form-privacy"><a class="link" href="{root}privacidade/">{e(c['ct_privacy'])}</a></p>
      </form>
    </div>
    <aside class="contato-aside">
      <article class="contato-card">
        <h2 class="h4">{e(c['contato_wa_title'])}</h2>
        <p>{e(c['contato_wa_text'])}</p>
        <a class="btn btn--solid btn--sm" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['contato_wa_cta'])}</a>
      </article>
      <article class="contato-card">
        <h2 class="h4">{e(c['contato_other_title'])}</h2>
        <p>{e(c['contato_other_text'])}</p>
        <a class="btn btn--line-dark btn--sm" href="{SITE['instagram']}" target="_blank" rel="noopener">{ICON_IG}{e(c['contato_other_cta'])}</a>
      </article>
      <article class="contato-card contato-card--muted">
        <h2 class="h4">{e(c['contato_hours_title'])}</h2>
        <p>{e(c['contato_hours_text'])}</p>
        <a class="link-arrow" href="{root}#faq">{e(c['contato_hours_cta'])}{ICON_ARROW}</a>
      </article>
    </aside>
  </div>
</section>"""

    footer = page_footer(code, prefix, "contato")
    scripts = page_scripts(code, prefix)
    body = "<body>" + header + '<main id="conteudo">' + main_html + "</main>" + footer + scripts + "</body></html>"
    return head + chr(10) + body


def render_agendar(code):
    """/agendar/ — descoberta por carrossel e fluxo por jornada.

    A página entrega o carrossel renderizado no servidor (três artigos,
    um por jornada) e um <form data-journey> único e oculto. O
    experience.js assume a partir daí: navega o carrossel, troca o fluxo
    conforme a escolha e escreve os valores nos campos ocultos do form.

    O form é o mesmo contrato que o site.js já lê (data-journey,
    data-intro, [data-label], .form-status) — validação e envio pelo
    WhatsApp seguem sendo os de sempre, e por isso ele precisa existir no
    HTML desde o carregamento, não ser criado depois pelo JS.

    Sem JS a página continua útil: os três cartões aparecem em sequência,
    cada um com link para a jornada correspondente na home.
    """
    c = CONTENT[code]
    other = "en" if code == "pt" else "pt"
    prefix = "../" if code == "pt" else "../../"
    base = SITE["base_url"].rstrip("/")
    canonical = base + c["agendar_path"]
    og_image = base + "/assets/img/og.jpg"

    alternates = (
        f'<link rel="alternate" hreflang="pt-BR" href="{base}/agendar/">'
        f'<link rel="alternate" hreflang="en" href="{base}/en/agendar/">'
        f'<link rel="alternate" hreflang="x-default" href="{base}/agendar/">'
    )

    head = f"""<!doctype html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(c['agendar_title'])}</title>
<meta name="description" content="{e(c['agendar_description'])}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="theme-color" content="#123D2B">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(c['agendar_title'])}">
<meta property="og:description" content="{e(c['agendar_description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{c['og_locale']}">
<meta property="og:locale:alternate" content="{CONTENT[other]['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/manrope-latin-standard-normal.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/dmserifdisplay-latin-standard-normal.woff2" crossorigin>
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>"""

    root = "/" if code == "pt" else "/en/"
    # Sem JS não há fluxo: o "Explorar" abre o WhatsApp já com a frase
    # daquela jornada. Com JS o clique é interceptado e o href nunca é
    # seguido. (Antes isso apontava para as abas da home, que saíram.)
    wa_intro = {
        "experimentar": c["a_wa_intro"],
        "treinar": c["b_wa_intro"],
        "particular": c["c_wa_intro"],
    }
    slides = ""
    for i, (key, photo_key, title, desc) in enumerate(c["xp_cards"]):
        photo = PHOTOS[photo_key]
        slides += f"""
      <article class="xp-slide" id="xp-{key}" data-xp-slide="{key}" role="group" aria-roledescription="slide" aria-label="{i + 1} / {len(c['xp_cards'])}">
        <figure class="xp-shot">
          <img src="{prefix}assets/img/{photo['file']}" alt="{e(photo[f'alt_{code}'])}" style="--focus:{photo.get('focus', 'center')}" loading="{'eager' if i == 0 else 'lazy'}" decoding="async">
        </figure>
        <div class="xp-slide-body">
          <span class="xp-num" aria-hidden="true">{i + 1:02d}</span>
          <h2 class="xp-slide-title">{e(title)}</h2>
          <p class="xp-slide-desc">{e(desc)}</p>
          <a class="btn btn--gold xp-explore" href="{wa_link(wa_intro[key])}" data-xp-explore="{key}" target="_blank" rel="noopener">{e(c['xp_explore'])}</a>
        </div>
      </article>"""

    dots = "".join(
        f'<button type="button" class="xp-dot" data-xp-dot="{i}" aria-label="{i + 1:02d}"><span>{i + 1:02d}</span></button>'
        for i in range(len(c["xp_cards"]))
    )

    # Campos ocultos: o experience.js escreve aqui o que a pessoa escolheu,
    # com o rótulo que vai aparecer na mensagem. collect() lê [data-label].
    hidden = "".join(
        f'<input type="hidden" name="{n}" data-label="" data-xp-field="{n}">'
        for n in ("experiencia", "tipo", "modalidade", "periodo", "nivel", "pessoas", "data")
    )

    opt = f' ({c["f_optional"]})'
    contact = (
        field("xp-name", c["f_name"], text_input("xp-name", "name", c["f_name"], extra='autocomplete="name"'))
        + field("xp-email", c["f_email"] + opt, text_input("xp-email", "email", c["f_email"], kind="email", required=False, extra='autocomplete="email"'))
        + field("xp-phone", c["bk"]["phone"] + opt, text_input("xp-phone", "phone", c["bk"]["phone"], kind="tel", required=False, extra='autocomplete="tel" placeholder="(71) 9 0000-0000"'))
        + f'<details class="more field--full"><summary>{e(c["f_more"])}</summary>'
        + field("xp-notes", c["f_notes"], textarea("xp-notes", "notes", c["f_notes"]), full=True, error=False)
        + "</details>"
    )

    main_html = f"""
<!-- data-booking: a página inteira é uma reserva em andamento, então o
     pop-up do WhatsApp não se abre sozinho por cima dela (wa-widget.js).
     Sem data-modality, o booking.js ignora este host. -->
<section class="xp" data-xp data-booking>
  <div class="wrap wrap--wide">

    <header class="xp-head">
      {eyebrow(c['agendar_kicker'])}
      <h1 class="xp-h1">{e(c['agendar_h1'])}</h1>
      <p class="xp-hint" data-xp-hint>{e(c['agendar_hint'])}</p>
    </header>

    <div class="xp-stage" data-xp-stage>
      <div class="xp-track" data-xp-track>{slides}
      </div>
      <div class="xp-controls" data-xp-controls hidden>
        <button type="button" class="xp-arrow" data-xp-prev aria-label="{e(c['xp_prev_label'])}">{ICON_PREV}</button>
        <div class="xp-dots" role="tablist" aria-label="{e(c['agendar_h1'])}">{dots}</div>
        <button type="button" class="xp-arrow" data-xp-next aria-label="{e(c['xp_next_label'])}">{ICON_NEXT}</button>
      </div>
    </div>

    <div class="xp-flow" data-xp-flow hidden>
      <div class="xp-flow-head">
        <button type="button" class="xp-back" data-xp-back-all>{ICON_PREV}{e(c['xp_back_all'])}</button>
        <ol class="xp-steps" data-xp-steps></ol>
      </div>
      <div class="xp-panel" data-xp-panel tabindex="-1"></div>
    </div>

    <form class="form xp-form" data-journey="experimentar" data-intro="{e(c['a_wa_intro'])}" novalidate aria-label="{e(c['xp_submit'])}" hidden data-xp-form>
      {hidden}
      <div class="fields" data-xp-contact>{contact}</div>
      <div class="form-actions">
        <button class="btn btn--gold btn--xl" type="submit">{ICON_WA}{e(c['xp_submit'])}</button>
        <p class="form-status" role="status" aria-live="polite"></p>
      </div>
      <p class="form-privacy">{e(c['f_privacy'])}</p>
    </form>

  </div>
</section>"""

    header = page_header(code, prefix, "agendar")
    footer = page_footer(code, prefix, "agendar")
    scripts = page_scripts(code, prefix)
    body = "<body class=\"page-xp\">" + header + '<main id="conteudo">' + main_html + "</main>" + footer + scripts + "</body></html>"
    return head + chr(10) + body


def render_legal(code, key):
    """Página institucional (privacidade, termos, diretrizes, reservas).

    Documento marcado como rascunho em legal_content.py ganha aviso no
    topo e `noindex` — e fica fora do sitemap (ver sitemap()). Assim ele
    existe, é navegável e é honesto sobre o próprio status, sem se
    apresentar como política em vigor."""
    c = CONTENT[code]
    doc = LEGAL[key]
    d = doc[code]
    slug_ = doc["slug"]
    draft = doc["draft"]
    prefix = "../" if code == "pt" else "../../"
    base = SITE["base_url"].rstrip("/")
    root = "/" if code == "pt" else "/en/"
    canonical = f"{base}{root}{slug_}/"

    alternates = (
        f'<link rel="alternate" hreflang="pt-BR" href="{base}/{slug_}/">'
        f'<link rel="alternate" hreflang="en" href="{base}/en/{slug_}/">'
        f'<link rel="alternate" hreflang="x-default" href="{base}/{slug_}/">'
    )
    robots = '<meta name="robots" content="noindex, follow">' if draft else ""

    head = f"""<!doctype html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(d['title'])}</title>
<meta name="description" content="{e(d['description'])}">
{robots}
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="theme-color" content="#123D2B">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/manrope-latin-standard-normal.woff2" crossorigin>
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>"""

    header = page_header(code, prefix, slug_)

    anchors = [(slug(h, f"sec-{i+1}"), h, t, pend) for i, (h, t, pend) in enumerate(d["sections"])]
    pend_tag = f'<span class="legal-pending" title="{e(c["legal_pending_aria"])}">{e(c["legal_pending"])}</span>'
    sections = "".join(
        f'<section id="{a_}" class="legal-section{" is-pending" if pend else ""}">'
        f'<h2>{e(h)}{pend_tag if pend else ""}</h2><p>{e(t)}</p></section>'
        for a_, h, t, pend in anchors
    )
    toc = "".join(f'<a href="#{a_}">{e(h)}</a>' for a_, h, _, _ in anchors)
    draft_note = (
        f'<p class="legal-draft"><strong>{e(c["legal_draft_label"])}</strong> {e(c["legal_draft_note"])}</p>'
        if draft else ""
    )
    others = "".join(
        f'<a class="legal-other" href="{root}{o["slug"]}/">{e(o[code]["h1"].rstrip("."))}</a>'
        for k, o in LEGAL.items() if k != key
    )
    main_html = f"""
<section class="section legal">
  <div class="wrap wrap--wide">
    <div class="legal-head">
      {eyebrow(c['kicker_legal'])}
      <h1 class="display">{e(d['h1'])}</h1>
      <p class="lead">{e(d['lead'])}</p>
      <p class="meta">{e(d['updated'])}</p>
      {draft_note}
    </div>
    <div class="legal-grid">
      <nav class="legal-toc" aria-label="{e(c['legal_index'])}">{toc}</nav>
      <div class="legal-body">
        {sections}
        <p class="note">{e(d['note'])}</p>
        <div class="legal-foot">
          <a class="btn btn--solid" href="{root}">{e(c['legal_back'])}</a>
          <a class="btn btn--line-dark" href="{root}contato/">{e(c['footer_service_cta'])}</a>
        </div>
        <div class="legal-others">
          <h2 class="legal-others-title">{e(c['legal_docs_title'])}</h2>
          <div class="legal-others-list">{others}</div>
        </div>
      </div>
    </div>
  </div>
</section>"""

    footer = page_footer(code, prefix, slug_)
    scripts = page_scripts(code, prefix)
    body = "<body>" + header + '<main id="conteudo">' + main_html + "</main>" + footer + scripts + "</body></html>"
    return head + "\n" + body


def render_404():
    c = CONTENT["pt"]
    en = CONTENT["en"]
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 · Good Vibes Va'a</title><meta name="robots" content="noindex">
<meta name="theme-color" content="#0D3527">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/site.css"></head>
<body class="band-dark">
<main class="wrap wrap--wide nf">
<p class="eyebrow">404</p>
<h1 class="display">{e(c['not_found_title'])}</h1>
<p class="lead">{e(c['not_found_lead'])}</p>
<div class="btn-row"><a class="btn btn--gold" href="/">{e(c['not_found_cta'])}</a>
<a class="btn btn--line" href="/en/" lang="en">{e(en['not_found_cta'])}</a></div></main></body></html>"""


def sitemap():
    """Só entra no sitemap o que é documento público e válido: rascunho
    institucional (draft=True em legal_content.py) fica de fora e recebe
    noindex na própria página."""
    base = SITE["base_url"].rstrip("/")
    groups = [("/", "/en/"), ("/agendar/", "/en/agendar/"),
              ("/produtos/", "/en/produtos/"), ("/contato/", "/en/contato/")]
    for doc in LEGAL.values():
        if not doc["draft"]:
            groups.append((f'/{doc["slug"]}/', f'/en/{doc["slug"]}/'))
    urls = ""
    for pt_path, en_path in groups:
        for path in (pt_path, en_path):
            urls += f"""
  <url>
    <loc>{base}{path}</loc>
    <xhtml:link rel="alternate" hreflang="pt-BR" href="{base}{pt_path}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{base}{en_path}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{base}{pt_path}"/>
  </url>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}
</urlset>
"""


def write_page(path_parts, html):
    target = DIST.joinpath(*path_parts)
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(html, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC / "assets", DIST / "assets")
    (DIST / "index.html").write_text(render("pt"), encoding="utf-8")
    (DIST / "en").mkdir(parents=True, exist_ok=True)
    (DIST / "en" / "index.html").write_text(render("en"), encoding="utf-8")

    for code, parts in (("pt", ()), ("en", ("en",))):
        write_page((*parts, "agendar"), render_agendar(code))
        write_page((*parts, "produtos"), render_produtos(code))
        write_page((*parts, "contato"), render_contato(code))
        for key, doc in LEGAL.items():
            write_page((*parts, doc["slug"]), render_legal(code, key))

    (DIST / "404.html").write_text(render_404(), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE['base_url'].rstrip('/')}/sitemap.xml\n", encoding="utf-8"
    )
    print("Build ok ->", DIST)


if __name__ == "__main__":
    main()
