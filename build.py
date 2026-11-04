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
    "booking_mode": "demo",
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
        "nav": [("#experimentar", "Passeios"), ("#treinar", "Treinar"), ("#particular", "Particular"), ("#clube", "O clube"), ("#local", "Local"), ("#faq", "Dúvidas")],
        "nav_produtos": "Produtos",
        "lang_label": "Idioma",
        "cta_team": "Fale com a equipe",
        "menu_open": "Abrir menu",
        "menu_close": "Fechar menu",
        "hero_place": "Praia da Preguiça, Salvador",
        "hero_title": "Encontre seu ritmo no mar.",
        "hero_sub": "Experiências, aulas e uma comunidade conectada pela canoa havaiana na Baía de Todos-os-Santos.",
        "hero_cta1": "Conheça nossas experiências",
        "hero_slot": "Foto oficial: equipe remando ao amanhecer na Baía de Todos-os-Santos · 2400×1600 · hero.jpg",
        "hero_alt": "Equipe Good Vibes Va'a remando uma canoa havaiana ao amanhecer na Baía de Todos-os-Santos",
        "hero_facts": ["Passeios, aulas e treinos", "Para quem nunca remou e para atletas", "Aceitamos Gympass e TotalPass"],

        "about_title": "Um clube de canoa havaiana no coração de Salvador.",
        "about_statement": "Na canoa, ninguém rema sozinho. Cada remada depende do ritmo de quem está ao lado, e é isso que transforma uma aula em comunidade.",
        "about_pillars": [
            ("Experiências", "Passeios no nascer e no pôr do sol, primeira remada e saídas privadas para quem quer ver Salvador a partir do mar."),
            ("Clube", "Aulas, treinos e planos recorrentes para quem quer evoluir no esporte e fazer parte da equipe."),
            ("Good Vibes lifestyle", "Produtos, eventos e parcerias que levam a identidade do clube para fora da água."),
        ],
        "kicker_journeys": "Experiências",
        "kicker_club": "O clube",
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

        "steps_title": "Como funciona a primeira remada.",
        "steps_lead": "Do primeiro contato até a canoa na água.",
        "steps": [
            ("Envie sua solicitação", "Escolha a experiência e a data e mande sua solicitação pelo WhatsApp."),
            ("Receba a confirmação", "A equipe confirma horário, valores e as condições do mar."),
            ("Chegue à Praia da Preguiça", "Encontro na areia com os capitães, no ponto combinado."),
            ("Orientação e saída", "Instruções de remada e segurança e, então, mar."),
        ],
        "bring_title": "O que levar",
        "bring": ["Roupa de banho", "Protetor solar", "Água", "Boné ou viseira", "Bolsa estanque para o celular"],

        "team_title": "Quem rema com você.",
        "team_lead": "Os capitães conduzem cada saída, das primeiras orientações na areia até o retorno.",
        "captain_role": "Capitão",
        "captain_role_f": "Capitã",
        "captain_slot": "Foto oficial: retrato do(a) capitão(ã) na canoa · 1200×1500",

        "community_title": "Uma comunidade que se encontra no mar.",
        "community_lead": "Treinos ao amanhecer, ações como o Outubro Rosa e um ano de histórias contadas por quem rema com a gente.",
        "community_slots": ["Foto oficial: equipe celebrando após o treino · comunidade-1.jpg", "Foto oficial: Outubro Rosa · comunidade-2.jpg", "Foto oficial: aniversário de 1 ano do clube · comunidade-3.jpg", "Foto oficial: remadores na canoa · comunidade-canoa.jpg"],
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

        "privacy_path": "/privacidade/",
        "privacy_title": "Política de Privacidade — Good Vibes Va'a",
        "privacy_description": "Como o Good Vibes Va'a coleta, usa e protege os dados pessoais de quem visita o site e se cadastra na lista de novidades.",
        "privacy_h1": "Política de Privacidade.",
        "privacy_lead": "Como tratamos os dados de quem visita o site, faz uma solicitação ou se cadastra na nossa lista — conforme a Lei Geral de Proteção de Dados (LGPD).",
        "privacy_updated": "Última atualização: novembro de 2026.",
        "privacy_sections": [
            ("Quais dados coletamos", "Nome, WhatsApp e, quando aplicável, e-mail — só quando você mesmo os informa, ao solicitar uma reserva, pedir um orçamento ou se cadastrar na lista de novidades. Não coletamos dados de navegação, localização ou de outros sites."),
            ("Para que usamos", "Para responder à sua solicitação (reserva, orçamento, dúvida) e, só com seu consentimento separado e explícito, para enviar novidades e ofertas da Good Vibes Va'a por e-mail."),
            ("Cadastro na lista de novidades", "Guardamos o e-mail informado, o idioma do site no momento do cadastro e o texto exato do consentimento aceito — isso serve como prova de que você autorizou o envio, conforme exige a LGPD. Cada e-mail é cadastrado uma única vez."),
            ("Armazenamento de preferências no navegador", "Usamos armazenamento local do navegador (sessionStorage/localStorage) só para lembrar que você já fechou um pop-up ou já concluiu um cadastro, evitando mostrá-lo de novo. Isso fica só no seu aparelho — não é enviado a nós nem a terceiros."),
            ("Com quem compartilhamos", "Seus dados não são vendidos nem compartilhados publicamente. Quando o pagamento online estiver ativo, o valor da reserva é processado pelo Mercado Pago, que recebe só o necessário para a cobrança. O armazenamento dos dados é feito em banco de dados (Supabase) com acesso restrito à equipe do clube."),
            ("Seus direitos", "Você pode pedir a qualquer momento para acessar, corrigir ou excluir seus dados, e cancelar o recebimento de e-mails de novidades quando quiser. Basta falar com a equipe pelo WhatsApp."),
            ("Contato", "Dúvidas sobre esta política ou sobre seus dados: fale com a equipe pelo WhatsApp " + SITE["whatsapp_display"] + "."),
        ],
        "privacy_note": "Este texto é um resumo em linguagem simples das práticas do clube. Recomendamos revisão jurídica antes de qualquer uso comercial mais amplo dos dados coletados.",
        "privacy_back": "Voltar ao início",

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

        "footer_about": "Clube de canoa havaiana na Praia da Preguiça, Salvador, Bahia.",
        "footer_nav": "Navegue",
        "footer_contact": "Contato",
        "footer_follow": "Acompanhe",
        "footer_rights": "Todos os direitos reservados.",
        "footer_privacy": "Política de privacidade",
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
            "sendError": "Não foi possível enviar agora. Fale com a equipe pelo WhatsApp " + SITE["whatsapp_display"] + ".",
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
        "nav": [("#experimentar", "Paddles"), ("#treinar", "Train"), ("#particular", "Private"), ("#clube", "The club"), ("#local", "Location"), ("#faq", "FAQ")],
        "nav_produtos": "Products",
        "lang_label": "Language",
        "cta_team": "Talk to the team",
        "menu_open": "Open menu",
        "menu_close": "Close menu",
        "hero_place": "Praia da Preguiça, Salvador, Brazil",
        "hero_title": "Find your rhythm at sea.",
        "hero_sub": "Paddling experiences, classes and a community brought together by the outrigger canoe on the Bay of All Saints.",
        "hero_cta1": "Explore our experiences",
        "hero_slot": "Official photo: crew paddling at sunrise on the Bay of All Saints · 2400×1600 · hero.jpg",
        "hero_alt": "Good Vibes Va'a crew paddling an outrigger canoe at sunrise on the Bay of All Saints",
        "hero_facts": ["Paddles, classes and training", "For first-timers and athletes", "Gympass and TotalPass accepted"],

        "about_title": "An outrigger canoe club in the heart of Salvador.",
        "about_statement": "In a canoe, nobody paddles alone. Every stroke depends on the rhythm of the person beside you, and that is what turns a class into a community.",
        "about_pillars": [
            ("Experiences", "Sunrise and sunset paddles, a first-time session and private outings for anyone who wants to see Salvador from the water."),
            ("Club", "Classes, training sessions and recurring plans for those who want to progress in the sport and join the crew."),
            ("Good Vibes lifestyle", "Gear, events and partnerships that carry the club's identity beyond the water."),
        ],
        "kicker_journeys": "Experiences",
        "kicker_club": "The club",
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

        "steps_title": "How your first paddle works.",
        "steps_lead": "From first message to canoe on the water.",
        "steps": [
            ("Send your request", "Pick the experience and date and send your request on WhatsApp."),
            ("Get your confirmation", "The team confirms the time, price and sea conditions."),
            ("Meet at Praia da Preguiça", "Meet the captains on the sand at the agreed spot."),
            ("Briefing and launch", "Paddling and safety instructions, then out to sea."),
        ],
        "bring_title": "What to bring",
        "bring": ["Swimwear", "Sunscreen", "Water", "Cap or visor", "Dry bag for your phone"],

        "team_title": "Who paddles with you.",
        "team_lead": "The captains lead every outing, from the first briefing on the sand to the return.",
        "captain_role": "Captain",
        "captain_role_f": "Captain",
        "captain_slot": "Official photo: captain's portrait in the canoe · 1200×1500",

        "community_title": "A community that meets at sea.",
        "community_lead": "Sunrise training, campaigns like Pink October and a year of stories told by the people who paddle with us.",
        "community_slots": ["Official photo: crew celebrating after training · comunidade-1.jpg", "Official photo: Pink October · comunidade-2.jpg", "Official photo: club's first anniversary · comunidade-3.jpg", "Official photo: paddlers in the canoe · comunidade-canoa.jpg"],
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

        "privacy_path": "/en/privacidade/",
        "privacy_title": "Privacy Policy — Good Vibes Va'a",
        "privacy_description": "How Good Vibes Va'a collects, uses and protects the personal data of site visitors and newsletter subscribers.",
        "privacy_h1": "Privacy Policy.",
        "privacy_lead": "How we handle the data of people who visit the site, make a request, or subscribe to our list — under Brazil's General Data Protection Law (LGPD).",
        "privacy_updated": "Last updated: November 2026.",
        "privacy_sections": [
            ("What data we collect", "Name, WhatsApp number and, when applicable, email — only when you provide them yourself, when requesting a booking, a quote, or subscribing to our newsletter. We do not collect browsing data, location, or data from other sites."),
            ("What we use it for", "To reply to your request (booking, quote, question) and, only with your separate and explicit consent, to send news and offers from Good Vibes Va'a by email."),
            ("Newsletter sign-up", "We store the email you provide, the site language at the time of sign-up, and the exact consent text you accepted — this serves as proof of your authorization, as required by the LGPD. Each email is registered only once."),
            ("Browser preference storage", "We use browser-local storage (sessionStorage/localStorage) only to remember that you've already closed a pop-up or completed a sign-up, so we don't show it again. This stays on your device only — it isn't sent to us or to third parties."),
            ("Who we share data with", "Your data is never sold or shared publicly. When online payment is active, the booking amount is processed by Mercado Pago, which only receives what's needed to charge it. Data storage is handled in a database (Supabase) with access restricted to the club's team."),
            ("Your rights", "You can ask at any time to access, correct or delete your data, and unsubscribe from newsletter emails whenever you want. Just message the team on WhatsApp."),
            ("Contact", "Questions about this policy or your data: message the team on WhatsApp at +55 71 99978-9710."),
        ],
        "privacy_note": "This text is a plain-language summary of the club's practices. We recommend legal review before any broader commercial use of the data collected.",
        "privacy_back": "Back to home",

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

        "footer_about": "Outrigger canoe club at Praia da Preguiça, Salvador, Bahia, Brazil.",
        "footer_nav": "Explore",
        "footer_contact": "Contact",
        "footer_follow": "Follow",
        "footer_rights": "All rights reserved.",
        "footer_privacy": "Privacy policy",
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
            "sendError": "We couldn't send it right now. Message the team on WhatsApp at +55 71 99978-9710.",
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


def nav_items_html(code, page):
    """`page` é o slug da página atual ("home", "produtos", "privacidade").
    Nas âncoras (#experimentar etc.) fora da home, usa link absoluto de
    volta pra home (`/#experimentar`) em vez do hash puro — na home elas
    continuam hash puro pro JS de abas (ver initTabs em site.js) continuar
    funcionando sem mudança."""
    c = CONTENT[code]
    root = "/" if code == "pt" else "/en/"
    parts = []
    for h, t in c["nav"]:
        href = h if page == "home" else f"{root}{h}"
        parts.append(f'<li><a href="{href}">{e(t)}</a></li>')
    cur = ' aria-current="page"' if page == "produtos" else ""
    parts.append(f'<li><a href="{root}produtos/"{cur}>{e(c["nav_produtos"])}</a></li>')
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
    c = CONTENT[code]
    root = "/" if code == "pt" else "/en/"
    nav_items = nav_items_html(code, page)
    lang_switch = lang_switch_html(code, page)
    brand_href = "./" if page == "home" else root
    # Só a home tem hero (fotografia atrás do cabeçalho). Nas demais rotas o
    # cabeçalho já nasce sólido — sem isso o menu ficaria off-white sobre
    # fundo off-white enquanto a página não rola.
    solid = "" if page == "home" else " is-solid"
    return f"""
<a class="skip" href="#conteudo">{e(c['skip'])}</a>
<header class="header{solid}">
  <div class="wrap wrap--wide">
    <a class="brand" href="{brand_href}" aria-label="{e(SITE['name'])}">
      <img class="brand-logo" src="{prefix}assets/img/logo.png" alt="" width="40" height="40" onerror="this.remove()">
      <span class="brand-word">Good Vibes Va'a<small>{e(c['brand_sub'])}</small></span>
    </a>
    <nav class="nav" aria-label="{e(c['footer_nav'])}"><ul>{nav_items}</ul></nav>
    <div class="header-actions">
      {lang_switch}
      <a class="btn btn--sm btn--gold header-cta" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{e(c['cta_team'])}</a>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-nav" aria-label="{e(c['menu_open'])}"><span></span></button>
    </div>
  </div>
  <div class="mobile-nav" id="mobile-nav">
    <ul>{nav_items}</ul>
    <a class="btn btn--solid" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
  </div>
</header>"""


def page_footer(code, prefix, page):
    c = CONTENT[code]
    root = "/" if code == "pt" else "/en/"
    fnav = nav_items_html(code, page)
    lang_switch_footer = lang_switch_html(code, page)
    dock_href = "#experimentar" if page == "home" else f"{root}#experimentar"
    return f"""
<footer class="footer">
  <div class="wrap wrap--wide">
    <div class="footer-grid">
      <div class="footer-brand">
        <p class="brand-word">Good Vibes Va'a</p>
        <p>{e(c['footer_about'])}</p>
        <a class="btn btn--line btn--sm" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
      </div>
      <div class="footer-col"><h2>{e(c['footer_nav'])}</h2><ul>{fnav}</ul></div>
      <div class="footer-col"><h2>{e(c['footer_contact'])}</h2><ul>
        <li><a href="{wa_link()}" target="_blank" rel="noopener">WhatsApp {e(SITE['whatsapp_display'])}</a></li>
        <li>Praia da Preguiça, Salvador, BA</li></ul></div>
      <div class="footer-col"><h2>{e(c['footer_follow'])}</h2><ul>
        <li><a href="{SITE['instagram']}" target="_blank" rel="noopener">Instagram {e(SITE['instagram_handle'])}</a></li></ul></div>
    </div>
    <div class="footer-bottom">
      <span>© <span data-year></span> Good Vibes Va'a. {e(c['footer_rights'])}</span>
      <nav aria-label="{e(c['kicker_legal'])}"><a href="{c['privacy_path']}">{e(c['footer_privacy'])}</a></nav>
      {lang_switch_footer}
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
<div class="nl-widget" data-nl-widget></div>"""


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


def form_shell(journey, title, intro, wa_intro, fields_html, submit, c, extra_cls=""):
    off = SITE["booking_mode"] == "off"
    icon = ICON_WA if off else ""
    privacy = c["f_privacy"] if off else c["f_privacy_site"]
    return f"""
      <form class="form{extra_cls}" data-journey="{journey}" data-intro="{e(wa_intro)}" novalidate aria-labelledby="{journey}-form-title">
        <h3 class="h3" id="{journey}-form-title">{e(title)}</h3>
        <p class="form-intro">{e(intro)}</p>
        <div class="fields">{fields_html}</div>
        <div class="form-actions">
          <button class="btn btn--gold" type="submit">{icon}{e(submit)}</button>
          <p class="form-status" role="status" aria-live="polite"></p>
        </div>
        <p class="form-privacy">{e(privacy)}</p>
      </form>"""


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
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
    # Desktop: manchete em coluna larga à esquerda, "fatos" num trilho
    # vertical à direita — composição de 2 colunas, não a pilha do celular.
    facts = "".join(f"<li>{e(f)}</li>" for f in c["hero_facts"])
    hero = f"""
<section class="hero" aria-labelledby="hero-title">
  {media('hero', code, c['hero_slot'], prefix, cls='hero-media', w=2400, h=1600, eager=True)}
  <div class="wrap wrap--wide hero-inner">
    <div class="hero-lead">
      <p class="eyebrow hero-place">{e(c['hero_place'])}</p>
      <h1 class="display" id="hero-title">{e(c['hero_title'])}</h1>
      <p class="hero-sub">{e(c['hero_sub'])}</p>
      <div class="btn-row">
        <a class="btn btn--light" href="#experiencias">{e(c['hero_cta1'])}</a>
        <a class="btn btn--line" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
      </div>
    </div>
    <ul class="hero-facts">{facts}</ul>
  </div>
</section>"""

    # ---- Jornadas em abas (uma de cada vez na tela) ----
    tabs = "".join(
        f'<a class="tab" role="tab" id="tab-{h[1:]}" href="{h}" aria-controls="{h[1:]}">'
        f'<span class="tab-num" aria-hidden="true">{i + 1:02d}</span>'
        f'<span class="tab-title">{e(t)}</span><span class="tab-short" aria-hidden="true">{e(go_short)}</span><span class="tab-desc">{e(d)}</span></a>'
        for i, ((h, t, d, go), go_short) in enumerate(zip(c["journeys"], c["tab_short"]))
    )

    def offer_list(items):
        return '<dl class="offers">' + "".join(f"<div><dt>{e(t)}</dt><dd>{e(d)}</dd></div>" for t, d in items) + "</dl>"

    def more_field(fid, name, label, hint):
        return (f'<details class="more field--full"><summary>{e(c["f_more"])}</summary>'
                + field(fid, label, textarea(fid, name, label, hint=bool(hint)), hint=hint, full=True, error=False)
                + "</details>")

    # A — experimentar
    steps = "".join(f'<li class="step"><strong>{e(t)}</strong><span>{e(d)}</span></li>' for t, d in c["steps"])
    steps_block = f"""<div class="first-paddle" id="primeira-remada">
            <h3 class="h3">{e(c['steps_title'])}</h3>
            <ol class="steps">{steps}</ol>
          </div>"""

    if SITE["booking_mode"] == "off":
        # Sem sistema de reservas: formulário de WhatsApp de sempre.
        a_fields = (
            field("a-exp", c["f_experience"], select("a-exp", "experience", c["f_experience"], c["a_options"], c), full=True)
            + field("a-date", c["f_date"], text_input("a-date", "date", c["f_date"], kind="date"))
            + field("a-people", c["f_people"], text_input("a-people", "people", c["f_people"], kind="number", extra='min="1" max="60" inputmode="numeric" value="1"'))
            + more_field("a-notes", "notes", c["f_notes"], c["f_notes_hint"])
        )
        panel_a_main = form_shell("experimentar", c["a_form_title"], c["a_form_intro"], c["a_wa_intro"], a_fields, c["f_submit"], c)
        panel_a_aside = offer_list(c["a_offers"]) + f'<p class="note">{c["a_note"]}</p>'
    else:
        demo_note = (
            f'<p class="bk-demo-note">{e(c["bk"]["demo"])}</p>' if SITE["booking_mode"] == "demo" else ""
        )
        panel_a_main = f"""<div class="bk" data-booking data-modality="experimentar">
            {demo_note}
            <div class="bk-root"></div>
          </div>"""
        panel_a_aside = steps_block

    # Coluna estreita (narrativa) + coluna larga (reserva): no desktop a
    # reserva ocupa 8 das 12 colunas, em vez do cartão fixo de 420px.
    panel_a = f"""
    <div class="panel" id="experimentar" role="tabpanel" aria-labelledby="tab-experimentar" tabindex="-1">
      <div class="panel-grid">
        <div class="panel-intro">
          <h3 class="h3">{e(c['a_title'])}</h3>
          <p class="lead">{e(c['a_lead'])}</p>
          {panel_a_aside}
        </div>
        <div class="panel-main">
          {panel_a_main}
        </div>
      </div>
    </div>"""

    # B — treinar
    # Nome e WhatsApp só entram quando a solicitação não abre mais o
    # WhatsApp sozinha (demo/live) — no modo "off", a conversa de WhatsApp
    # já identifica a pessoa, como sempre foi.
    def contact_fields(prefix):
        if SITE["booking_mode"] == "off":
            return ""
        return (
            field(f"{prefix}-name", c["f_name"], text_input(f"{prefix}-name", "name", c["f_name"], extra='autocomplete="name"'))
            + field(
                f"{prefix}-phone", c["bk"]["phone"],
                text_input(f"{prefix}-phone", "phone", c["bk"]["phone"], kind="tel", extra='autocomplete="tel" placeholder="(71) 9 0000-0000"', hint=True),
                hint=c["bk"]["phone_hint"],
            )
        )

    plans = "".join(
        f'<div><dt>{e(t)}</dt><dd>{e(d)} <span class="price">{e(p)}</span></dd></div>' for t, d, p in c["plans"]
    )
    if SITE["booking_mode"] == "off":
        b_fields = (
            contact_fields("b")
            + field("b-mod", c["f_modality"], select("b-mod", "modality", c["f_modality"], c["b_options"], c), full=True)
            + field("b-period", c["f_period"], select("b-period", "period", c["f_period"], c["f_periods"], c))
            + field("b-level", c["f_experience_level"], select("b-level", "level", c["f_experience_level"], c["f_levels"], c))
            + more_field("b-notes", "notes", c["f_notes"], None)
        )
        panel_b_main = form_shell("treinar", c["b_form_title"], c["b_form_intro"], c["b_wa_intro"], b_fields, c["f_submit"], c)
    else:
        panel_b_main = f"""<div class="bk" data-booking data-modality="treinar">
            {demo_note}
            <div class="bk-root"></div>
          </div>"""

    panel_b = f"""
    <div class="panel" id="treinar" role="tabpanel" aria-labelledby="tab-treinar" tabindex="-1">
      <div class="panel-grid">
        <div class="panel-intro">
          <h3 class="h3">{e(c['b_title'])}</h3>
          <p class="lead">{e(c['b_lead'])}</p>
          <dl class="offers">{plans}</dl>
          <p class="note">{c['b_note']}</p>
        </div>
        <div class="panel-main">
          {panel_b_main}
        </div>
      </div>
    </div>"""

    # C — particular
    if SITE["booking_mode"] == "off":
        c_fields = (
            contact_fields("c")
            + field("c-type", c["f_type"], select("c-type", "type", c["f_type"], c["c_options"], c), full=True)
            + field("c-date", c["f_date"], text_input("c-date", "date", c["f_date"], kind="date"))
            + field("c-people", c["f_people"], text_input("c-people", "people", c["f_people"], kind="number", extra='min="1" max="200" inputmode="numeric"'))
            + more_field("c-details", "details", c["f_details"], c["f_details_hint"])
        )
        panel_c_main = form_shell("particular", c["c_form_title"], c["c_form_intro"], c["c_wa_intro"], c_fields, c["f_submit_quote"], c)
    else:
        panel_c_main = f"""<div class="bk" data-booking data-modality="particular">
            {demo_note}
            <div class="bk-root"></div>
          </div>"""

    panel_c = f"""
    <div class="panel" id="particular" role="tabpanel" aria-labelledby="tab-particular" tabindex="-1">
      <div class="panel-grid panel-grid--quote">
        <div class="panel-intro">
          <h3 class="h3">{e(c['c_title'])}</h3>
          <p class="lead">{e(c['c_lead'])}</p>
          {offer_list(c['formats'])}
        </div>
        <div class="panel-main">
          {panel_c_main}
        </div>
      </div>
    </div>"""

    journeys = f"""
<section class="section journeys band-dark" id="experiencias" aria-labelledby="journeys-title">
  <div class="wrap wrap--wide">
    <div class="section-head section-head--split">
      {eyebrow(c['kicker_journeys'])}
      <h2 class="h2" id="journeys-title">{e(c['journeys_title'])}</h2>
      <p class="lead">{e(c['journeys_lead'])}</p>
    </div>
    <div class="tabs" role="tablist" aria-label="{e(c['journeys_title'])}">{tabs}</div>
    {panel_a}{panel_b}{panel_c}
  </div>
</section>"""

    # ---- O clube: apresentação + capitães + comunidade ----
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
    tiles = "".join(
        media(f"community_{i+1}", code, s, prefix, cls="media--zoom", w=900, h=1125)
        for i, s in enumerate(c["community_slots"][:4])
    )
    pillars = "".join(f"<div><dt>{e(t)}</dt><dd>{e(d)}</dd></div>" for t, d in c["about_pillars"])
    club = f"""
<section class="section club" id="clube" aria-labelledby="club-title">
  <div class="wrap wrap--wide">
    <div class="club-grid">
      <div class="club-manifesto">
        {eyebrow(c['kicker_club'])}
        <h2 class="h2" id="club-title">{e(c['about_title'])}</h2>
        <p class="club-statement">{e(c['about_statement'])}</p>
        <dl class="club-pillars">{pillars}</dl>
      </div>
      <div class="club-team" id="equipe">
        <h3 class="h3">{e(c['team_title'])}</h3>
        <p class="lead" style="font-size:var(--t-sm);margin-top:10px">{e(c['team_lead'])}</p>
        <div class="captains">{caps}
        </div>
      </div>
    </div>
    <div class="strip" aria-label="{e(c['community_title'])}">{tiles}</div>
    <!-- Depoimentos escritos: publicar aqui apenas depoimentos reais, com autorização. -->
    <div class="testimonials"></div>
    <div class="community-foot">
      <p>{e(c['community_note'])}</p>
      <a class="btn btn--line-dark" href="{SITE['instagram']}" target="_blank" rel="noopener">{ICON_IG}{e(c['community_cta'])}</a>
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

    # ---- Local + FAQ lado a lado ----
    pitems = "".join(f"<div><dt>{e(t)}</dt><dd>{e(d)}</dd></div>" for t, d in c["place_items"])
    qa = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in c["faq"])
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in c["faq"]
        ],
    }
    place = f"""
<section class="section info" id="local" aria-labelledby="place-title">
  <div class="wrap wrap--wide">
    {eyebrow(c['kicker_info'])}
    <div class="info-grid" style="margin-top:clamp(28px,3vw,48px)">
      <div class="info-place">
        <h2 class="h2" id="place-title">{e(c['place_title'])}</h2>
        <div class="map"><iframe src="{SITE['maps_embed']}" title="{e(c['map_title'])}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>
        <dl class="place-list">{pitems}</dl>
        <a class="btn btn--line-dark" href="{SITE['maps_link']}" target="_blank" rel="noopener">{e(c['place_maps'])}</a>
      </div>
      <div class="info-faq" id="faq">
        <h2 class="h2">{e(c['faq_title'])}</h2>
        <div class="faq">{qa}</div>
      </div>
    </div>
  </div>
  <script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
</section>"""

    # ---- Chamada final ----
    closing = f"""
<section class="section closing band-dark" aria-labelledby="closing-title">
  <div class="wrap wrap--wide closing-inner">
    {eyebrow(c['kicker_closing'])}
    <h2 class="h2" id="closing-title">{e(c['final_title'])}</h2>
    <div class="closing-aside">
      <p class="lead">{e(c['final_lead'])}</p>
      <div class="btn-row">
        <a class="btn btn--gold" href="#experimentar">{e(c['dock_book'])}</a>
        <a class="btn btn--line" href="{wa_link()}" data-wa-open target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
      </div>
    </div>
  </div>
</section>"""

    # ---- footer ----
    footer = page_footer(code, prefix, "home")
    scripts = page_scripts(code, prefix)

    body = (
        "<body>" + header + '<main id="conteudo">' + hero + journeys + club + shop + place + closing
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
    <article class="pcard">
      <button type="button" class="pcard-trigger" data-open-product="{e(p['id'])}" aria-haspopup="dialog">
        {media(p['photo'], code, p['name'][code], prefix, cls='pcard-media media--zoom', w=900, h=1125, light=True)}
        <span class="pcard-body">
          <span class="pcard-cat">{e(cat)}</span>
          <strong class="pcard-name">{e(p['name'][code])}</strong>
          <span class="pcard-foot"><span class="pcard-price">{e(price)}</span><span class="pcard-stock pcard-stock--{e(p['stock'])}">{e(stock_label)}</span></span>
        </span>
      </button>
    </article>"""

    cards = "".join(product_card(p) for p in PRODUCTS)
    grid = f'<div class="pgrid">{cards}</div>' if PRODUCTS else f'<p class="meta">{e(c["produtos_empty"])}</p>'

    main_html = f"""
<section class="section--tight produtos-hero">
  <div class="wrap wrap--wide produtos-hero-grid">
    {eyebrow(c['nav_produtos'])}
    <h1 class="display">{e(c['shop_title'])}</h1>
    <div class="produtos-hero-aside">
      <p class="lead">{e(c['shop_lead'])}</p>
      <a class="btn btn--line-dark" href="{wa_link(c['shop_wa'])}" target="_blank" rel="noopener">{ICON_WA}{e(c['shop_cta'])}</a>
    </div>
  </div>
</section>
<section class="section produtos-grid">
  <div class="wrap wrap--wide">{grid}</div>
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


def render_privacy(code):
    c = CONTENT[code]
    other = "en" if code == "pt" else "pt"
    prefix = "../" if code == "pt" else "../../"
    base = SITE["base_url"].rstrip("/")
    canonical = base + c["privacy_path"]

    alternates = (
        f'<link rel="alternate" hreflang="pt-BR" href="{base}/privacidade/">'
        f'<link rel="alternate" hreflang="en" href="{base}/en/privacidade/">'
        f'<link rel="alternate" hreflang="x-default" href="{base}/privacidade/">'
    )

    head = f"""<!doctype html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(c['privacy_title'])}</title>
<meta name="description" content="{e(c['privacy_description'])}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="theme-color" content="#0D3527">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>"""

    header = page_header(code, prefix, "privacidade")

    # Índice lateral (só no desktop, via CSS) gerado a partir dos próprios
    # títulos das seções — nenhum texto novo, só âncoras estáveis.
    anchors = [(slug(h, f"sec-{i+1}"), h, t) for i, (h, t) in enumerate(c["privacy_sections"])]
    sections = "".join(
        f'<section id="{a}"><h2>{e(h)}</h2><p>{e(t)}</p></section>' for a, h, t in anchors
    )
    toc = "".join(f'<a href="#{a}">{e(h)}</a>' for a, h, _ in anchors)
    home_href = "/" if code == "pt" else "/en/"
    main_html = f"""
<section class="section legal">
  <div class="wrap wrap--wide">
    <div class="legal-head">
      {eyebrow(c['kicker_legal'])}
      <h1 class="display">{e(c['privacy_h1'])}</h1>
      <p class="lead">{e(c['privacy_lead'])}</p>
      <p class="meta">{e(c['privacy_updated'])}</p>
    </div>
    <div class="legal-grid">
      <nav class="legal-toc" aria-label="{e(c['privacy_h1'])}">{toc}</nav>
      <div class="legal-body">
        {sections}
        <p class="note">{e(c['privacy_note'])}</p>
        <div class="legal-foot"><a class="btn btn--solid" href="{home_href}">{e(c['privacy_back'])}</a></div>
      </div>
    </div>
  </div>
</section>"""

    footer = page_footer(code, prefix, "privacidade")
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
    base = SITE["base_url"].rstrip("/")
    groups = [
        ("/", "/en/"),
        ("/produtos/", "/en/produtos/"),
        ("/privacidade/", "/en/privacidade/"),
    ]
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


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC / "assets", DIST / "assets")
    (DIST / "index.html").write_text(render("pt"), encoding="utf-8")
    (DIST / "en").mkdir(parents=True, exist_ok=True)
    (DIST / "en" / "index.html").write_text(render("en"), encoding="utf-8")

    (DIST / "produtos").mkdir(parents=True, exist_ok=True)
    (DIST / "produtos" / "index.html").write_text(render_produtos("pt"), encoding="utf-8")
    (DIST / "en" / "produtos").mkdir(parents=True, exist_ok=True)
    (DIST / "en" / "produtos" / "index.html").write_text(render_produtos("en"), encoding="utf-8")

    (DIST / "privacidade").mkdir(parents=True, exist_ok=True)
    (DIST / "privacidade" / "index.html").write_text(render_privacy("pt"), encoding="utf-8")
    (DIST / "en" / "privacidade").mkdir(parents=True, exist_ok=True)
    (DIST / "en" / "privacidade" / "index.html").write_text(render_privacy("en"), encoding="utf-8")

    (DIST / "404.html").write_text(render_404(), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE['base_url'].rstrip('/')}/sitemap.xml\n", encoding="utf-8"
    )
    print("Build ok ->", DIST)


if __name__ == "__main__":
    main()
