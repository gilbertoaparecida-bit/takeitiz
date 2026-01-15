import urllib.parse
from datetime import timedelta
import config # <--- IMPORTANDO O PAINEL

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
            'business': "almoço executivo ambiente tranquilo" 
        }

        # 4. Ordenação Booking (Preservando Handover de Estilo)
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
        Gera links monetizados (Booking, Viator) se os IDs estiverem no config.py.
        Mantém o handover completo de Datas, Destino e Vibe.
        """
        
        # Sanitização
        style_key = style.lower()
        if "super" in style_key: style_key = "super_luxo"
        elif "econ" in style_key: style_key = "econômico"
        
        vibe_key = vibe if vibe in self.VIBE_FOOD_TERMS else 'tourist_mix' 

        # A. Datas (Essencial para o handover)
        date_params_bk = "" # Para Booking
        date_str = ""       # Para Google
        if start_date:
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            try: date_str = f"{meses[start_date.month-1]} {start_date.year}"
            except: pass
            if days > 0:
                end_date = start_date + timedelta(days=days)
                # Booking usa formato YYYY-MM-DD
                date_params_bk = f"&checkin={start_date}&checkout={end_date}"

        # --- GERAÇÃO DOS LINKS ---

        # 1. VOOS (Mantemos Google Search para melhor UX sem origem)
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        # 2. HOTEL (Booking Monetizado)
        booking_order = self.BOOKING_ORDER.get(style_key, 'review_score_and_price')
        hotel_base = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}{date_params_bk}&order={booking_order}"
        
        if config.BOOKING_AID:
            hotel_url = f"{hotel_base}&aid={config.BOOKING_AID}"
        else:
            hotel_url = hotel_base
        
        # 3. GASTRONOMIA (Google Maps - Sem afiliação direta, foco em utilidade)
        food_style = self.STYLE_TERMS.get(style_key, "Restaurantes")
        food_vibe = self.VIBE_FOOD_TERMS.get(vibe_key, "")
        food_query = f"{food_style} em {destination} {food_vibe}"
        food_url = f"https://www.google.com/maps/search/{self._clean(food_query)}"
        
        food_label = "Gastronomia"
        if vibe_key == 'business': food_label = "Almoço Executivo"
        
        # 4. SEGURO (Seguros Promo ou Google)
        if config.SEGUROS_PROMO_CODE:
            # Envia para a home com o cookie de afiliado (UX segura)
            insurance_url = f"https://www.segurospromo.com.br/?promo={config.SEGUROS_PROMO_CODE}"
        else:
            insurance_url = "https://www.google.com/search?q=seguro+viagem+cotacao"

        # 5. VARIÁVEIS (Concierge com Viator Monetizado)
        
        # Função auxiliar para gerar link Viator ou Google (Fallback)
        def get_activity_link(query_text, google_fallback_query):
            if config.VIATOR_PID:
                # Busca deep link na Viator com os parâmetros de afiliado
                base = f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' ' + query_text)}"
                return f"{base}&pid={config.VIATOR_PID}&aid={config.VIATOR_AID if hasattr(config, 'VIATOR_AID') else ''}&subId={config.VIATOR_SUBID}"
            else:
                return f"https://www.viator.com/searchResults/all?text={self._clean(destination + ' ' + query_text)}"

        # Compras (Mantém Google Maps)
        shop_term = self.SHOPPING_TERMS.get(style_key, "Shopping")
        shop_url = f"https://www.google.com/maps/search/{self._clean(shop_term + ' em ' + destination)}"

        # Vida Noturna
        night_url = get_activity_link("nightlife pub crawl", "nightlife")

        # Arte & Cultura
        cult_url = get_activity_link("museum tickets historical tours", "museums")

        # Natureza
        nature_url = get_activity_link("outdoor activities parks hiking", "parks")
        
        # Agenda / Feiras (Mantém Google Search)
        event_query = "agenda cultural eventos"
        if vibe_key == 'business': event_query = "feiras de negocios congressos expo"
        event_url = f"https://www.google.com/search?q={self._clean(event_query)}+{self._clean(destination)}+{self._clean(date_str)}"
        event_label = "Agenda Local"
        if vibe_key == 'business': event_label = "Feiras & Expo"

        # Attr (Passeios ou Coworking)
        attr_label = "Principais Atrações"
        if vibe_key == 'business':
            # Se for Business, linka para Google Maps "Coworking" (Utilidade)
            attr_label = "Coworking & Cafés"
            attr_url = f"https://www.google.com/maps/search/{self._clean('Coworking cafes com wifi em ' + destination)}"
        else:
            # Se for Lazer, linka para Viator (Monetizado)
            attr_url = get_activity_link("top attractions skip the line", "attractions")

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
            "attr":      {"url": attr_url,      "label": attr_label,       "icon": "🎟️"} 
        }
