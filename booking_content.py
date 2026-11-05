"""
Textos do fluxo de reserva e do pop-up do WhatsApp (PT e EN).

As experiências e valores abaixo são ILUSTRATIVOS e só aparecem no modo
"demo" (com aviso visível). No modo "live", experiências, horários, vagas e
preços vêm do backend do clube.
"""

import random

DEMO_EXPERIENCES = {
    "pt": [
        {"id": "primeira", "name": "Primeira experiência", "desc": "Introdução ao esporte com o capitão. Ideal para quem nunca remou.", "time": "08:00", "dur": "1h", "price": 100},
        {"id": "nascer", "name": "Nascer do sol", "desc": "Saída cedo, mar calmo e a cidade acordando vista da baía.", "time": "05:30", "dur": "1h30", "price": 120},
        {"id": "por", "name": "Pôr do sol", "desc": "O fim de tarde de Salvador visto de dentro da Baía de Todos-os-Santos.", "time": "16:30", "dur": "1h30", "price": 120},
        {"id": "turismo", "name": "Turismo náutico", "desc": "A orla e a história da cidade a partir do mar.", "time": "09:30", "dur": "2h", "price": 150},
    ],
    "en": [
        {"id": "primeira", "name": "First-time session", "desc": "An introduction to the sport with a captain. Ideal if you've never paddled.", "time": "08:00", "dur": "1h", "price": 100},
        {"id": "nascer", "name": "Sunrise paddle", "desc": "An early start, calm water and the city waking up, seen from the bay.", "time": "05:30", "dur": "1h30", "price": 120},
        {"id": "por", "name": "Sunset paddle", "desc": "Salvador's late afternoon, seen from inside the Bay of All Saints.", "time": "16:30", "dur": "1h30", "price": 120},
        {"id": "turismo", "name": "Sea tour", "desc": "The city's waterfront and history, seen from the water.", "time": "09:30", "dur": "2h", "price": 150},
    ],
}

# Horários de "Treinar" ainda não definidos pelo clube — gerados com seed fixa
# (sempre o mesmo resultado a cada build) só para servir de exemplo visual.
# Trocar pelos horários reais quando o clube confirmar (ver docs/SETUP.md).
def _generate_training_schedule(locale):
    names = (
        ["Treino regular", "Técnica de remada", "Condicionamento físico", "Treino de resistência"]
        if locale == "pt" else
        ["Regular training", "Paddling technique", "Fitness conditioning", "Endurance training"]
    )
    descs = (
        [
            "Treino de base do clube, remada em grupo com um capitão.",
            "Foco em pegada, catch e sincronia de remada em dupla ou na canoa.",
            "Trabalho físico fora da canoa para ganhar resistência na água.",
            "Remada mais longa, ritmo constante, para quem já tem uma base.",
        ] if locale == "pt" else [
            "The club's base training, group paddling with a captain.",
            "Focus on catch, stroke and timing, in pairs or in the canoe.",
            "Off-water conditioning work to build stamina on the water.",
            "A longer, steady-pace paddle for people who already have a base.",
        ]
    )
    durs = (
        ["1h", "1h30", "1h", "1h30"]
        if locale == "pt" else
        ["1h", "1h30", "1h", "1h30"]
    )
    # weekdays segue Date.getDay() do JS: 0=domingo ... 6=sábado.
    slots = [
        {"time": "06:00", "weekdays": [1, 3, 5], "instructorKey": "captain_jesse", "instructor": "Jesse", "capacity": 10},
        {"time": "18:00", "weekdays": [2, 4], "instructorKey": "captain_nala", "instructor": "Nala", "capacity": 10},
        {"time": "08:00", "weekdays": [6], "instructorKey": "captain_jesse", "instructor": "Jesse", "capacity": 6},
        {"time": "07:00", "weekdays": [0], "instructorKey": "captain_nala", "instructor": "Nala", "capacity": 8},
    ]
    shuffled = slots[:]
    random.Random(7).shuffle(shuffled)
    out = [
        {
            "id": f"treino-{i}",
            "name": names[i],
            "desc": descs[i],
            "dur": durs[i],
            "price": None,
            **slot,
        }
        for i, slot in enumerate(shuffled)
    ]
    out.sort(key=lambda a: (min(a["weekdays"]), a["time"]))
    return out


TRAINING_SCHEDULE = {
    "pt": _generate_training_schedule("pt"),
    "en": _generate_training_schedule("en"),
}

# As três jornadas de agendamento, mesma "casca" visual (calendário + cartões
# + modal), comportamento por "flow":
#   "calendar+pix"     -> Experimentar: calendário real, pagamento Pix.
#   "calendar+request" -> Treinar: calendário (horários acima), sem cobrança
#                         nesta etapa — a vaga é travada e confirmada direto.
#   "quote"             -> Particular: sem calendário, é sempre orçamento.
MODALITIES = {
    "pt": [
        {"key": "experimentar", "flow": "calendar+pix", "accent": "ocean", "activities": DEMO_EXPERIENCES["pt"]},
        {"key": "treinar", "flow": "calendar+request", "accent": "forest", "activities": TRAINING_SCHEDULE["pt"]},
        {"key": "particular", "flow": "quote", "accent": "sand", "activities": []},
    ],
    "en": [
        {"key": "experimentar", "flow": "calendar+pix", "accent": "ocean", "activities": DEMO_EXPERIENCES["en"]},
        {"key": "treinar", "flow": "calendar+request", "accent": "forest", "activities": TRAINING_SCHEDULE["en"]},
        {"key": "particular", "flow": "quote", "accent": "sand", "activities": []},
    ],
}

BOOKING = {
    "pt": {
        "title": "Reserve sua remada",
        "demo": "Demonstração: experiências, valores e vagas são ilustrativos. Nada é cobrado.",
        "step": "{n} de {t}",
        "steps": ["Dia e horário", "Participantes", "Termo", "Pagamento"],
        "board_title": "Escolha sua saída.",
        "board_subtitle": "Reserve em menos de um minuto. Confirmação imediata no WhatsApp.",
        "board_steps": [
            "Escolha a saída e o dia",
            "Assine o termo e pague o sinal por Pix",
            "Receba a confirmação e o lembrete no WhatsApp",
        ],
        "board_wa_prefix": "Prefere falar com alguém?",
        "low_seats_one": "Última vaga",
        "low_seats_many": "Últimas {n} vagas",
        "back": "Voltar",
        "next": "Continuar",
        "to_pay": "Ir para o pagamento",
        "per_person": "por pessoa",
        "departure": "Saída às {t}",
        "day": "Dia",
        "slots": "Saídas",
        "today": "hoje",
        "free": "{n} de {c} lugares livres",
        "full": "Esgotado",
        "pick_slot": "Escolha uma saída para continuar.",
        "people": "Participantes",
        "seats_after_one": "Depois da sua reserva, 1 lugar continua livre nesta canoa.",
        "seats_after_many": "Depois da sua reserva, {n} lugares continuam livres nesta canoa.",
        "seats_after_none": "Depois da sua reserva, a canoa fica completa.",
        "name": "Nome do responsável",
        "phone": "WhatsApp",
        "phone_hint": "Enviamos a confirmação e o lembrete por aqui.",
        "err_name": "Informe o nome do responsável.",
        "err_phone": "Informe um WhatsApp com DDD.",
        "err_terms": "Aceite o termo para continuar.",
        "terms": [
            "Declaro estar ciente de que a canoa havaiana é uma atividade realizada no mar, sujeita a condições climáticas e de maré, e que seguirei as orientações do capitão durante toda a saída.",
            "Declaro que informei à equipe qualquer condição de saúde relevante dos participantes.",
            "Autorizo o clube a remarcar a saída sem custo caso as condições do mar não sejam seguras.",
        ],
        "terms_note": "Modelo para demonstração. O texto final deve ser revisado juridicamente.",
        "terms_accept": "Li e aceito o termo em nome de todos os participantes desta reserva.",
        "total": "Total",
        "deposit": "Sinal agora (50%)",
        "remaining": "Restante no dia",
        "pix_valid": "Código válido por {t}. Sua vaga fica reservada até lá.",
        "pix_alt": "QR Code Pix ilustrativo",
        "copy": "Copiar código Pix",
        "copied": "Código copiado.",
        "waiting": "Aguardando o pagamento",
        "sim_pay": "Simular pagamento aprovado",
        "expired": "O código expirou e a vaga foi liberada.",
        "regen": "Gerar novo código",
        "done_title": "Reserva confirmada",
        "code": "Código",
        "when": "Quando",
        "who": "Participantes",
        "experience": "Experiência",
        "paid": "Sinal pago",
        "meeting": "Encontro na Praia da Preguiça, 15 minutos antes da saída.",
        "wa_note": "A confirmação também chega no WhatsApp informado, com lembrete na véspera.",
        "ics": "Adicionar à agenda",
        "again": "Fazer outra reserva",
        "ics_title": "Remada Good Vibes Va'a",
        "error": "Não foi possível concluir agora. Tente de novo em instantes.",
        "weekdays": ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
        "months": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
        "req_demo": "Solicitação registrada (demonstração). Na versão final, a equipe recebe na hora e responde pelo WhatsApp informado.",
        "req_live": "Solicitação enviada. A equipe responde em breve pelo WhatsApp informado.",
        "send_request": "Enviar solicitação",
        "send_quote": "Pedir orçamento",
        "price_on_request": "Sob consulta",
        "with_instructor": "com {name}",
        "modal_close": "Fechar",
        "no_dates": "Sem turmas nos próximos dias.",
        "already_train_q": "Você já treina no clube?",
        "already_train_yes": "Sim, já treino",
        "already_train_no": "Não, seria minha primeira vez",
        "level_label": "Nível",
        "level_options": [["nunca", "Nunca remei"], ["algumas", "Algumas vezes"], ["pratico", "Já pratico"]],
        "notes_label": "Observações (opcional)",
        "request_title": "Solicitar vaga",
        "train_done_note": "Vaga garantida nesta turma. A equipe confirma os detalhes pelo WhatsApp informado.",
        "quote_title": "Peça um orçamento",
        "quote_lead": "Grupos, aniversários, eventos corporativos ou uma remada só para vocês — conte os detalhes e te mandamos uma proposta.",
        "type_label": "Tipo de experiência",
        "type_options": [["grupo", "Grupo"], ["aniversario", "Aniversário"], ["corporativo", "Evento corporativo"], ["privada", "Experiência privada"]],
        "date_label": "Data desejada",
        "people_label": "Número de pessoas",
        "details_label": "Conte mais",
        "details_hint": "Ocasião, horário preferido, se o grupo já remou.",
        "quote_done_title": "Pedido de orçamento enviado",
        "quote_done_note": "A equipe responde com uma proposta pelo WhatsApp informado.",
        "sending": "Enviando…",
        "loading": "Carregando…",
    },
    "en": {
        "title": "Book your paddle",
        "demo": "Demo: experiences, prices and availability are illustrative. Nothing is charged.",
        "step": "{n} of {t}",
        "steps": ["Date and time", "Participants", "Waiver", "Payment"],
        "board_title": "Choose your departure.",
        "board_subtitle": "Book in under a minute. Instant confirmation on WhatsApp.",
        "board_steps": [
            "Choose the departure and day",
            "Sign the waiver and pay the deposit by Pix",
            "Get your confirmation and reminder on WhatsApp",
        ],
        "board_wa_prefix": "Prefer to talk to someone?",
        "low_seats_one": "Last seat",
        "low_seats_many": "Last {n} seats",
        "back": "Back",
        "next": "Continue",
        "to_pay": "Go to payment",
        "per_person": "per person",
        "departure": "Departs at {t}",
        "day": "Date",
        "slots": "Departures",
        "today": "today",
        "free": "{n} of {c} seats free",
        "full": "Sold out",
        "pick_slot": "Choose a departure to continue.",
        "people": "Participants",
        "seats_after_one": "After your booking, 1 seat remains free in this canoe.",
        "seats_after_many": "After your booking, {n} seats remain free in this canoe.",
        "seats_after_none": "After your booking, the canoe is full.",
        "name": "Lead name",
        "phone": "WhatsApp",
        "phone_hint": "We send your confirmation and reminder here.",
        "err_name": "Enter the lead participant's name.",
        "err_phone": "Enter a WhatsApp number with area code.",
        "err_terms": "Accept the waiver to continue.",
        "terms": [
            "I understand that outrigger paddling takes place at sea, is subject to weather and tide conditions, and I will follow the captain's instructions throughout the outing.",
            "I have told the team about any relevant health conditions of the participants.",
            "I authorise the club to reschedule at no cost if sea conditions are not safe.",
        ],
        "terms_note": "Demo template. The final text must be reviewed by a lawyer.",
        "terms_accept": "I have read and accept the waiver on behalf of everyone in this booking.",
        "total": "Total",
        "deposit": "Deposit now (50%)",
        "remaining": "Balance on the day",
        "pix_valid": "Code valid for {t}. Your seats are held until then.",
        "pix_alt": "Illustrative Pix QR code",
        "copy": "Copy Pix code",
        "copied": "Code copied.",
        "waiting": "Waiting for payment",
        "sim_pay": "Simulate approved payment",
        "expired": "The code expired and the seats were released.",
        "regen": "Generate a new code",
        "done_title": "Booking confirmed",
        "code": "Code",
        "when": "When",
        "who": "Participants",
        "experience": "Experience",
        "paid": "Deposit paid",
        "meeting": "Meet at Praia da Preguiça, 15 minutes before departure.",
        "wa_note": "You'll also get the confirmation on WhatsApp, with a reminder the day before.",
        "ics": "Add to calendar",
        "again": "Make another booking",
        "ics_title": "Good Vibes Va'a paddle",
        "error": "We couldn't complete this right now. Please try again shortly.",
        "weekdays": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "req_demo": "Request recorded (demo). In the final version, the team receives it instantly and replies on WhatsApp.",
        "req_live": "Request sent. The team will reply soon on the WhatsApp number you gave.",
        "send_request": "Send request",
        "send_quote": "Request a quote",
        "price_on_request": "Price on request",
        "with_instructor": "with {name}",
        "modal_close": "Close",
        "no_dates": "No classes in the next few days.",
        "already_train_q": "Do you already train with the club?",
        "already_train_yes": "Yes, I already train here",
        "already_train_no": "No, this would be my first time",
        "level_label": "Level",
        "level_options": [["nunca", "Never paddled"], ["algumas", "A few times"], ["pratico", "I paddle regularly"]],
        "notes_label": "Notes (optional)",
        "request_title": "Request a spot",
        "train_done_note": "Your spot in this class is guaranteed. The team confirms details on the WhatsApp number you gave.",
        "quote_title": "Request a quote",
        "quote_lead": "Groups, birthdays, corporate events or a paddle just for you — tell us the details and we'll send a proposal.",
        "type_label": "Type of experience",
        "type_options": [["grupo", "Group"], ["aniversario", "Birthday"], ["corporativo", "Corporate event"], ["privada", "Private experience"]],
        "date_label": "Desired date",
        "people_label": "Number of people",
        "details_label": "Tell us more",
        "details_hint": "Occasion, preferred time, whether the group has paddled before.",
        "quote_done_title": "Quote request sent",
        "quote_done_note": "The team will reply with a proposal on the WhatsApp number you gave.",
        "sending": "Sending…",
        "loading": "Loading…",
    },
}

WA_WIDGET = {
    "pt": {
        "open": "Falar com a equipe no WhatsApp",
        "title": "Good Vibes Va'a",
        "status": "Equipe do clube",
        "msg": "Oi! Ficou alguma dúvida antes de reservar? Escreva aqui e continue a conversa no nosso WhatsApp.",
        "placeholder": "Escreva sua mensagem",
        "send": "Continuar no WhatsApp",
        "close": "Fechar",
        "default": "Olá, Good Vibes Va'a! Tenho uma dúvida.",
    },
    "en": {
        "open": "Talk to the team on WhatsApp",
        "title": "Good Vibes Va'a",
        "status": "Club team",
        "msg": "Hi! Any questions before booking? Write here and continue the chat on our WhatsApp.",
        "placeholder": "Write your message",
        "send": "Continue on WhatsApp",
        "close": "Close",
        "default": "Hi Good Vibes Va'a! I have a question.",
    },
}
