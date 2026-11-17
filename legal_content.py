# -*- coding: utf-8 -*-
"""
Páginas institucionais do Good Vibes Va'a (privacidade, termos, diretrizes
da comunidade, política de reservas e cancelamentos).

Mesmo padrão de booking_content.py / products.py: o texto mora aqui, em
Python, e build.py só renderiza. Cada documento:

  slug      segmento da URL, igual nos dois idiomas (/termos/, /en/termos/).
  draft     True enquanto o documento NÃO foi validado pelo clube e por
            revisão jurídica. Um rascunho:
              - mostra um aviso de rascunho no topo da página;
              - sai do sitemap.xml e recebe <meta name="robots" noindex>;
            ou seja, existe e é navegável, mas nunca se apresenta como
            política oficial em vigor. Virar documento válido é trocar
            draft para False — nada mais muda.
  <locale>  title/description (SEO), h1, lead, updated, note e sections.

  sections  lista de (título, texto, pendente). `pendente=True` marca um
            ponto que o clube ainda precisa definir: a seção é renderizada
            com a etiqueta "a definir" e o texto descreve o que falta
            decidir, nunca uma regra inventada. NUNCA transformar um
            pendente em regra sem o clube confirmar — prazo de
            cancelamento, reembolso, foro e uso de imagem têm efeito
            jurídico e comercial real.
"""

LEGAL = {
    # -----------------------------------------------------------------
    # Privacidade — único documento já validado (texto que já estava no
    # ar desde a primeira versão do site).
    # -----------------------------------------------------------------
    "privacidade": {
        "slug": "privacidade",
        "draft": False,
        "pt": {
            "title": "Política de Privacidade — Good Vibes Va'a",
            "description": "Como o Good Vibes Va'a coleta, usa e protege os dados pessoais de quem visita o site e se cadastra na lista de novidades.",
            "h1": "Política de Privacidade.",
            "lead": "Como tratamos os dados de quem visita o site, faz uma solicitação ou se cadastra na nossa lista — conforme a Lei Geral de Proteção de Dados (LGPD).",
            "updated": "Última atualização: novembro de 2026.",
            "sections": [
                ("Quais dados coletamos", "Nome, WhatsApp e, quando aplicável, e-mail — só quando você mesmo os informa, ao solicitar uma reserva, pedir um orçamento, enviar uma mensagem pela página de contato ou se cadastrar na lista de novidades. Não coletamos dados de navegação, localização ou de outros sites.", False),
                ("Para que usamos", "Para responder à sua solicitação (reserva, orçamento, dúvida) e, só com seu consentimento separado e explícito, para enviar novidades e ofertas da Good Vibes Va'a por e-mail.", False),
                ("Cadastro na lista de novidades", "Guardamos o e-mail informado, o idioma do site no momento do cadastro e o texto exato do consentimento aceito — isso serve como prova de que você autorizou o envio, conforme exige a LGPD. Cada e-mail é cadastrado uma única vez.", False),
                ("Armazenamento de preferências no navegador", "Usamos armazenamento local do navegador (sessionStorage/localStorage) só para lembrar que você já fechou um pop-up ou já concluiu um cadastro, evitando mostrá-lo de novo. Isso fica só no seu aparelho — não é enviado a nós nem a terceiros.", False),
                ("Com quem compartilhamos", "Seus dados não são vendidos nem compartilhados publicamente. Quando o pagamento online estiver ativo, o valor da reserva é processado pelo Mercado Pago, que recebe só o necessário para a cobrança. O armazenamento dos dados é feito em banco de dados (Supabase) com acesso restrito à equipe do clube.", False),
                ("Seus direitos", "Você pode pedir a qualquer momento para acessar, corrigir ou excluir seus dados, e cancelar o recebimento de e-mails de novidades quando quiser. Basta falar com a equipe pela página de contato.", False),
                ("Contato", "Dúvidas sobre esta política ou sobre seus dados: fale com a equipe pela página de contato do site.", False),
            ],
            "note": "Este texto é um resumo em linguagem simples das práticas do clube. Recomendamos revisão jurídica antes de qualquer uso comercial mais amplo dos dados coletados.",
        },
        "en": {
            "title": "Privacy Policy — Good Vibes Va'a",
            "description": "How Good Vibes Va'a collects, uses and protects the personal data of site visitors and newsletter subscribers.",
            "h1": "Privacy Policy.",
            "lead": "How we handle the data of people who visit the site, make a request, or subscribe to our list — under Brazil's General Data Protection Law (LGPD).",
            "updated": "Last updated: November 2026.",
            "sections": [
                ("What data we collect", "Name, WhatsApp number and, when applicable, email — only when you provide them yourself, when requesting a booking, a quote, sending a message through the contact page, or subscribing to our newsletter. We do not collect browsing data, location, or data from other sites.", False),
                ("What we use it for", "To reply to your request (booking, quote, question) and, only with your separate and explicit consent, to send news and offers from Good Vibes Va'a by email.", False),
                ("Newsletter sign-up", "We store the email you provide, the site language at the time of sign-up, and the exact consent text you accepted — this serves as proof of your authorization, as required by the LGPD. Each email is registered only once.", False),
                ("Browser preference storage", "We use browser-local storage (sessionStorage/localStorage) only to remember that you've already closed a pop-up or completed a sign-up, so we don't show it again. This stays on your device only — it isn't sent to us or to third parties.", False),
                ("Who we share data with", "Your data is never sold or shared publicly. When online payment is active, the booking amount is processed by Mercado Pago, which only receives what's needed to charge it. Data storage is handled in a database (Supabase) with access restricted to the club's team.", False),
                ("Your rights", "You can ask at any time to access, correct or delete your data, and unsubscribe from newsletter emails whenever you want. Just message the team through the contact page.", False),
                ("Contact", "Questions about this policy or your data: message the team through the site's contact page.", False),
            ],
            "note": "This text is a plain-language summary of the club's practices. We recommend legal review before any broader commercial use of the data collected.",
        },
    },

    # -----------------------------------------------------------------
    # Termos de Uso — RASCUNHO. Só o que o site já faz hoje está escrito
    # como fato; o resto é ponto em aberto, marcado como pendente.
    # -----------------------------------------------------------------
    "termos": {
        "slug": "termos",
        "draft": True,
        "pt": {
            "title": "Termos de Uso — Good Vibes Va'a",
            "description": "Condições de uso do site do Good Vibes Va'a. Documento em elaboração, pendente de validação pelo clube e de revisão jurídica.",
            "h1": "Termos de Uso.",
            "lead": "As condições de uso deste site e dos canais de atendimento do clube.",
            "updated": "Documento em elaboração.",
            "sections": [
                ("Quem opera este site", "O site é mantido pelo Good Vibes Va'a, clube de canoa havaiana na Praia da Preguiça, em Salvador, Bahia. O atendimento é feito pela equipe do clube pelos canais listados na página de contato.", False),
                ("O que o site oferece", "Informação sobre as experiências do clube, solicitação de reserva e orçamento, contato com a equipe e apresentação da linha de produtos. O site não processa pagamento no momento: toda reserva é confirmada pela equipe antes de qualquer cobrança.", False),
                ("Informações sujeitas a confirmação", "Horários, valores, vagas e condições das experiências dependem do mar e da agenda do clube, e são confirmados pela equipe a cada reserva. O que aparece no site antes dessa confirmação é indicativo.", False),
                ("Uso do conteúdo e da marca", "Condições de uso das fotografias, textos e da marca Good Vibes Va'a por terceiros — o clube ainda precisa definir o que é permitido (por exemplo, uso por parceiros, imprensa e alunos nas redes).", True),
                ("Responsabilidade na prática esportiva", "Canoa havaiana é atividade física em mar aberto. As condições de participação, o termo de responsabilidade assinado antes da saída, exigências de saúde e a existência de seguro precisam ser definidos pelo clube e revisados juridicamente antes de virarem texto público.", True),
                ("Cadastro e dados pessoais", "O tratamento de dados pessoais está descrito na Política de Privacidade, que faz parte destes termos.", False),
                ("Alterações destes termos", "Como e com que aviso prévio o clube pode alterar estas condições — a definir.", True),
                ("Legislação aplicável e foro", "Legislação aplicável e foro eleito para resolução de conflitos — a definir com apoio jurídico.", True),
            ],
            "note": "Enquanto este documento estiver marcado como rascunho, ele não vale como termo de uso em vigor. Para dúvidas sobre participação, condições ou responsabilidade, fale com a equipe pela página de contato.",
        },
        "en": {
            "title": "Terms of Use — Good Vibes Va'a",
            "description": "Terms of use for the Good Vibes Va'a website. A working draft, pending club validation and legal review.",
            "h1": "Terms of Use.",
            "lead": "The conditions for using this site and the club's service channels.",
            "updated": "Document in progress.",
            "sections": [
                ("Who runs this site", "The site is maintained by Good Vibes Va'a, an outrigger canoe club at Praia da Preguiça, in Salvador, Bahia, Brazil. Support is handled by the club's team through the channels listed on the contact page.", False),
                ("What the site offers", "Information about the club's experiences, booking and quote requests, contact with the team, and a presentation of the club's product line. The site does not process payments at this time: every booking is confirmed by the team before any charge.", False),
                ("Information subject to confirmation", "Times, prices, available seats and conditions depend on the sea and on the club's schedule, and are confirmed by the team for each booking. Anything shown before that confirmation is indicative.", False),
                ("Use of content and brand", "Conditions for third-party use of Good Vibes Va'a photographs, texts and brand — the club still needs to define what is allowed (for example, use by partners, press and members on social media).", True),
                ("Responsibility in the sport", "Outrigger canoeing is a physical activity in open water. Participation requirements, the liability waiver signed before each outing, health requirements and insurance coverage must be defined by the club and legally reviewed before becoming public text.", True),
                ("Sign-up and personal data", "Personal data handling is described in the Privacy Policy, which forms part of these terms.", False),
                ("Changes to these terms", "How and with how much notice the club may change these conditions — to be defined.", True),
                ("Applicable law and jurisdiction", "Applicable law and the jurisdiction for resolving disputes — to be defined with legal support.", True),
            ],
            "note": "While this document is marked as a draft, it does not constitute terms of use in force. For questions about participation, conditions or liability, talk to the team through the contact page.",
        },
    },

    # -----------------------------------------------------------------
    # Diretrizes da Comunidade — RASCUNHO.
    # -----------------------------------------------------------------
    "diretrizes": {
        "slug": "diretrizes",
        "draft": True,
        "pt": {
            "title": "Diretrizes da Comunidade — Good Vibes Va'a",
            "description": "Como a comunidade do Good Vibes Va'a convive dentro e fora da água. Documento em elaboração, pendente de validação pelo clube.",
            "h1": "Diretrizes da Comunidade.",
            "lead": "Na canoa, o ritmo é coletivo. Estas diretrizes reúnem o que o clube espera de quem rema com a gente.",
            "updated": "Documento em elaboração.",
            "sections": [
                ("Por que existem", "A canoa havaiana é um esporte de equipe: uma remada fora do tempo atrapalha o barco inteiro. O mesmo vale para a convivência em terra. Estas diretrizes existem para que todo mundo saiba o que esperar do clube e o que o clube espera de volta.", False),
                ("Orientação dos capitães", "Quem comanda a saída é o capitão ou a capitã. As orientações de remada, de posição no barco e de segurança dadas antes e durante a saída valem para todos, inclusive para quem já tem experiência.", False),
                ("Respeito dentro e fora da água", "O compromisso do clube com um ambiente seguro e acolhedor, e o que caracteriza conduta inaceitável — o clube precisa definir esse texto na própria voz antes de publicá-lo.", True),
                ("Uso de imagem", "Fotos e vídeos das saídas e eventos são parte da vida do clube. Como funciona a autorização de uso de imagem, como pedir que uma foto sua não seja publicada e o uso das imagens pelos alunos — a definir.", True),
                ("Cuidado com o equipamento e com o mar", "Responsabilidade sobre canoas, remos e coletes, e as práticas de preservação da baía que o clube quer firmar como compromisso — a definir.", True),
                ("Faltas, atrasos e vaga nas saídas", "Como o clube trata atrasos e faltas em treinos e saídas, e o efeito disso na vaga de quem está na fila — a definir junto com a política de reservas.", True),
                ("Quando alguém não segue as diretrizes", "Como o clube conduz uma conversa dessas e quais são as consequências — a definir.", True),
            ],
            "note": "Enquanto este documento estiver marcado como rascunho, ele não vale como regra em vigor. As orientações de segurança dadas pelos capitães antes de cada saída valem sempre, independentemente deste texto.",
        },
        "en": {
            "title": "Community Guidelines — Good Vibes Va'a",
            "description": "How the Good Vibes Va'a community works together, on and off the water. A working draft, pending club validation.",
            "h1": "Community Guidelines.",
            "lead": "In a canoe, the rhythm is collective. These guidelines gather what the club expects from everyone who paddles with us.",
            "updated": "Document in progress.",
            "sections": [
                ("Why they exist", "Outrigger canoeing is a team sport: a single stroke out of time throws off the whole boat. The same goes for life on land. These guidelines exist so everyone knows what to expect from the club, and what the club expects back.", False),
                ("The captains lead", "The captain leads every outing. Instructions about paddling, seat position and safety, given before and during the outing, apply to everyone — experienced paddlers included.", False),
                ("Respect on and off the water", "The club's commitment to a safe and welcoming environment, and what counts as unacceptable conduct — the club needs to write this in its own voice before publishing it.", True),
                ("Use of images", "Photos and videos of outings and events are part of club life. How image-use consent works, how to ask that a photo of you not be published, and how members may use club images — to be defined.", True),
                ("Care for the equipment and the sea", "Responsibility for canoes, paddles and life vests, and the bay-preservation practices the club wants to commit to — to be defined.", True),
                ("Absences, lateness and seats", "How the club handles lateness and no-shows at training sessions and outings, and what that means for people on the waiting list — to be defined alongside the booking policy.", True),
                ("When someone does not follow the guidelines", "How the club handles that conversation and what the consequences are — to be defined.", True),
            ],
            "note": "While this document is marked as a draft, it does not constitute rules in force. The safety instructions given by the captains before each outing always apply, regardless of this text.",
        },
    },

    # -----------------------------------------------------------------
    # Reservas e cancelamentos — RASCUNHO. Prazo, reembolso e remarcação
    # tem efeito comercial direto: nada aqui pode ser inventado.
    # -----------------------------------------------------------------
    "reservas": {
        "slug": "reservas",
        "draft": True,
        "pt": {
            "title": "Política de Reservas e Cancelamentos — Good Vibes Va'a",
            "description": "Como reservar uma experiência no Good Vibes Va'a e o que acontece em caso de cancelamento. Documento em elaboração, pendente de validação pelo clube.",
            "h1": "Reservas e Cancelamentos.",
            "lead": "Como funciona reservar uma saída com o clube, e o que acontece quando o mar ou a vida mudam o plano.",
            "updated": "Documento em elaboração.",
            "sections": [
                ("Como reservar", "Pelo site, escolhendo a experiência e enviando a solicitação, ou direto pelo WhatsApp. A solicitação não é uma vaga garantida: ela abre uma conversa com a equipe.", False),
                ("Confirmação da vaga", "A equipe confirma a reserva informando horário, ponto de encontro e valor. Sua vaga está garantida a partir dessa confirmação, não antes.", False),
                ("Condições do mar", "A equipe acompanha as condições do mar antes de cada saída. Quando o mar não permite, a saída não acontece e a equipe entra em contato para combinar uma nova data.", False),
                ("Prazo para cancelar", "Com quanta antecedência uma reserva pode ser cancelada sem custo — a definir pelo clube.", True),
                ("Reembolso", "Se houver sinal ou pagamento antecipado, em que casos ele é devolvido, em quanto tempo e por qual meio — a definir pelo clube.", True),
                ("Remarcação", "Quantas vezes e com qual antecedência uma saída pode ser remarcada, e por quanto tempo o crédito vale — a definir pelo clube.", True),
                ("Atraso e não comparecimento", "Tolerância de atraso no ponto de encontro e o que acontece com quem não comparece sem avisar — a definir pelo clube.", True),
                ("Grupos, aniversários e empresas", "Experiências particulares envolvem reserva exclusiva da canoa e da agenda da equipe. Condições próprias de sinal, prazo e cancelamento para esses casos — a definir pelo clube.", True),
                ("Planos de treino, Gympass e TotalPass", "Regras de cancelamento e de falta nos planos recorrentes e nos check-ins por aplicativo — a definir pelo clube, junto com as regras dos próprios aplicativos.", True),
            ],
            "note": "Enquanto este documento estiver marcado como rascunho, as condições de cada reserva são as que a equipe informar na confirmação pelo WhatsApp. Nenhum prazo, reembolso ou multa deve ser presumido a partir deste texto.",
        },
        "en": {
            "title": "Booking and Cancellation Policy — Good Vibes Va'a",
            "description": "How to book an experience at Good Vibes Va'a and what happens in case of cancellation. A working draft, pending club validation.",
            "h1": "Bookings and Cancellations.",
            "lead": "How booking an outing with the club works, and what happens when the sea — or life — changes the plan.",
            "updated": "Document in progress.",
            "sections": [
                ("How to book", "Through the site, by choosing an experience and sending a request, or directly on WhatsApp. A request is not a guaranteed seat: it opens a conversation with the team.", False),
                ("Seat confirmation", "The team confirms the booking with the time, meeting point and price. Your seat is guaranteed from that confirmation onward, not before.", False),
                ("Sea conditions", "The team checks sea conditions before every outing. When the sea does not allow it, the outing does not happen and the team gets in touch to arrange a new date.", False),
                ("Cancellation notice", "How far in advance a booking can be cancelled at no cost — to be defined by the club.", True),
                ("Refunds", "If a deposit or advance payment applies, in which cases it is refunded, how long it takes and by which method — to be defined by the club.", True),
                ("Rescheduling", "How many times and with how much notice an outing can be rescheduled, and how long any credit remains valid — to be defined by the club.", True),
                ("Lateness and no-shows", "Grace period at the meeting point and what happens to someone who does not show up without notice — to be defined by the club.", True),
                ("Groups, birthdays and companies", "Private experiences involve exclusive booking of the canoe and of the team's schedule. Specific deposit, notice and cancellation conditions for these cases — to be defined by the club.", True),
                ("Training plans, Gympass and TotalPass", "Cancellation and no-show rules for recurring plans and app check-ins — to be defined by the club, alongside the rules of the apps themselves.", True),
            ],
            "note": "While this document is marked as a draft, the conditions for each booking are the ones the team states in the WhatsApp confirmation. No deadline, refund or penalty should be assumed from this text.",
        },
    },
}
