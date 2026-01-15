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
        
        # 2. Termos de Compras
        self.SHOPPING_TERMS = {
            'econômico': "Outlets e feiras de rua",
            'moderado': "Shopping centers e comércio local",
            'conforto': "Shopping centers e lojas de departamento",
            'luxo': "Boutiques de luxo e designer stores",
            'super_luxo': "High end fashion boutiques personal shopper"
        }

        # 3. Labels Dinâmicos (Incluindo Business)
        self.LABEL_MAP = {
            'business': {'food': 'Almoço Executivo', 'event': 'Feiras & Expo', 'attr': 'Coworking & Cafés'},
            'tourist_mix': {'food': 'Gastronomia', 'event': 'Agenda Cultural', 'attr': 'Principais Atrações'}
        }

        self.VIBE_FOOD_TERMS = {
            'gastro': "menu degustação",
            'festa': "animados com drinks",
            'romântico': "ambiente íntimo",
            'familiar': "com espaço kids",
            'natureza': "com vista",
            'cultura': "tradicionais",
            'business': "almoço executivo ambiente tranquilo" # Termo Business
        }

        # 4. Ordenação Booking
        self.BOOKING_ORDER = {
            'econômico': 'price',
            'moderado': 'review_score_and_price',
            'conforto': 'bayesian_review_score',
            'luxo': 'class_descending',
            'super_luxo': 'class_descending'
        }

    def _clean(self, text):
        return urllib.parse.quote_plus(text)

    def generate_concierge_links(self, destination, style, start_date=None, days=0, vibe="tourist_mix"):
        """
        Gera links incluindo a lógica Business e Gastronomia Fixa.
        """
        
        # Sanitização
        style_key = style.lower()
        if "super" in style_key: style_key = "super_luxo"
        elif "econ" in style_key: style_key = "econômico"
        
        vibe_key = vibe if vibe in self.VIBE_FOOD_TERMS else 'tourist_mix' # Fallback seguro

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

        # 1. FIXOS (Flight, Hotel, Food, Insurance)
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        booking_order = self.BOOKING_ORDER.get(style_key, 'review_score_and_price')
        hotel_url = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}{date_params}&order={booking_order}"
        
        # Gastronomia (Agora com termo Business se aplicável)
        food_style = self.STYLE_TERMS.get(style_key, "Restaurantes")
        food_vibe = self.VIBE_FOOD_TERMS.get(vibe_key, "")
        food_query = f"{food_style} em {destination} {food_vibe}"
        food_url = f"https://www.google.com/maps/search/{self._clean(food_query)}"
        
        # Label da comida muda se for Business
        food_label = "Gastronomia"
        if vibe_key == 'business': food_label = "Almoço Executivo"
        
        insurance_url = "https://www.google.com/search?q=seguro+viagem+cotacao"

        # 2. VARIÁVEIS (Concierge)
        
        # Compras
        shop_term = self.SHOPPING_TERMS.get(style_key, "Shopping")
        shop_url = f"https://www.google.com/maps/search/{self._clean(shop_term + ' em ' + destination)}"

        # Vida Noturna (Viator ou Google)
        night_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' nightlife pub crawl')}"

        # Arte & Cultura (Viator)
        cult_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' museum tickets historical tours')}"

        # Natureza (Viator)
        nature_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' outdoor activities parks hiking')}"
        
        # Agenda / Feiras
        event_query = "agenda cultural eventos"
        if vibe_key == 'business': event_query = "feiras de negocios congressos expo"
        event_url = f"https://www.google.com/search?q={self._clean(event_query)}+{self._clean(destination)}+{self._clean(date_str)}"
        event_label = "Agenda Local"
        if vibe_key == 'business': event_label = "Feiras & Expo"

        # Attr (Passeios ou Coworking)
        attr_label = "Principais Atrações"
        if vibe_key == 'business':
            # Se for Business, linka para Google Maps "Coworking"
            attr_label = "Coworking & Cafés"
            attr_url = f"https://www.google.com/maps/search/{self._clean('Coworking cafes com wifi em ' + destination)}"
        else:
            # Se for Lazer, linka para Viator
            attr_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' top attractions skip the line')}"

        return {
            "flight":    {"url": flight_url,    "label": "Monitorar Voos", "icon": "✈️"},
            "hotel":     {"url": hotel_url,     "label": "Ver Hotéis",     "icon": "🏨"},
            "food":      {"url": food_url,      "label": food_label,       "icon": "🍽️"},
            "insurance": {"url": insurance_url, "label": "Seguro Viagem",  "icon": "🛡️"},
            
            "shopping":  {"url": shop_url,      "label": "Compras & Lojas", "icon": "🛍️"},
            "night":     {"url": night_url,     "label": "Vida Noturna",   "icon": "🍸"},
            "culture":   {"url": cult_url,      "label": "Arte & Cultura", "icon": "🏛️"},
            "nature":    {"url": nature_url,    "label": "Ar Livre",       "icon": "🍃"},
            "event":     {"url": event_url,     "label": event_label,      "icon": "📅"},
            "attr":      {"url": attr_url,      "label": attr_label,       "icon": "🎟️"} # Item 'Passeios' genérico disponível
        }
