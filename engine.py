import time
import logging
import math
import numpy as np
import requests_cache
import unicodedata
from datetime import datetime
from geopy.geocoders import Nominatim

# --- CONFIGURAÇÃO ---
requests_cache.install_cache('takeitiz_cache', expire_after=3600)
logging.basicConfig(level=logging.INFO)

# --- 1. A ÂNCORA (GLOBAL BASELINE) ---
BASE_SPEND_USD_ANCHOR = {
    'food': 45.0, 'transport': 12.0, 'activities': 25.0, 'nightlife': 0.0, 'misc': 8.0
}

# --- 2. CONFIGURAÇÕES ---
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

# --- 3. PROVEDORES ---
class FXProvider:
    def __init__(self):
        self.audit = []
    def get_rate(self, target_currency):
        if target_currency == "USD": return 1.0
        try:
            import yfinance as yf
            if target_currency == "BRL":
                ticker = yf.Ticker("BRL=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    rate = hist['Close'].iloc[-1]
                    final_rate = rate * 1.045 # Spread
                    self.audit.append({"src": "CÂMBIO", "msg": f"Cotação Dólar Turismo aplicada: R$ {final_rate:.2f}", "status": "OK"})
                    return final_rate
            elif target_currency == "EUR":
                ticker = yf.Ticker("EURUSD=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    eur_usd = hist['Close'].iloc[-1]
                    rate = 1 / eur_usd
                    self.audit.append({"src": "CÂMBIO", "msg": f"Conversão Euro/Dólar atualizada: € 1,00 = U$ {eur_usd:.2f}", "status": "OK"})
                    return rate
        except: pass
        fallback = {"BRL": 6.15, "EUR": 0.92}
        val = fallback.get(target_currency, 1.0)
        self.audit.append({"src": "CÂMBIO", "msg": f"Usando taxa de referência padrão: {val}", "status": "WARN"})
        return val

class OnlineGeoLocator:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="takeitiz_app_v5_matrix")
        
        # Mapeamento para Perfis Climáticos (Zoneamento)
        # 1: Norte Temperado (Europa/EUA)
        # 2: Sul Tropical (Brasil/Oceania)
        # 3: Inverno Fugitivo/Seca (Caribe/Sudeste Asiático/Dubai)
        self.COUNTRY_PROFILE_MAP = {
            'br': 'sul_tropical', 'ar': 'sul_tropical', 'cl': 'sul_tropical', 'au': 'sul_tropical', 'za': 'sul_tropical',
            'us': 'norte_temperado', 'ca': 'norte_temperado', 'gb': 'norte_temperado', 'fr': 'norte_temperado', 
            'it': 'norte_temperado', 'es': 'norte_temperado', 'pt': 'norte_temperado', 'de': 'norte_temperado',
            'th': 'inverno_fugitivo', 'id': 'inverno_fugitivo', 'ae': 'inverno_fugitivo', 'mx': 'inverno_fugitivo', 
            'do': 'inverno_fugitivo', 'mv': 'inverno_fugitivo'
        }

    def identify_profile(self, city_name):
        try:
            location = self.geolocator.geocode(city_name, language='en', timeout=2)
            if location:
                address = location.raw.get('address', {})
                country_code = address.get('country_code', '').lower()
                
                # Regras de Exceção (Estados Específicos)
                state = address.get('state', '').lower()
                
                # Flórida (EUA) não é Norte Temperado, é Inverno Fugitivo (Caribe)
                if country_code == 'us' and 'florida' in state:
                    return 'inverno_fugitivo', location.address
                
                return self.COUNTRY_PROFILE_MAP.get(country_code, 'padrao'), location.address
        except:
            return 'padrao', None
        return 'padrao', None

class GeoCostProvider:
    def __init__(self):
        self.audit = []
        self.online_locator = OnlineGeoLocator()
        
        # --- MATRIZ DE CALOR MENSAL (Index 0 = Janeiro, 11 = Dezembro) ---
        self.SEASONALITY_MATRIX = {
            # Pico: Jun-Ago (Verão). Vale: Jan-Fev (Inverno).
            'norte_temperado': [0.85, 0.85, 0.95, 1.10, 1.20, 1.40, 1.50, 1.50, 1.30, 1.10, 0.95, 1.30],
            
            # Pico: Dez-Fev (Verão) + Jul (Férias). Vale: Mai-Jun (Chuva/Outono).
            'sul_tropical':    [1.50, 1.40, 1.10, 1.00, 0.90, 0.90, 1.30, 1.00, 1.05, 1.10, 1.20, 1.50],
            
            # Pico: Jan-Abr (Seca/Fuga do frio). Vale: Ago-Out (Furacão/Monção).
            'inverno_fugitivo':[1.40, 1.40, 1.30, 1.20, 1.00, 0.90, 1.00, 0.85, 0.80, 0.85, 1.10, 1.50],
            
            # Padrão Global (Sem grandes oscilações)
            'padrao':          [1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.1]
        }

        # --- SEU DICIONÁRIO DE CIDADES COMPLETO AQUI (Resumido para o exemplo) ---
        self.RAW_INDICES = {
            "madrid": 100, "londres": 175, "paris": 160, "nova york": 190, "miami": 155,
            "maragogi": 125, "fernando de noronha": 170, "rio de janeiro": 110, "gramado": 125,
            "dubai": 140, "cancun": 120, "bangkok": 80
            # ... (INSIRA A LISTA GIGANTE DO CHATGPT AQUI) ...
        }

    def _normalize(self, text):
        return ''.join(c for c in unicodedata.normalize('NFD', text)
                      if unicodedata.category(c) != 'Mn').lower().strip()

    def get_index_and_profile(self, destination):
        dest_clean = self._normalize(destination)
        idx = 100
        profile = 'padrao'
        found_idx = False

        # 1. Busca Índice Local
        for city, val in self.RAW_INDICES.items():
            if self._normalize(city) in dest_clean:
                idx = val
                found_idx = True
                self.audit.append({"src": "LOCAL", "msg": f"Custo local: {city.title()} (Índice {idx})", "status": "OK"})
                break
        
        # 2. Busca Perfil Climático (Online)
        self.audit.append({"src": "WEB", "msg": "Analisando perfil climático da região...", "status": "INFO"})
        prof, address = self.online_locator.identify_profile(destination)
        
        if prof:
            profile = prof
            self.audit.append({"src": "WEB", "msg": f"Perfil Climático identificado: {prof.upper().replace('_', ' ')}", "status": "OK"})
        
        # Ajuste Fino Manual para Brasil (Garantia)
        if not found_idx and 'brasil' in dest_clean:
             idx = 85 # Média Brasil se não achar a cidade
             profile = 'sul_tropical'

        return idx, profile

class AccommodationProvider:
    def __init__(self):
        self.audit = []
    def estimate_adr(self, price_index, style_pct):
        BASE_HOTEL_USD = 120.0
        city_factor = price_index / 100.0
        style_factor = np.exp(1.6 * (style_pct - 0.45))
        return BASE_HOTEL_USD * city_factor * style_factor

# --- 4. ENGINE PRINCIPAL ---
class CostEngine:
    def __init__(self):
        self.fx = FXProvider()
        self.geo = GeoCostProvider()
        self.hotel = AccommodationProvider()
        self.audit_log = []

    def calculate_cost(self, destination, days, travelers, style, currency, vibe="tourist_mix", start_date=None):
        self.audit_log = []
        
        # 1. Câmbio
        usd_rate = self.fx.get_rate(currency)
        self.audit_log.extend(self.fx.audit)
        
        # 2. Geografia e Clima
        idx, profile = self.geo.get_index_and_profile(destination)
        self.audit_log.extend(self.geo.audit)
        
        # 3. Sazonalidade Matricial
        season_factor = 1.0
        if start_date:
            month_idx = start_date.month - 1 # Array começa em 0
            matrix = self.geo.SEASONALITY_MATRIX.get(profile, self.geo.SEASONALITY_MATRIX['padrao'])
            season_factor = matrix[month_idx]
            
            percentage = int((season_factor - 1) * 100)
            sign = "+" if percentage > 0 else ""
            self.audit_log.append({"src": "DATA", "msg": f"Sazonalidade ({start_date.strftime('%B')}): {sign}{percentage}% no preço.", "status": "INFO"})

        # 4. Cálculo
        style_cfg = StyleConfig.SETTINGS.get(style.lower(), StyleConfig.SETTINGS['moderado'])
        vibe_mult = VibeConfig.MULTIPLIERS.get(vibe.lower(), VibeConfig.MULTIPLIERS['tourist_mix'])
        
        breakdown_usd = {}
        daily_lifestyle_usd = 0
        
        for cat, base_val in BASE_SPEND_USD_ANCHOR.items():
            # Sazonalidade afeta menos comida/transporte e mais hotel/aéreo
            # Vamos aplicar peso 0.5 da sazonalidade no lifestyle
            lifestyle_seasonality = 1 + (season_factor - 1) * 0.5
            
            val = base_val * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat] * lifestyle_seasonality
            breakdown_usd[cat] = val
            daily_lifestyle_usd += val
            
        rooms = math.ceil(travelers / 2)
        adr_usd = self.hotel.estimate_adr(idx, style_cfg['hotel_pct'])
        adr_usd *= season_factor # Hotel absorve sazonalidade cheia (100%)
        
        total_hotel = adr_usd * rooms * days
        total_life = daily_lifestyle_usd * travelers * days
        final_total = (total_hotel + total_life) * usd_rate
        
        daily_avg = (final_total / days) / travelers
        margin = 0.15

        return {
            "total": final_total,
            "daily_avg": daily_avg,
            "range": [final_total * (1-margin), final_total * (1+margin)],
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
