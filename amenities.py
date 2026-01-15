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

    def generate_links(self, destination, vibe, style, start_date=None, days=0):
        """
        Gera links com datas injetadas (Booking) e restaura os 6 botões.
        """
        
        # 1. Preparar Datas para URL (Formato YYYY-MM-DD)
        date_params = ""
        if start_date and days > 0:
            from datetime import timedelta
            end_date = start_date + timedelta(days=days)
            # Parâmetros padrão do Booking.com
            date_params = f"&checkin={start_date}&checkout={end_date}"
            
        # 2. VOOS (Skyscanner / Google)
        flight_url = f"https://www.google.com/search?q=passagens+aereas+para+{self._clean(destination)}"
        
        # 3. HOSPEDAGEM (Booking com DATAS)
        # Injeta o checkin/checkout na URL
        hotel_url = f"https://www.booking.com/searchresults.pt-br.html?ss={self._clean(destination)}{date_params}"
        
        # 4. GASTRONOMIA (Restaurado)
        food_url = f"https://www.google.com/maps/search/{self._clean(destination + ' restaurantes ' + style)}"
        
        # 5. AGENDA (Restaurado)
        # Tenta colocar o mês/ano na busca se houver data
        date_str = ""
        if start_date:
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            date_str = f"{meses[start_date.month-1]} {start_date.year}"
            
        event_url = f"https://www.google.com/search?q=agenda+cultural+eventos+{self._clean(destination)}+{self._clean(date_str)}"
        
        # 6. PASSEIOS (TripAdvisor)
        attr_term = self.VIBE_MAP.get(vibe, "things to do")
        attr_url = f"https://www.tripadvisor.com.br/Search?q={self._clean(destination + ' ' + attr_term)}"
        
        # 7. SEGURO (Novo)
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
                "food": "Gastronomia",
                "event": "Agenda Cultural",
                "attr": "Passeios",
                "insurance": "Seguro Viagem"
            },
            "icons": {
                "flight": "✈️",
                "hotel": "🏨",
                "food": "🍽️",
                "event": "📅",
                "attr": "ticket", # Usando emoji direto no app.py ou map
                "insurance": "🛡️"
            }
        }
