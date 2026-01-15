import urllib.parse
from datetime import timedelta

class AmenitiesGenerator:
    def __init__(self):
        # 1. Rótulos Dinâmicos (Camaleão)
        self.LABEL_MAP = {
            'tourist_mix': {'food': 'Gastronomia', 'event': 'Agenda Cultural', 'attr': 'Principais Atrações'},
            'cultura':     {'food': 'Cafés & Bistrôs', 'event': 'Exposições & Arte', 'attr': 'Museus & História'},
            'gastro':      {'food': 'Melhores Mesas', 'event': 'Degustações', 'attr': 'Mercados Locais'},
            'natureza':    {'food': 'Comer c/ Vista', 'event': 'Ar Livre', 'attr': 'Parques & Trilhas'},
            'festa':       {'food': 'Bares & Drinks', 'event': 'Festas & Shows', 'attr': 'Vida Noturna'},
            'familiar':    {'food': 'Comer em Família', 'event': 'Teatro & Lazer', 'attr': 'Diversão Kids'}
        }

        # 2. Termos para Busca no Google Maps (Sintaxe Limpa)
        self.STYLE_TERMS = {
            'econômico': "Restaurantes baratos",
            'moderado': "Restaurantes bem avaliados",
            'conforto': "Restaurantes charmosos",
            'luxo': "Restaurantes Michelin",
            'super_luxo': "Fine dining awards"
        }
        
        self.VIBE_FOOD_TERMS = {
            'gastro': "menu degustação",
            'festa': "animados com drinks",
            'romântico': "ambiente íntimo",
            'familiar': "com espaço kids",
            'natureza': "com vista",
            'cultura': "tradicionais"
        }

        # 3. Termos para Busca no Viator (Experiências Pagas)
        self.VIATOR_TERMS = {
            'tourist_mix': "Attractions skip the line",
            'cultura': "Museum tickets historical tours",
            'gastro': "Food tours wine tasting",
            'natureza': "Outdoor activities hiking tours",
            'festa': "Pub crawl nightlife experience", # O Pulo do Gato para monetizar festa
            'familiar': "Family friendly activities parks"
        }

        # 4. Ordenação Booking (Filtro Inteligente)
        self.BOOKING_ORDER = {
            'econômico': 'price',
            'moderado': 'review_score_and_price',
            'conforto': 'bayesian_review_score',
            'luxo': 'class_descending',
            'super_luxo': 'class_descending' # E confiar nos preços altos
        }

    def _clean(self, text):
        return urllib.parse.quote_plus(text)

    def generate_links(self, destination, vibe, style, start_date=None, days=0):
        
        # Sanitização de chaves
        vibe_key = vibe if vibe in self.LABEL_MAP else 'tourist_mix'
        style_key = style.lower()
        if "super" in style_key: style_key = "super_luxo"
        elif "econ" in style_key: style_key = "econômico"

        # A. Preparar Datas
        date_params = ""
        date_str = ""
        if start_date:
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            try: date_str = f"{meses[start_date.month-1]} {start_date.year}"
            except: pass
            if days > 0:
                end_date = start_date + timedelta(days=days)
                date_params = f"&checkin={start_date}&checkout={end_date}"

        # B. Parâmetros de Busca Otimizados
        booking_order = self.BOOKING_ORDER.get(style_key, 'review_score_and_price')
        labels = self.LABEL_MAP.get(vibe_key, self.LABEL_MAP['tourist_mix'])
        
        # Sintaxe Gastronômica Limpa: "Restaurantes Michelin em Paris menu degustação"
        style_term = self.STYLE_TERMS.get(style_key, "Restaurantes")
        vibe_term = self.VIBE_FOOD_TERMS.get(vibe_key, "")
        food_query = f"{style_term} em {destination} {vibe_term}"

        # Viator Keyword
        viator_kw = self.VIATOR_TERMS.get(vibe_key, "Top things to do")

        # --- GERAÇÃO DE LINKS ---

        # 1. VOOS
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        # 2. HOSPEDAGEM (Booking com Filtro)
        hotel_url = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}{date_params}&order={booking_order}"
        
        # 3. GASTRONOMIA (Google Maps Limpo)
        food_url = f"https://www.google.com/maps/search/{self._clean(food_query)}"
        
        # 4. AGENDA
        event_url = f"https://www.google.com/search?q=agenda+cultural+eventos+{self._clean(destination)}+{self._clean(date_str)}"
        
        # 5. PASSEIOS (MIGRAÇÃO PARA VIATOR)
        # Busca transacional, ignora GPS de Varginha
        attr_url = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' ' + viator_kw)}"
        
        # 6. SEGURO
        insurance_url = "https://www.google.com/search?q=seguro+viagem+cotacao"

        return {
            "links": {
                "flight": flight_url,
                "hotel": hotel_url,
                "food": food_url,
                "event": event_url,
                "attr": attr_url,
                "insurance": insurance_url
            },
            "labels": {
                "flight": "Monitorar Voos",
                "hotel": "Ver Hotéis",
                "food": labels['food'],
                "event": labels['event'],
                "attr": labels['attr'],
                "insurance": "Seguro Viagem"
            },
            "icons": {
                "flight": "✈️",
                "hotel": "🏨",
                "food": "🍽️",
                "event": "📅",
                "attr": "ticket", 
                "insurance": "🛡️"
            }
        }
