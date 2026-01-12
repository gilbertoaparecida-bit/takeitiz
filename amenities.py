import urllib.parse

class AmenitiesGenerator:
    """
    Gera links profundos (Deep Links) para Google Maps e Search.
    Sintaxe de busca: Otimizada pelo Perfil.
    Labels visuais: Elegantes e Neutros (Sem expor o perfil de gasto).
    """
    
    def __init__(self):
        # Mapeamento: Vibe -> Keywords de Busca
        self.VIBE_MAP = {
            'tourist_mix': {
                'food': "best traditional restaurants",
                'attr': "must see tourist attractions",
                'hidden': "hidden gems architecture",
                'event': "events"
            },
            'cultura': {
                'food': "historic cafes and bistros",
                'attr': "museums art galleries historical sites",
                'hidden': "underrated museums",
                'event': "art exhibitions theater classical music"
            },
            'gastro': {
                'food': "top rated gastronomy tasting menu",
                'attr': "food markets gourmet shops",
                'hidden': "best street food locals love",
                'event': "food festivals wine tasting"
            },
            'natureza': {
                'food': "restaurants with a view garden",
                'attr': "parks hiking trails nature reserves",
                'hidden': "secret sunset spots viewpoints",
                'event': "outdoor activities"
            },
            'festa': {
                'food': "late night food cocktail bars",
                'attr': "popular districts nightlife",
                'hidden': "underground speakeasy bars",
                'event': "concerts dj sets parties nightlife"
            },
            'familiar': {
                'food': "family friendly restaurants with play area",
                'attr': "kids activities parks theme parks",
                'hidden': "picnic spots playgrounds",
                'event': "family workshops kids events"
            }
        }
        
        # Refinamento por Estilo (Usado APENAS na busca, não no texto)
        self.STYLE_MODIFIERS = {
            'econômico': "cheap eats budget friendly free entry",
            'moderado': "best value rated",
            'conforto': "high end comfortable",
            'luxo': "luxury fine dining exclusive vip"
        }

    def _clean_url(self, query):
        return urllib.parse.quote_plus(query)

    def generate_links(self, destination, vibe, style, start_date=None):
        """Retorna links com Labels Higienizados (Sem 'Econômico' no texto)"""
        
        vibe_key = vibe if vibe in self.VIBE_MAP else 'tourist_mix'
        style_key = style if style in self.STYLE_MODIFIERS else 'moderado'
        
        keywords = self.VIBE_MAP[vibe_key]
        style_mod = self.STYLE_MODIFIERS[style_key]
        
        # 1. FOOD
        q_food = f"{style_mod} {destination} {keywords['food']}"
        url_food = f"https://www.google.com/maps/search/{self._clean_url(q_food)}"
        
        # 2. EVENTS
        date_str = ""
        display_date = "Agenda Local"
        if start_date:
            date_str = start_date.strftime("%B %Y")
            display_date = f"Agenda {start_date.strftime('%b/%Y')}" # Ex: Jun/2026
            
        q_event = f"{keywords['event']} in {destination} {date_str}"
        url_event = f"https://www.google.com/search?q={self._clean_url(q_event)}"
        
        # 3. ATTRACTIONS (MAPA)
        q_attr = f"top {keywords['attr']} in {destination} {style_mod}"
        url_attr = f"https://www.google.com/maps/search/{self._clean_url(q_attr)}"
        
        # 4. SURPRISE ME
        q_surprise = f"best {keywords['hidden']} in {destination} blog review"
        url_surprise = f"https://www.google.com/search?q={self._clean_url(q_surprise)}"
        
        return {
            "food": url_food,
            "event": url_event,
            "attr": url_attr,
            "surprise": url_surprise,
            "labels": {
                # TEXTOS NEUTROS E ELEGANTES
                "food_label": "Gastronomia Local", 
                "event_label": "Agenda Cultural",
                "surprise_label": "Surpreenda-se"
            }
        }
