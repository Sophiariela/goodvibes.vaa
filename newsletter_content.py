"""
Textos do pop-up de captação de e-mail e configuração da campanha
promocional (PT e EN) — ver README.md / CLAUDE.md para como o pop-up
decide quando aparecer e como a campanha liga/desliga.
"""

NEWSLETTER = {
    "pt": {
        "title": "Entre para o universo Good Vibes.",
        "text": "Novidades, lançamentos, experiências e benefícios exclusivos. Deixe seu e-mail e fique mais perto da nossa comunidade.",
        "email_label": "Seu melhor e-mail",
        "email_placeholder": "nome@email.com",
        "consent_label": "Quero receber novidades e ofertas da Good Vibes Va'a por e-mail.",
        "privacy_prefix": "Seus dados são tratados conforme a nossa ",
        "privacy_link": "política de privacidade",
        "cta": "Quero participar",
        "sending": "Enviando…",
        "close": "Fechar",
        "success_title": "Você está na lista!",
        "success_text": "Em breve teremos novidades para você.",
        "err_email": "Informe um e-mail válido.",
        "err_consent": "É preciso aceitar para continuar.",
        "duplicate_title": "Você já faz parte!",
        "duplicate_text": "Esse e-mail já está na nossa lista — obrigado por fazer parte da comunidade.",
        "err_generic": "Não foi possível cadastrar agora. Tente novamente em instantes.",
        "image_alt": "Comunidade Good Vibes Va'a reunida após o treino",
    },
    "en": {
        "title": "Join the Good Vibes universe.",
        "text": "News, launches, experiences and exclusive perks. Leave your email and get closer to our community.",
        "email_label": "Your best email",
        "email_placeholder": "name@email.com",
        "consent_label": "I want to receive news and offers from Good Vibes Va'a by email.",
        "privacy_prefix": "Your details are handled under our ",
        "privacy_link": "privacy policy",
        "cta": "Count me in",
        "sending": "Sending…",
        "close": "Close",
        "success_title": "You're on the list!",
        "success_text": "We'll have news for you soon.",
        "err_email": "Enter a valid email address.",
        "err_consent": "You need to accept to continue.",
        "duplicate_title": "You're already in!",
        "duplicate_text": "That email is already on our list — thanks for being part of the community.",
        "err_generic": "We couldn't sign you up right now. Please try again shortly.",
        "image_alt": "The Good Vibes Va'a community gathered after training",
    },
}

# ---------------------------------------------------------------------------
# Campanha promocional do pop-up — DESLIGADA por padrão.
#
# "enabled": False -> o pop-up mostra só o cadastro de e-mail simples (texto
# de NEWSLETTER acima), sem nenhuma promessa de prêmio ou benefício.
#
# Pra ligar uma campanha, usar "type": "early_access" (acesso antecipado a
# lançamentos) ou "coupon" (cupom de desconto real, preencher "coupon_code")
# — essas duas são seguras de ativar a qualquer momento, são um benefício
# garantido a quem se cadastra, não dependem de autorização legal especial.
#
# "type": "raffle" (sorteio/concorrer a um prêmio) é tratado como DESLIGADO
# em build.py (resolve_campaign) a não ser que "legal_cleared" esteja True —
# ligar isso exige regulamento registrado e autorizações conforme a Lei
# 5.768/71 e a legislação de promoções comerciais no Brasil. Não marcar
# "legal_cleared": True sem isso estar pronto de verdade.
# ---------------------------------------------------------------------------
CAMPAIGN = {
    "enabled": False,
    "type": "early_access",
    "legal_cleared": False,
    "pt": {
        "title": "Cadastre-se e garanta acesso antecipado.",
        "text": "Quem está na lista fica sabendo primeiro dos próximos lançamentos da Moda Good Vibes.",
        "coupon_code": "",
    },
    "en": {
        "title": "Sign up for early access.",
        "text": "The mailing list hears about the next Moda Good Vibes launches first.",
        "coupon_code": "",
    },
}
