import urllib.parse
from datetime import timedelta

class AmenitiesGenerator:
    def __init__(self):
        # 1. Mapeamento de Termos de Busca (O que o Google busca)
        self.VIBE_MAP = {
            'tourist_mix': "top attractions",
            'cultura': "museums and historical sites",
            'gastro': "best restaurants and food tours",
            'natureza': "parks hiking and nature",
            'festa': "nightlife bars and clubs",
            'familiar': "family friendly activities"
        }

        # 2. Mapeamento de Rótulos Dinâmicos (O que o usuário vê no botão)
        self.LABEL_MAP = {
            'tourist_mix': {'food': 'Gastronomia', 'event': 'Agenda Cultural', 'attr': 'Principais Atrações'},
            'cultura':     {'food': 'Cafés & Bistrôs', 'event': 'Exposições & Arte', 'attr': 'Museus & História'},
            'gastro':      {'food': 'Melhores Mesas', 'event': 'Degustações', 'attr': 'Mercados Locais'},
            'natureza':    {'food': 'Comer c/ Vista', 'event': 'Ar Livre', 'attr': 'Parques & Trilhas'},
            'festa':       {'food': 'Bares & Drinks', 'event': 'Festas & Shows', 'attr': 'Vida Noturna'},
            'familiar':    {'food': 'Comer em Família', 'event': 'Teatro & Lazer', 'attr': 'Diversão Kids'}
        }

        # 3. Mapeamento de Ordenação do Booking (Otimização de Estilo)
        self.BOOKING_ORDER = {
            'econômico': 'price',                   # Menor preço primeiro
            'moderado': 'review_score_and_price',   # Custo-benefício
            'conforto': 'bayesian_review_score',    # Melhores avaliações
            'luxo': 'class_descending'              # Estrelas (5->1)
        }

    def _clean(self, text):
        return urllib.parse.quote_plus(text)

    def generate_links(self, destination, vibe, style, start_date=None, days=0):
        """
        Gera links profundos com:
        - Rótulos dinâmicos baseados na Vibe.
        - Filtro de preço/estrelas no Booking baseado no Estilo.
        - Injeção de datas.
        """
        
        # A. Preparar Datas e Parâmetros
        date_params = ""
        date_str = "" 
        
        if start_date:
            # Texto para Google Agenda (Ex: Janeiro 2026)
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            try:
                date_str = f"{meses[start_date.month-1]} {start_date.year}"
            except:
                date_str = ""

            # Datas para Booking (Checkin/Checkout)
            if days > 0:
                end_date = start_date + timedelta(days=days)
                date_params = f"&checkin={start_date}&checkout={end_date}"
            
        # B. Definir Ordenação do Booking pelo Estilo
        order_param = self.BOOKING_ORDER.get(style, 'review_score_and_price')

        # C. Definir Rótulos pela Vibe (Fallback para tourist_mix)
        labels = self.LABEL_MAP.get(vibe, self.LABEL_MAP['tourist_mix'])

        # --- GERAÇÃO DOS LINKS ---

        # 1. VOOS (Google Flights)
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        # 2. HOSPEDAGEM (Booking Otimizado)
        # Injeta datas e a ordenação correta (order=...)
        hotel_url = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}{date_params}&order={order_param}"
        
        # 3. GASTRONOMIA (Google Maps)
        food_url = f"https://www.google.com/maps/search/{self._clean(destination + ' restaurantes ' + style)}"
        
        # 4. AGENDA (Google Search com Data)
        event_url = f"https://www.google.com/search?q=agenda+cultural+eventos+{self._clean(destination)}+{self._clean(date_str)}"
        
        # 5. PASSEIOS (TripAdvisor)
        attr_term = self.VIBE_MAP.get(vibe, "things to do")
        attr_url = f"https://www.tripadvisor.com.br/Search?q={self._clean(destination + ' ' + attr_term)}"
        
        # 6. SEGURO (Google Search)
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
                "food": labels['food'],   # Dinâmico
                "event": labels['event'], # Dinâmico
                "attr": labels['attr'],   # Dinâmico
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
