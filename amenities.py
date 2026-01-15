import urllib.parse

class AmenitiesGenerator:
    def __init__(self):
        # Mapeamento de Vibe para termos de busca otimizados
        self.VIBE_MAP = {
            'tourist_mix': "top attractions",
            'cultura': "museums and historical sites",
            'gastro': "best restaurants and food tours",
            'natureza': "parks hiking and nature",
            'festa': "nightlife bars and clubs",
            'familiar': "family friendly activities"
        }

    def _clean(self, text):
        return urllib.parse.quote_plus(text)

    def generate_links(self, destination, vibe, style, start_date=None):
        """
        Gera links direcionados para parceiros ou buscas inteligentes.
        Estrutura otimizada para monetização futura (Affiliate Ready).
        """
        
        # 1. VOOS -> Skyscanner / Google Flights
        # Link genérico de busca, fácil de virar afiliado depois.
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        # 2. HOSPEDAGEM -> Booking / Hoteis.com
        # Busca direta por hotéis na região
        hotel_url = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}"
        
        # 3. ATRAÇÕES -> TripAdvisor / Viator
        attr_term = self.VIBE_MAP.get(vibe, "things to do")
        attr_url = f"https://www.tripadvisor.com.br/Search?q={self._clean(destination + ' ' + attr_term)}"
        
        # 4. SEGURO VIAGEM (Novo Item de Receita)
        insurance_url = "https://www.google.com/search?q=seguro+viagem+cotacao"

        return {
            "links": {
                "flight": flight_url,
                "hotel": hotel_url,
                "attr": attr_url,
                "insurance": insurance_url
            },
            "labels": {
                "flight": "Monitorar Voos", # Copy mais "Curadoria"
                "hotel": "Ver Hotéis",
                "attr": "Passeios",
                "insurance": "Seguro Viagem"
            },
            "icons": {
                "flight": "✈️",
                "hotel": "🏨",
                "attr": "🎟️",
                "insurance": "🛡️"
            }
        }
