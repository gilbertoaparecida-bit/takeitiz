import time
import logging
import math
import numpy as np
import requests
import requests_cache
import unicodedata
from datetime import datetime
from geopy.geocoders import Nominatim

# --- CONFIGURAÇÃO ---
# Cache para evitar chamadas repetitivas nas APIs (dura 1 hora)
requests_cache.install_cache('takeitiz_cache', expire_after=3600)
logging.basicConfig(level=logging.INFO)

# --- 1. A ÂNCORA (GLOBAL BASELINE) ---
# Base: Madrid (100) - Gastos diários em Dólar para perfil Moderado
BASE_SPEND_USD_ANCHOR = {
    'food': 45.0, 'transport': 12.0, 'activities': 25.0, 'nightlife': 0.0, 'misc': 8.0
}

# --- 2. CONFIGURAÇÕES DE ESTILO E VIBE ---
class VibeConfig:
    MULTIPLIERS = {
        'tourist_mix': {'food': 1.0, 'transport': 1.0, 'activities': 1.0, 'nightlife': 0.5, 'misc': 1.0},
        'cultura':     {'food': 1.0, 'transport': 1.1, 'activities': 1.8, 'nightlife': 0.2, 'misc': 1.0},
        'gastro':      {'food': 1.8, 'transport': 0.8, 'activities': 0.5, 'nightlife': 0.6, 'misc': 1.2},
        'natureza':    {'food': 0.9, 'transport': 1.5, 'activities': 1.6, 'nightlife': 0.1, 'misc': 1.3},
        'festa':       {'food': 0.8, 'transport': 1.5, 'activities': 0.5, 'nightlife': 3.0, 'misc': 1.2},
        'familiar':    {'food': 1.2, 'transport': 1.4, 'activities': 1.1, 'nightlife': 0.0, 'misc': 1.5},
    }

class StyleConfig:
    SETTINGS = {
        'econômico': {'factor': 0.60, 'hotel_pct': 0.15},
        'moderado':  {'factor': 1.00, 'hotel_pct': 0.40}, 
        'conforto':  {'factor': 1.60, 'hotel_pct': 0.75},
        'luxo':      {'factor': 3.20, 'hotel_pct': 0.95},
    }

# --- 3. PROVEDOR DE CÂMBIO (COM BACKUP) ---
class FXProvider:
    def __init__(self):
        self.audit = []
        
    def _get_backup_rate(self, target_currency):
        """Consulta a AwesomeAPI (BC/Fechamento) se o Yahoo falhar."""
        try:
            # Mapeamento: BRL busca USD-BRL, EUR busca EUR-USD
            pair_map = {"BRL": "USD-BRL", "EUR": "EUR-USD"}
            pair = pair_map.get(target_currency)
            if not pair: return None
            
            url = f"https://economia.awesomeapi.com.br/last/{pair}"
            response = requests.get(url, timeout=3)
            data = response.json()
            
            key = pair.replace("-", "")
            if target_currency == "BRL":
                return float(data[key]['ask'])
            elif target_currency == "EUR":
                # Inverte pois a API dá EUR em USD, queremos USD em EUR
                return 1 / float(data[key]['ask'])
        except:
            return None

    def get_rate(self, target_currency):
        self.audit = []
        if target_currency == "USD": return 1.0
        
        # 1. Tenta Yahoo Finance (Tempo Real)
        try:
            import yfinance as yf
            if target_currency == "BRL":
                ticker = yf.Ticker("BRL=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    rate = hist['Close'].iloc[-1]
                    final = rate * 1.045 # Spread
                    self.audit.append({"src": "CÂMBIO", "msg": f"Cotação Yahoo (Live): R$ {final:.2f}", "status": "OK"})
                    return final
            elif target_currency == "EUR":
                ticker = yf.Ticker("EURUSD=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    rate = 1 / hist['Close'].iloc[-1]
                    self.audit.append({"src": "CÂMBIO", "msg": f"Cotação Yahoo (Live): € {rate:.2f}", "status": "OK"})
                    return rate
        except: pass

        # 2. Tenta Backup (AwesomeAPI)
        backup = self._get_backup_rate(target_currency)
        if backup:
            final = backup * 1.045 if target_currency == "BRL" else backup
            self.audit.append({"src": "CÂMBIO", "msg": f"⚠️ Yahoo instável. Usando Backup (BC): {final:.2f}", "status": "INFO"})
            return final

        # 3. Fallback Fixo (Emergência)
        fallback = {"BRL": 6.15, "EUR": 0.92}
        val = fallback.get(target_currency, 1.0)
        self.audit.append({"src": "CÂMBIO", "msg": f"⛔ APIs Offline. Usando taxa fixa: {val}", "status": "WARN"})
        return val

# --- 4. GEOLOCALIZAÇÃO E PERFIL CLIMÁTICO ---
class OnlineGeoLocator:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="takeitiz_app_v7_mobile")
        # Mapa auxiliar para inferir clima pelo país
        self.COUNTRY_PROFILE_MAP = {
            'br': 'sul_tropical', 'ar': 'sul_tropical', 'cl': 'sul_tropical', 'uy': 'sul_tropical',
            'au': 'sul_tropical', 'za': 'sul_tropical', 'nz': 'sul_tropical',
            'us': 'norte_temperado', 'ca': 'norte_temperado', 'gb': 'norte_temperado', 
            'fr': 'norte_temperado', 'es': 'norte_temperado', 'it': 'norte_temperado', 
            'pt': 'norte_temperado', 'de': 'norte_temperado',
            'th': 'inverno_fugitivo', 'ae': 'inverno_fugitivo', 'mx': 'inverno_fugitivo',
            'do': 'inverno_fugitivo', 'mv': 'inverno_fugitivo'
        }

    def identify_profile(self, city_name):
        try:
            location = self.geolocator.geocode(city_name, language='en', timeout=2)
            if location:
                address = location.raw.get('address', {})
                country = address.get('country_code', '').lower()
                state = address.get('state', '').lower()
                # Exceção Flórida
                if country == 'us' and 'florida' in state: return 'inverno_fugitivo', location.address
                return self.COUNTRY_PROFILE_MAP.get(country, 'padrao'), location.address
        except: return None, None
        return None, None

class GeoCostProvider:
    def __init__(self):
        self.audit = []
        self.online_locator = OnlineGeoLocator()
        
        # --- MATRIZ DE CALOR (Sazonalidade) ---
        # Índices 0 a 11 correspondem a Jan a Dez
        self.SEASONALITY_MATRIX = {
            'norte_temperado': [0.85, 0.85, 0.95, 1.10, 1.20, 1.40, 1.50, 1.50, 1.30, 1.10, 0.95, 1.30],
            'sul_tropical':    [1.50, 1.40, 1.10, 1.00, 0.90, 0.90, 1.30, 1.00, 1.05, 1.10, 1.20, 1.50],
            'inverno_fugitivo':[1.40, 1.40, 1.30, 1.20, 1.00, 0.90, 1.00, 0.85, 0.80, 0.85, 1.10, 1.50],
            'padrao':          [1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.1]
        }
        
        # --- MAPA MANUAL DE PERFIS (Correção de Bug Maragogi) ---
        self.MANUAL_PROFILE_MAP = {
            'brasil': 'sul_tropical', 'brazil': 'sul_tropical', 'maragogi': 'sul_tropical', 
            'noronha': 'sul_tropical', 'rio': 'sul_tropical', 'sp': 'sul_tropical', 'gramado': 'sul_tropical',
            'argentina': 'sul_tropical', 'chile': 'sul_tropical', 'australia': 'sul_tropical',
            'miami': 'inverno_fugitivo', 'orlando': 'inverno_fugitivo', 'cancun': 'inverno_fugitivo', 
            'dubai': 'inverno_fugitivo', 'thailand': 'inverno_fugitivo', 'tailandia': 'inverno_fugitivo',
            'europa': 'norte_temperado', 'usa': 'norte_temperado', 'canada': 'norte_temperado'
        }

        # --- BANCO DE DADOS UNIFICADO (Europa + Américas + Ásia + Brasil) ---
        self.RAW_INDICES = {
            # EUROPA
            "madrid": 100, "barcelona": 112, "sevilha": 95, "seville": 95, "valencia": 98,
            "lisboa": 95, "lisbon": 95, "porto": 88, "faro": 90, "paris": 160, "nice": 135,
            "londres": 175, "london": 175, "manchester": 135, "edimburgo": 150, "dublin": 155,
            "amsterda": 155, "amsterdam": 155, "bruxelas": 125, "berlim": 120, "munique": 150,
            "roma": 135, "rome": 135, "milao": 145, "veneza": 160, "florenca": 140,
            "zurique": 200, "zurich": 200, "genebra": 195, "viena": 145, "praga": 110,
            "atenas": 105, "santorini": 140, "istambul": 90, "moscou": 120,

            # AMERICAS
            "nova york": 190, "new york": 190, "nyc": 190, "los angeles": 160, "sao francisco": 185,
            "miami": 155, "orlando": 135, "las vegas": 145, "chicago": 150, "washington": 165,
            "honolulu": 200, "toronto": 160, "vancouver": 170, "cancun": 120, "tulum": 135,
            "cidade do mexico": 80, "havana": 75, "punta cana": 125, "buenos aires": 95,
            "bariloche": 120, "mendoza": 90, "santiago": 120, "san pedro de atacama": 135,
            "cartagena": 100, "bogota": 80, "cusco": 90, "lima": 85, "montevideo": 120,
            "punta del este": 145, "ushuaia": 125,

            # ASIA / AFRICA / OCEANIA
            "dubai": 140, "abu dhabi": 130, "doha": 150, "tel aviv": 175, "jerusalem": 150,
            "toquio": 150, "tokyo": 150, "osaka": 140, "seul": 140, "pequim": 115, "xangai": 130,
            "hong kong": 170, "bangkok": 80, "phuket": 105, "chiang mai": 70, "singapura": 160,
            "bali": 75, "jacarta": 80, "hanoi": 70, "ho chi minh": 75, "maldivas": 185, "male": 185,
            "nova delhi": 70, "mumbai": 85, "cidade do cabo": 95, "marraquexe": 85, "cairo": 80,
            "seychelles": 170, "sidney": 160, "sydney": 160, "melbourne": 150, "auckland": 150,
            "papeete": 175, "bora bora": 180,

            # BRASIL (DESTAQUES DO ARQUIVO COMPLETO)
            "fernando de noronha": 170, "noronha": 170, "trancoso": 150, "buzios": 140,
            "jurere": 135, "sao miguel dos milagres": 135, "angra dos reis": 130,
            "campos do jordao": 130, "gramado": 125, "maragogi": 125, "itacare": 125,
            "praia do forte": 125, "rio de janeiro": 110, "rio": 110, "sao paulo": 105,
            "sp": 105, "brasilia": 105, "florianopolis": 105, "recife": 90, "salvador": 90,
            "fortaleza": 90, "manaus": 85, "foz do iguacu": 80, "ouro preto": 95,
            "tiradentes": 105, "bonito": 110, "jalapao": 100, "lencois maranhenses": 105,
            "pipa": 115, "jericoacoara": 110, "capitolio": 95, "porto seguro": 120,
            "arraial d ajuda": 135, "caraiva": 140, "morro de sao paulo": 130,
            "ilhabela": 120, "paraty": 115, "petropolis": 115, "visconde de maua": 115,
            "alter do chao": 95, "chapada dos veadeiros": 95, "pirenopolis": 95,
            "ubatuba": 110, "maresias": 125, "juquehy": 130, "monte verde": 115,
            "balneario camboriu": 120, "bombinhas": 120, "canela": 120
        }

    def _normalize(self, text):
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower().strip()

    def get_index_and_profile(self, destination):
        dest_clean = self._normalize(destination)
        idx = 100
        profile = 'padrao'
        found_idx = False
        found_profile = False

        # 1. Busca Índice (Local)
        for city, val in self.RAW_INDICES.items():
            if self._normalize(city) in dest_clean:
                idx = val
                found_idx = True
                self.audit.append({"src": "LOCAL", "msg": f"Custo local: {city.title()} (Índice {idx})", "status": "OK"})
                break
        
        # 2. Busca Perfil Climático (Manual - Prioridade)
        for key, prof in self.MANUAL_PROFILE_MAP.items():
            if key in dest_clean:
                profile = prof
                found_profile = True
                self.audit.append({"src": "SISTEMA", "msg": f"Perfil Climático (Manual): {prof.upper()}", "status": "OK"})
                break
        
        # 3. Busca Perfil Climático (Web - Fallback)
        if not found_profile:
            self.audit.append({"src": "WEB", "msg": "Consultando satélite para clima...", "status": "INFO"})
            prof, _ = self.online_locator.identify_profile(destination)
            if prof:
                profile = prof
                self.audit.append({"src": "WEB", "msg": f"Perfil Climático (Web): {prof.upper()}", "status": "OK"})

        # Fallback Final Brasil
        if not found_idx and not found_profile and 'brasil' in dest_clean:
             idx = 85
             profile = 'sul_tropical'

        return idx, profile

# --- 5. PREÇO DE HOTELARIA (Curva Exponencial) ---
class AccommodationProvider:
    def __init__(self):
        self.audit = []
    def estimate_adr(self, price_index, style_pct):
        BASE_HOTEL_USD = 120.0
        city_factor = price_index / 100.0
        style_factor = np.exp(1.6 * (style_pct - 0.45))
        return BASE_HOTEL_USD * city_factor * style_factor

# --- 6. MOTOR PRINCIPAL ---
class CostEngine:
    def __init__(self):
        self.fx = FXProvider()
        self.geo = GeoCostProvider()
        self.hotel = AccommodationProvider()
        self.audit_log = []

    def calculate_cost(self, destination, days, travelers, style, currency, vibe="tourist_mix", start_date=None):
        self.audit_log = []
        
        # 1. Câmbio (com Failover)
        usd_rate = self.fx.get_rate(currency)
        self.audit_log.extend(self.fx.audit)
        
        # 2. Geografia e Clima
        idx, profile = self.geo.get_index_and_profile(destination)
        self.audit_log.extend(self.geo.audit)
        
        # 3. Sazonalidade (Matriz)
        season_factor = 1.0
        if start_date:
            month_idx = start_date.month - 1
            matrix = self.geo.SEASONALITY_MATRIX.get(profile, self.geo.SEASONALITY_MATRIX['padrao'])
            season_factor = matrix[month_idx]
            
            pct = int((season_factor - 1) * 100)
            sign = "+" if pct > 0 else ""
            self.audit_log.append({"src": "DATA", "msg": f"Sazonalidade ({start_date.strftime('%B')}) [{profile}]: {sign}{pct}%", "status": "INFO"})

        # 4. Cálculo Final
        style_cfg = StyleConfig.SETTINGS.get(style.lower(), StyleConfig.SETTINGS['moderado'])
        vibe_mult = VibeConfig.MULTIPLIERS.get(vibe.lower(), VibeConfig.MULTIPLIERS['tourist_mix'])
        
        breakdown_usd = {}
        daily_life_usd = 0
        
        for cat, base in BASE_SPEND_USD_ANCHOR.items():
            # Sazonalidade afeta 50% do lifestyle
            life_season = 1 + (season_factor - 1) * 0.5
            val = base * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat] * life_season
            breakdown_usd[cat] = val
            daily_life_usd += val
            
        rooms = math.ceil(travelers / 2)
        # Sazonalidade afeta 100% do hotel
        adr_usd = self.hotel.estimate_adr(idx, style_cfg['hotel_pct']) * season_factor
        
        total_hotel = adr_usd * rooms * days
        total_life = daily_life_usd * travelers * days
        final = (total_hotel + total_life) * usd_rate
        
        return {
            "total": final,
            "daily_avg": (final / days) / travelers,
            "range": [final * 0.85, final * 1.15],
            "breakdown": {
                'lodging': total_hotel * usd_rate,
                'food': breakdown_usd['food'] * travelers * days * usd_rate,
                'transport': breakdown_usd['transport'] * travelers * days * usd_rate,
                'activities': (breakdown_usd['activities'] + breakdown_usd['nightlife']) * travelers * days * usd_rate,
                'misc': breakdown_usd['misc'] * travelers * days * usd_rate
            },
            "audit": self.audit_log
        }

engine = CostEngine()
