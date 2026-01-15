import urllib.parse
from datetime import timedelta

class AmenitiesGenerator:
    def __init__(self):
        # 1. Termos de Busca Google Maps (Gastronomia)
        self.STYLE_TERMS = {
            'econômico': "Restaurantes baratos",
            'moderado': "Restaurantes bem avaliados",
            'conforto': "Restaurantes charmosos",
            'luxo': "Restaurantes Michelin",
            'super_luxo': "Fine dining awards"
        }
        
        # 2. Termos de Compras (Novo!)
        self.SHOPPING_TERMS = {
            'econômico': "Outlets e feiras de rua",
            'moderado': "Shopping centers e comércio local",
            'conforto': "Shopping centers e lojas de departamento",
            'luxo': "Boutiques de luxo e designer stores",
            'super_luxo': "High end fashion boutiques personal shopper"
        }

        # 3. Ordenação Booking
        self.BOOKING_ORDER = {
            'econômico': 'price',
            'moderado': 'review_score_and_price',
            'conforto': 'bayesian_review_score',
            'luxo': 'class_descending',
            'super_luxo': 'class_descending'
        }

    def _clean(self, text):
        return urllib.parse.quote_plus(text)

    def generate_concierge_links(self, destination, style, start_date=None, days=0):
        """
        Gera um dicionário completo com TODOS os links possíveis.
        O app.py decide quais mostrar baseado na escolha do usuário.
        """
        
        # Sanitização
        style_key = style.lower()
        if "super" in style_key: style_key = "super_luxo"
        elif "econ" in style_key: style_key = "econômico"

        # A. Datas
        date_params = ""
        date_str = ""
        if start_date:
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            try: date_str = f"{meses[start_date.month-1]} {start_date.year}"
            except: pass
            if days > 0:
                end_date = start_date + timedelta(days=days)
                date_params = f"&checkin={start_date}&checkout={end_date}"

        # --- GERAÇÃO DOS LINKS ---

        # 1. FIXOS (Obrigatórios)
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        booking_order = self.BOOKING_ORDER.get(style_key, 'review_score_and_price')
        hotel_url = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}{date_params}&order={booking_order}"
        
        insurance_url = "https://www.google.com/search?q=seguro+viagem+cotacao"

        # 2. VARIÁVEIS (Dependem da escolha)
        
        # Gastronomia (Google Maps)
        food_term = self.STYLE_TERMS.get(style_key, "Restaurantes")
        food_url = f"https://www.google.com/maps/search/{self._clean(food_term + ' em ' + destination)}"
        
        # Compras (Google Maps - Novo)
        shop_term = self.SHOPPING_TERMS.get(style_key, "Shopping")
        shop_url = f"https://www.google.com/maps/search/{self._clean(shop_term + ' em ' + destination)}"

        # Vida Noturna (Viator ou Google)
        # Viator converte melhor para festa organizada, Google melhor para bares soltos. 
        # Vamos de Viator para monetizar "Pub Crawls" e "Shows".
        night_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' nightlife pub crawl')}"

        # Arte & Cultura (Viator - Museus e Tickets)
        cult_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' museum tickets historical tours')}"

        # Natureza & Ar Livre (Viator)
        nature_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' outdoor activities parks hiking')}"
        
        # Agenda (Google Search)
        event_url = f"https://www.google.com/search?q=agenda+cultural+eventos+{self._clean(destination)}+{self._clean(date_str)}"

        return {
            "flight":    {"url": flight_url,    "label": "Monitorar Voos", "icon": "✈️"},
            "hotel":     {"url": hotel_url,     "label": "Ver Hotéis",     "icon": "🏨"},
            "insurance": {"url": insurance_url, "label": "Seguro Viagem",  "icon": "🛡️"},
            
            "food":      {"url": food_url,      "label": "Gastronomia",    "icon": "🍽️"},
            "shopping":  {"url": shop_url,      "label": "Compras & Lojas", "icon": "🛍️"},
            "night":     {"url": night_url,     "label": "Vida Noturna",   "icon": "🍸"},
            "culture":   {"url": cult_url,      "label": "Arte & Cultura", "icon": "🏛️"},
            "nature":    {"url": nature_url,    "label": "Ar Livre",       "icon": "🍃"},
            "event":     {"url": event_url,     "label": "Agenda Local",   "icon": "📅"}
        }
