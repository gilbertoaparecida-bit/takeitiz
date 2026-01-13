import urllib.parse

class AmenitiesGenerator:
    """
    Gera links profundos (Deep Links) otimizados para brasileiros.
    Inclui Voos, Hotéis, Gastronomia e Lazer.
    """
    
    def __init__(self):
        # Mapeamento de Vibe -> Palavras-chave de busca
        self.VIBE_MAP = {
            'tourist_mix': {
                'food': "melhores restaurantes tradicionais",
                'attr': "principais pontos turísticos",
                'hidden': "lugares incríveis pouco conhecidos",
                'event': "eventos e shows"
            },
            'cultura': {
                'food': "cafés históricos e bistrôs charmosos",
                'attr': "museus centros culturais igrejas históricas",
                'hidden': "museus pouco conhecidos e arquitetura",
                'event': "exposições teatro música clássica agenda cultural"
            },
            'gastro': {
                'food': "melhores restaurantes gastronomia premiada",
                'attr': "mercados municipais feiras gastronômicas",
                'hidden': "comida de rua famosa onde os locais comem",
                'event': "festivais gastronômicos degustação de vinhos"
            },
            'natureza': {
                'food': "restaurantes com vista panorâmica natureza",
                'attr': "melhores trilhas cachoeiras e parques",
                'hidden': "mirantes escondidos pôr do sol",
                'event': "passeios ecológicos atividades ao ar livre"
            },
            'festa': {
                'food': "bares com petiscos e drinks",
                'attr': "vida noturna rua dos bares",
                'hidden': "bares secretos speakeasy",
                'event': "melhores baladas shows festas hoje"
            },
            'familiar': {
                'food': "restaurantes com espaço kids",
                'attr': "parques para crianças passeios em família",
                'hidden': "lugares tranquilos para piquenique",
                'event': "oficinas infantis teatro infantil"
            }
        }
        
        self.STYLE_MODIFIERS = {
            'econômico': "barato bom e barato entrada gratuita",
            'moderado': "melhor custo benefício bem avaliado",
            'conforto': "confortável charmoso",
            'luxo': "luxo sofisticado exclusivo vip"
        }
        
        self.HOTEL_MODIFIERS = {
            'econômico': "hostels baratos e pousadas econômicas",
            'moderado': "melhores hotéis 3 estrelas e pousadas bem avaliadas",
            'conforto': "hotéis boutique e pousadas de charme",
            'luxo': "resorts de luxo hotéis 5 estrelas e pousadas exclusivas"
        }

    def _clean_url(self, query):
        return urllib.parse.quote_plus(query)

    def generate_links(self, destination, vibe, style, start_date=None):
        
        vibe_key = vibe if vibe in self.VIBE_MAP else 'tourist_mix'
        style_key = style if style in self.STYLE_MODIFIERS else 'moderado'
        
        keywords = self.VIBE_MAP[vibe_key]
        style_mod = self.STYLE_MODIFIERS[style_key]
        hotel_mod = self.HOTEL_MODIFIERS.get(style_key, "melhores hotéis e pousadas")
        
        # Data Formatada para melhorar busca de eventos
        date_str = ""
        if start_date:
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_nome = meses[start_date.month - 1]
            date_str = f"{mes_nome} {start_date.year}"
        
        # 1. VOOS
        q_flight = f"passagens aéreas para {destination} promoções"
        url_flight = f"https://www.google.com/search?q={self._clean_url(q_flight)}"

        # 2. HOTEL
        q_hotel = f"{hotel_mod} em {destination}"
        url_hotel = f"https://www.google.com/search?q={self._clean_url(q_hotel)}"

        # 3. FOOD
        q_food = f"{destination} {keywords['food']} {style_mod}"
        url_food = f"https://www.google.com/maps/search/{self._clean_url(q_food)}"
        
        # 4. EVENTS
        q_event = f"{keywords['event']} em {destination} {date_str}"
        url_event = f"https://www.google.com/search?q={self._clean_url(q_event)}"
        
        # 5. ATTRACTIONS (MAPA)
        q_attr = f"top {keywords['attr']} em {destination}"
        url_attr = f"https://www.google.com/maps/search/{self._clean_url(q_attr)}"
        
        # 6. SURPRISE ME
        q_surprise = f"dicas exclusivas o que fazer em {destination} blog viagem"
        url_surprise = f"https://www.google.com/search?q={self._clean_url(q_surprise)}"
        
        return {
            "flight": url_flight,
            "hotel": url_hotel,
            "food": url_food,
            "event": url_event,
            "attr": url_attr,
            "surprise": url_surprise,
            "labels": {
                "flight_label": "Passagens",
                "hotel_label": "Hospedagem",
                "food_label": "Gastronomia", 
                "event_label": "Agenda",
                "surprise_label": "Surpreenda-se"
            }
        }
