"""
Catálogo de produtos da loja Good Vibes Va'a (/produtos).

Editar PRODUCTS para adicionar, remover ou corrigir uma peça — nada mais no
resto do projeto precisa mudar. Cada entrada:

  id           slug único (usado na âncora do produto e na mensagem de
               WhatsApp — não reutilizar entre produtos).
  photo        chave de PHOTOS em build.py (a foto já cadastrada da peça).
  name         {"pt": ..., "en": ...}
  description  {"pt": ..., "en": ...} — descrição curta e honesta da peça.
  category     {"pt": ..., "en": ...} (ex.: "Vestuário"/"Apparel",
               "Acessórios"/"Accessories").
  price_cents  preço em centavos (int) OU None se ainda não definido.
               NUNCA inventar um valor — None mostra "sob consulta"/
               "price on request" no site até o clube confirmar.
  sizes        lista de tamanhos disponíveis (ex.: ["P", "M", "G", "GG"])
               OU [] se não definido/não se aplica — a interface só mostra
               o seletor de tamanho quando a lista não está vazia.
  colors       lista de {"pt": nome, "en": nome, "hex": "#rrggbb"} OU [].
  stock        "available" | "low" | "out" | "unknown" — usar "unknown"
               até o clube confirmar a disponibilidade real; nunca marcar
               "available"/"out" sem informação de verdade.
"""

PRODUCTS = [
    {
        "id": "camisa-atleta",
        "photo": "product_1",
        "name": {"pt": "Camisa UV Atleta", "en": "Athlete UV Shirt"},
        "description": {
            "pt": "Camisa de manga comprida com a identidade Good Vibes Va'a, pensada para remar e para o dia a dia.",
            "en": "Long-sleeve shirt with the Good Vibes Va'a identity, made for paddling and everyday wear.",
        },
        "category": {"pt": "Vestuário", "en": "Apparel"},
        "price_cents": None,
        "sizes": [],
        "colors": [],
        "stock": "unknown",
    },
    {
        "id": "sacola",
        "photo": "product_2",
        "name": {"pt": "Sacola Good Vibes", "en": "Good Vibes Drawstring Bag"},
        "description": {
            "pt": "Sacola com cordão e a logo circular do clube — prática para a praia, o treino ou o dia a dia.",
            "en": "Drawstring bag with the club's circular logo — practical for the beach, training or everyday life.",
        },
        "category": {"pt": "Acessórios", "en": "Accessories"},
        "price_cents": None,
        "sizes": [],
        "colors": [],
        "stock": "unknown",
    },
    {
        "id": "viseira",
        "photo": "product_3",
        "name": {"pt": "Viseira Good Vibes", "en": "Good Vibes Visor"},
        "description": {
            "pt": "Viseira com a logo do clube, para proteger do sol nos treinos e passeios.",
            "en": "Visor with the club's logo, for sun protection during training and paddles.",
        },
        "category": {"pt": "Acessórios", "en": "Accessories"},
        "price_cents": None,
        "sizes": [],
        "colors": [],
        "stock": "unknown",
    },
    {
        "id": "bone",
        "photo": "product_4",
        "name": {"pt": "Boné Good Vibes", "en": "Good Vibes Cap"},
        "description": {
            "pt": "Boné respirável com a logo bordada do clube, ajuste confortável para o dia a dia.",
            "en": "Breathable cap with the club's embroidered logo, comfortable fit for everyday wear.",
        },
        "category": {"pt": "Acessórios", "en": "Accessories"},
        "price_cents": None,
        "sizes": [],
        "colors": [],
        "stock": "unknown",
    },
    {
        "id": "camisa-comemorativa",
        "photo": "product_5",
        "name": {"pt": "Camisa Comemorativa", "en": "Commemorative Shirt"},
        "description": {
            "pt": "Camisa de algodão da coleção comemorativa Good Vibes Va'a.",
            "en": "Cotton shirt from the Good Vibes Va'a commemorative collection.",
        },
        "category": {"pt": "Vestuário", "en": "Apparel"},
        "price_cents": None,
        "sizes": [],
        "colors": [],
        "stock": "unknown",
    },
]
