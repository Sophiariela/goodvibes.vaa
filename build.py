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
        {"name": "Jesse Coutinho", "handle": "jesse_coutinho", "img": "captain-jesse.jpg"},
        {"name": "Nala Rodrigues", "handle": "nalarodrigues", "img": "captain-nala.jpg"},
    ],
    "maps_embed": "https://www.google.com/maps?q=Praia+da+Pregui%C3%A7a,+Salvador,+BA&output=embed",
    "maps_link": "https://www.google.com/maps/search/?api=1&query=Praia+da+Pregui%C3%A7a+Salvador+BA",
    # Integração futura: endpoint que recebe as solicitações (POST JSON). Vazio = WhatsApp.
    "request_endpoint": "",
}

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

# ---------------------------------------------------------------------------
# Conteúdo por idioma
# Regra editorial: nada de preços, horários, durações, regras ou depoimentos
# inventados. O que depende do clube aparece como "a equipe confirma" e está
# listado no README (checklist de conteúdo).
# ---------------------------------------------------------------------------
CONTENT = {
    "pt": {
        "lang": "pt-BR",
        "og_locale": "pt_BR",
        "path": "/",
        "title": "Good Vibes Va'a — Canoa havaiana na Praia da Preguiça, Salvador",
        "description": "Clube de canoa havaiana na Praia da Preguiça, em Salvador. Passeios no nascer e no pôr do sol, aulas, planos de treino e experiências particulares na Baía de Todos-os-Santos.",
        "skip": "Pular para o conteúdo",
        "brand_sub": "Clube de canoa havaiana",
        "nav": [("#experimentar", "Passeios"), ("#treinar", "Treinar"), ("#particular", "Particular"), ("#clube", "O clube"), ("#local", "Local"), ("#faq", "Dúvidas")],
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
        "about_slot": "Foto oficial: canoas Good Vibes na areia da Praia da Preguiça · 2400×1000 · clube.jpg",
        "about_alt": "Canoas do clube Good Vibes Va'a alinhadas na areia da Praia da Preguiça",

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
        "a_slot": "Foto oficial: turmas no passeio de pôr do sol · 1200×1500 · experimentar.jpg",
        "a_alt": "Grupo remando no passeio de pôr do sol na Baía de Todos-os-Santos",
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
        "captain_alt": "Retrato de {name}, capitão do Good Vibes Va'a",
        "captain_alt_f": "Retrato de {name}, capitã do Good Vibes Va'a",

        "community_title": "Uma comunidade que se encontra no mar.",
        "community_lead": "Treinos ao amanhecer, ações como o Outubro Rosa e um ano de histórias contadas por quem rema com a gente.",
        "community_slots": ["Foto oficial: equipe celebrando após o treino · comunidade-1.jpg", "Foto oficial: Outubro Rosa · comunidade-2.jpg", "Foto oficial: aniversário de 1 ano do clube · comunidade-3.jpg", "Foto oficial: remadores na canoa · comunidade-canoa.jpg", "Foto oficial: detalhe de remo e mar · comunidade-5.jpg"],
        "community_canoa_alt": "Equipe remando em canoa havaiana no mar",
        "community_alt": "Comunidade Good Vibes Va'a",
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
        "shop_item": "Produto Good Vibes",
        "shop_item_meta": "Nome e preço a confirmar",
        "shop_cta": "Pedir peças pelo WhatsApp",
        "shop_wa": "Olá, Good Vibes Va'a! Gostaria de saber sobre os produtos da Moda Good Vibes.",

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
        "final_slot": "Foto oficial: canoa no mar ao pôr do sol · 2400×1200 · final.jpg",
        "final_alt": "Canoa havaiana ao pôr do sol na Baía de Todos-os-Santos",

        "footer_about": "Clube de canoa havaiana na Praia da Preguiça, Salvador, Bahia.",
        "footer_nav": "Navegue",
        "footer_contact": "Contato",
        "footer_follow": "Acompanhe",
        "footer_rights": "Todos os direitos reservados.",
        "dock_book": "Experiências",
        "float_wa_label": "Fale com a gente no WhatsApp",
        "float_wa_msg": "Olá! Gostaria de saber mais sobre as experiências do Good Vibes Va'a.",

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
        },
        "not_found_title": "Página não encontrada.",
        "not_found_lead": "O endereço pode ter mudado. Volte para o início e escolha sua experiência.",
        "not_found_cta": "Voltar ao início",
    },

    "en": {
        "lang": "en",
        "og_locale": "en_US",
        "path": "/en/",
        "title": "Good Vibes Va'a — Outrigger canoe club at Praia da Preguiça, Salvador",
        "description": "Outrigger canoe (va'a) club at Praia da Preguiça in Salvador, Brazil. Sunrise and sunset paddles, classes, training plans and private experiences on the Bay of All Saints.",
        "skip": "Skip to content",
        "brand_sub": "Outrigger canoe club",
        "nav": [("#experimentar", "Paddles"), ("#treinar", "Train"), ("#particular", "Private"), ("#clube", "The club"), ("#local", "Location"), ("#faq", "FAQ")],
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
        "about_slot": "Official photo: Good Vibes canoes on the sand at Praia da Preguiça · 2400×1000 · clube.jpg",
        "about_alt": "Good Vibes Va'a canoes lined up on the sand at Praia da Preguiça",

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
        "a_slot": "Official photo: group on the sunset paddle · 1200×1500 · experimentar.jpg",
        "a_alt": "Group paddling at sunset on the Bay of All Saints",
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
        "captain_alt": "Portrait of {name}, Good Vibes Va'a captain",
        "captain_alt_f": "Portrait of {name}, Good Vibes Va'a captain",

        "community_title": "A community that meets at sea.",
        "community_lead": "Sunrise training, campaigns like Pink October and a year of stories told by the people who paddle with us.",
        "community_slots": ["Official photo: crew celebrating after training · comunidade-1.jpg", "Official photo: Pink October · comunidade-2.jpg", "Official photo: club's first anniversary · comunidade-3.jpg", "Official photo: paddlers in the canoe · comunidade-canoa.jpg", "Official photo: paddle and sea detail · comunidade-5.jpg"],
        "community_canoa_alt": "Crew paddling an outrigger canoe at sea",
        "community_alt": "Good Vibes Va'a community",
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
        "shop_item": "Good Vibes product",
        "shop_item_meta": "Name and price to be confirmed",
        "shop_cta": "Order on WhatsApp",
        "shop_wa": "Hi Good Vibes Va'a! I'd like to know about the Moda Good Vibes products.",

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
        "final_slot": "Official photo: canoe at sea at sunset · 2400×1200 · final.jpg",
        "final_alt": "Outrigger canoe at sunset on the Bay of All Saints",

        "footer_about": "Outrigger canoe club at Praia da Preguiça, Salvador, Bahia, Brazil.",
        "footer_nav": "Explore",
        "footer_contact": "Contact",
        "footer_follow": "Follow",
        "footer_rights": "All rights reserved.",
        "dock_book": "Experiences",
        "float_wa_label": "Chat with us on WhatsApp",
        "float_wa_msg": "Hi! I'd like to know more about Good Vibes Va'a experiences.",

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
ICON_ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 12h15M13 6l6 6-6 6"/></svg>'
ICON_IG = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3.5" y="3.5" width="17" height="17" rx="4.5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r=".9" fill="currentColor"/></svg>'


def e(s):
    return escape(str(s), quote=True)


def wa_link(text=None):
    url = f"https://wa.me/{SITE['whatsapp']}"
    if text:
        from urllib.parse import quote
        url += "?text=" + quote(text)
    return url


def media(img, slot, alt, prefix, cls="", w=1600, h=1000, eager=False, light=False):
    """Slot de fotografia. Mostra a foto oficial se assets/img/<img> existir;
    caso contrário, o slot exibe a descrição da foto a inserir."""
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    klass = "media" + (" media--light" if light else "") + (f" {cls}" if cls else "")
    return (
        f'<figure class="{klass}" data-slot="{e(slot)}">'
        f'<img src="{prefix}assets/img/{img}" alt="{e(alt)}" width="{w}" height="{h}" '
        f'{loading} decoding="async" onerror="this.remove()">'
        f"</figure>"
    )


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
    return f"""
      <form class="form{extra_cls}" data-journey="{journey}" data-intro="{e(wa_intro)}" novalidate aria-labelledby="{journey}-form-title">
        <h3 class="h3" id="{journey}-form-title">{e(title)}</h3>
        <p class="form-intro">{e(intro)}</p>
        <div class="fields">{fields_html}</div>
        <div class="form-actions">
          <button class="btn btn--primary" type="submit">{ICON_WA}{e(submit)}</button>
          <p class="form-status" role="status" aria-live="polite"></p>
        </div>
        <p class="form-privacy">{e(c["f_privacy"])}</p>
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
<meta name="theme-color" content="#123D2B">
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
<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/archivo-latin-standard-normal.woff2" crossorigin>
<link rel="preload" as="image" href="{prefix}assets/img/hero.jpg" fetchpriority="high">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>"""

    # ---- header ----
    nav_items = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in c["nav"])
    pt_cur = code == "pt"
    lang_switch = (
        f'<nav class="lang-switch" aria-label="{e(c["lang_label"])}">'
        + (f'<span aria-current="true"><b>PT</b></span>' if pt_cur else f'<a href="../" hreflang="pt-BR" lang="pt-BR">PT</a>')
        + (f'<span aria-current="true"><b>EN</b></span>' if not pt_cur else f'<a href="en/" hreflang="en" lang="en">EN</a>')
        + "</nav>"
    )
    header = f"""
<a class="skip" href="#conteudo">{e(c['skip'])}</a>
<header class="header">
  <div class="wrap">
    <a class="brand" href="{'./' if pt_cur else './'}" aria-label="{e(SITE['name'])}">
      <img class="brand-logo" src="{prefix}assets/img/logo.png" alt="" width="40" height="40" onerror="this.remove()">
      <span class="brand-word">Good Vibes Va'a<small>{e(c['brand_sub'])}</small></span>
    </a>
    <nav class="nav" aria-label="Principal"><ul>{nav_items}</ul></nav>
    <div class="header-actions">
      {lang_switch}
      <a class="btn btn--primary header-cta" href="{wa_link()}" target="_blank" rel="noopener">{e(c['cta_team'])}</a>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-nav" aria-label="{e(c['menu_open'])}"><span></span></button>
    </div>
  </div>
  <div class="mobile-nav" id="mobile-nav">
    <ul>{nav_items}</ul>
    <a class="btn btn--dark" href="{wa_link()}" target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
  </div>
</header>"""

    # ---- hero ----
    facts = "".join(f"<li>{e(f)}</li>" for f in c["hero_facts"])
    hero = f"""
<section class="hero" aria-labelledby="hero-title">
  {media('hero.jpg', c['hero_slot'], c['hero_alt'], prefix, w=2400, h=1600, eager=True)}
  <div class="wrap hero-inner">
    <p class="hero-place">{e(c['hero_place'])}</p>
    <h1 class="display" id="hero-title">{e(c['hero_title'])}</h1>
    <p class="hero-sub">{e(c['hero_sub'])}</p>
    <div class="btn-row">
      <a class="btn btn--primary" href="#experiencias">{e(c['hero_cta1'])}</a>
      <a class="btn btn--outline" href="{wa_link()}" target="_blank" rel="noopener">{ICON_WA}{e(c['cta_team'])}</a>
    </div>
    <ul class="hero-facts">{facts}</ul>
  </div>
</section>"""

    # ---- Jornadas em abas (uma de cada vez na tela) ----
    tabs = "".join(
        f'<a class="tab" role="tab" id="tab-{h[1:]}" href="{h}" aria-controls="{h[1:]}">'
        f'<span class="tab-title">{e(t)}</span><span class="tab-short" aria-hidden="true">{e(go_short)}</span><span class="tab-desc">{e(d)}</span></a>'
        for (h, t, d, go), go_short in zip(c["journeys"], c["tab_short"])
    )

    def offer_list(items):
        return '<dl class="offers">' + "".join(f"<div><dt>{e(t)}</dt><dd>{e(d)}</dd></div>" for t, d in items) + "</dl>"

    def more_field(fid, name, label, hint):
        return (f'<details class="more field--full"><summary>{e(c["f_more"])}</summary>'
                + field(fid, label, textarea(fid, name, label, hint=bool(hint)), hint=hint, full=True, error=False)
                + "</details>")

    # A — experimentar
    a_fields = (
        field("a-exp", c["f_experience"], select("a-exp", "experience", c["f_experience"], c["a_options"], c), full=True)
        + field("a-date", c["f_date"], text_input("a-date", "date", c["f_date"], kind="date"))
        + field("a-people", c["f_people"], text_input("a-people", "people", c["f_people"], kind="number", extra='min="1" max="60" inputmode="numeric" value="1"'))
        + more_field("a-notes", "notes", c["f_notes"], c["f_notes_hint"])
    )
    steps = "".join(f'<li class="step"><strong>{e(t)}</strong><span>{e(d)}</span></li>' for t, d in c["steps"])
    panel_a = f"""
    <div class="panel" id="experimentar" role="tabpanel" aria-labelledby="tab-experimentar" tabindex="-1">
      <div class="panel-grid">
        <div>
          <h3 class="h3">{e(c['a_title'])}</h3>
          <p class="panel-lead">{e(c['a_lead'])}</p>
          {offer_list(c['a_offers'])}
          <p class="note">{c['a_note']}</p>
        </div>
        {form_shell('experimentar', c['a_form_title'], c['a_form_intro'], c['a_wa_intro'], a_fields, c['f_submit'], c)}
      </div>
      <div class="first-paddle" id="primeira-remada">
        <h3 class="h3">{e(c['steps_title'])}</h3>
        <ol class="steps">{steps}</ol>
      </div>
    </div>"""

    # B — treinar
    plans = "".join(
        f'<div><dt>{e(t)}</dt><dd>{e(d)} <span class="price">{e(p)}</span></dd></div>' for t, d, p in c["plans"]
    )
    b_fields = (
        field("b-mod", c["f_modality"], select("b-mod", "modality", c["f_modality"], c["b_options"], c), full=True)
        + field("b-period", c["f_period"], select("b-period", "period", c["f_period"], c["f_periods"], c))
        + field("b-level", c["f_experience_level"], select("b-level", "level", c["f_experience_level"], c["f_levels"], c))
        + more_field("b-notes", "notes", c["f_notes"], None)
    )
    panel_b = f"""
    <div class="panel" id="treinar" role="tabpanel" aria-labelledby="tab-treinar" tabindex="-1">
      <div class="panel-grid">
        <div>
          <h3 class="h3">{e(c['b_title'])}</h3>
          <p class="panel-lead">{e(c['b_lead'])}</p>
          <dl class="offers">{plans}</dl>
          <p class="note">{c['b_note']}</p>
        </div>
        {form_shell('treinar', c['b_form_title'], c['b_form_intro'], c['b_wa_intro'], b_fields, c['f_submit'], c)}
      </div>
    </div>"""

    # C — particular
    c_fields = (
        field("c-type", c["f_type"], select("c-type", "type", c["f_type"], c["c_options"], c), full=True)
        + field("c-date", c["f_date"], text_input("c-date", "date", c["f_date"], kind="date"))
        + field("c-people", c["f_people"], text_input("c-people", "people", c["f_people"], kind="number", extra='min="1" max="200" inputmode="numeric"'))
        + more_field("c-details", "details", c["f_details"], c["f_details_hint"])
    )
    panel_c = f"""
    <div class="panel" id="particular" role="tabpanel" aria-labelledby="tab-particular" tabindex="-1">
      <div class="panel-grid">
        <div>
          <h3 class="h3">{e(c['c_title'])}</h3>
          <p class="panel-lead">{e(c['c_lead'])}</p>
          {offer_list(c['formats'])}
        </div>
        {form_shell('particular', c['c_form_title'], c['c_form_intro'], c['c_wa_intro'], c_fields, c['f_submit_quote'], c)}
      </div>
    </div>"""

    journeys = f"""
<section class="section journeys" id="experiencias" aria-labelledby="journeys-title">
  <div class="wrap">
    <div class="section-head section-head--split">
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
        alt = (c["captain_alt_f"] if fem else c["captain_alt"]).format(name=cap["name"])
        caps += f"""
        <figure class="captain">
          {media(cap['img'], cap['img'], alt, prefix, cls='captain-media', w=600, h=600, light=True)}
          <figcaption><span class="meta">{e(role)}</span><strong>{e(cap['name'])}</strong>
            <a class="link" href="https://www.instagram.com/{cap['handle']}/" target="_blank" rel="noopener">@{e(cap['handle'])}</a></figcaption>
        </figure>"""
    tiles = "".join(
        media(
            "comunidade-canoa.jpg" if i == 3 else f"comunidade-{i+1}.jpg",
            s,
            c["community_canoa_alt"] if i == 3 else c["community_alt"],
            prefix, w=900, h=900,
        )
        for i, s in enumerate(c["community_slots"][:4])
    )
    club = f"""
<section class="section club" id="clube" aria-labelledby="club-title">
  <div class="wrap">
    <div class="club-grid">
      <div>
        <h2 class="h2" id="club-title">{e(c['about_title'])}</h2>
        <p class="about-statement">{e(c['about_statement'])}</p>
      </div>
      <div id="equipe">
        <h3 class="h3">{e(c['team_title'])}</h3>
        <div class="captains">{caps}
        </div>
      </div>
    </div>
    <div class="strip" aria-label="{e(c['community_title'])}">{tiles}</div>
    <!-- Depoimentos escritos: publicar aqui apenas depoimentos reais, com autorização. -->
    <div class="testimonials"></div>
    <div class="community-foot">
      <p>{e(c['community_note'])}</p>
      <a class="btn btn--dark" href="{SITE['instagram']}" target="_blank" rel="noopener">{ICON_IG}{e(c['community_cta'])}</a>
    </div>
  </div>
</section>"""

    # ---- Produtos (faixa compacta) ----
    prods = "".join(
        f"""<figure class="product">{media(f'produto-{n}.jpg', f'produto-{n}.jpg', c['shop_item'], prefix, cls='product-media', w=800, h=800, light=True)}
        <figcaption>{e(c['shop_item_meta'])}</figcaption></figure>"""
        for n in range(1, 6)
    )
    shop = f"""
<section class="section shop" id="produtos" aria-labelledby="shop-title">
  <div class="wrap">
    <div class="row-head">
      <div><h2 class="h2" id="shop-title">{e(c['shop_title'])}</h2><p class="meta" style="margin-top:8px">{e(c['shop_lead'])}</p></div>
      <a class="btn btn--outline-dark" href="{wa_link(c['shop_wa'])}" target="_blank" rel="noopener">{ICON_WA}{e(c['shop_cta'])}</a>
    </div>
    <div class="shelf">{prods}</div>
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
  <div class="wrap info-grid">
    <div>
      <h2 class="h2" id="place-title">{e(c['place_title'])}</h2>
      <div class="map"><iframe src="{SITE['maps_embed']}" title="{e(c['map_title'])}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>
      <dl class="place-list">{pitems}</dl>
      <a class="btn btn--dark" href="{SITE['maps_link']}" target="_blank" rel="noopener">{e(c['place_maps'])}</a>
    </div>
    <div id="faq">
      <h2 class="h2">{e(c['faq_title'])}</h2>
      <div class="faq">{qa}</div>
    </div>
  </div>
  <script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
</section>"""

    # ---- footer ----
    fnav = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in c["nav"])
    footer = f"""
<footer class="footer">
  <div class="wrap">
    <div class="footer-grid">
      <div><p class="brand-word">Good Vibes Va'a</p><p style="margin-top:12px;max-width:36ch">{e(c['footer_about'])}</p></div>
      <div><h2>{e(c['footer_nav'])}</h2><ul>{fnav}</ul></div>
      <div><h2>{e(c['footer_contact'])}</h2><ul>
        <li><a href="{wa_link()}" target="_blank" rel="noopener">WhatsApp {e(SITE['whatsapp_display'])}</a></li>
        <li>Praia da Preguiça, Salvador, BA</li></ul></div>
      <div><h2>{e(c['footer_follow'])}</h2><ul>
        <li><a href="{SITE['instagram']}" target="_blank" rel="noopener">Instagram {e(SITE['instagram_handle'])}</a></li></ul></div>
    </div>
    <div class="footer-bottom"><span>© <span data-year></span> Good Vibes Va'a. {e(c['footer_rights'])}</span>{lang_switch.replace('class="lang-switch"', 'class="lang-switch" style="color:var(--ivory)"')}</div>
  </div>
</footer>
<div class="dock" inert>
  <a class="btn btn--dark" href="#experiencias">{e(c['dock_book'])}</a>
  <a class="btn btn--primary" href="{wa_link()}" target="_blank" rel="noopener">{ICON_WA}WhatsApp</a>
</div>
<a class="float-wa" href="{wa_link(c['float_wa_msg'])}" target="_blank" rel="noopener" aria-label="{e(c['float_wa_label'])}">{ICON_WA}</a>"""

    config = {"whatsapp": SITE["whatsapp"], "requestEndpoint": SITE["request_endpoint"]}
    scripts = f"""
<script type="application/json" id="i18n">{json.dumps(c['i18n'], ensure_ascii=False)}</script>
<script>window.GVV_CONFIG = {json.dumps(config)};</script>
<script src="{prefix}assets/js/site.js" type="module"></script>"""

    body = (
        "<body>" + header + '<main id="conteudo">' + hero + journeys + club + shop + place + "</main>" + footer + scripts + "</body></html>"
    )
    return head + "\n" + body


def render_404():
    c = CONTENT["pt"]
    en = CONTENT["en"]
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 · Good Vibes Va'a</title><meta name="robots" content="noindex">
<link rel="stylesheet" href="/assets/css/site.css"></head>
<body style="background:var(--forest);color:var(--ivory);min-height:100svh;display:grid;align-items:center">
<main class="wrap"><h1 class="display" style="font-size:var(--t-xl)">{e(c['not_found_title'])}</h1>
<p class="lead" style="color:rgba(244,240,230,.8);margin-top:20px">{e(c['not_found_lead'])}</p>
<div class="btn-row" style="margin-top:32px"><a class="btn btn--primary" href="/">{e(c['not_found_cta'])}</a>
<a class="btn btn--outline" href="/en/" lang="en">{e(en['not_found_cta'])}</a></div></main></body></html>"""


def sitemap():
    base = SITE["base_url"].rstrip("/")
    urls = ""
    for path in ["/", "/en/"]:
        urls += f"""
  <url>
    <loc>{base}{path}</loc>
    <xhtml:link rel="alternate" hreflang="pt-BR" href="{base}/"/>
    <xhtml:link rel="alternate" hreflang="en" href="{base}/en/"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{base}/"/>
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
    (DIST / "404.html").write_text(render_404(), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE['base_url'].rstrip('/')}/sitemap.xml\n", encoding="utf-8"
    )
    print("Build ok ->", DIST)


if __name__ == "__main__":
    main()
