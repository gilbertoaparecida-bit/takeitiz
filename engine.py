import time
import logging
import math
import numpy as np
import requests
import requests_cache
import unicodedata
from datetime import datetime
from geopy.geocoders import Nominatim
import database

# --- CONFIGURAÇÃO ---
requests_cache.install_cache('takeitiz_cache', expire_after=3600)
logging.basicConfig(level=logging.INFO)

# --- 1. A ÂNCORA (GLOBAL BASELINE - MADRID) ---
BASE_SPEND_USD_ANCHOR = {
    'food': 45.0, 
    'transport': 12.0, 
    'activities': 25.0, 
    'nightlife': 15.0,
    'misc': 8.0
}

# --- 2. CONFIGURAÇÕES (PERFIL E ESTILO) ---
class VibeConfig:
    MULTIPLIERS = {
        'tourist_mix': {'food': 1.0, 'transport': 1.0, 'activities': 1.0, 'nightlife': 0.5, 'misc': 1.0},
        'cultura':     {'food': 1.0, 'transport': 1.1, 'activities': 1.8, 'nightlife': 0.2, 'misc': 1.0},
        'gastro':      {'food': 1.8, 'transport': 0.8, 'activities': 0.5, 'nightlife': 0.6, 'misc': 1.2},
        'natureza':    {'food': 0.9, 'transport': 1.5, 'activities': 1.6, 'nightlife': 0.0, 'misc': 1.3},
        'festa':       {'food': 0.8, 'transport': 1.5, 'activities': 0.5, 'nightlife': 4.0, 'misc': 1.2},
        'familiar':    {'food': 1.2, 'transport': 1.4, 'activities': 1.1, 'nightlife': 0.0, 'misc': 1.5},
        # PERFIL BUSINESS: Transporte alto (Uber/Taxi), Atividades baixas, Comida executiva
        'business':    {'food': 1.3, 'transport': 2.0, 'activities': 0.2, 'nightlife': 0.3, 'misc': 1.5},
    }

class StyleConfig:
    # hotel_pct 1.75 gera um multiplicador exponencial para Super Luxo
    SETTINGS = {
        'econômico':  {'factor': 0.60, 'hotel_pct': 0.15},
        'moderado':   {'factor': 1.00, 'hotel_pct': 0.40}, 
        'conforto':   {'factor': 1.60, 'hotel_pct': 0.75},
        'luxo':       {'factor': 3.20, 'hotel_pct': 0.95},
        'super_luxo': {'factor': 6.00, 'hotel_pct': 1.75}
    }

# --- 3. PROVEDOR DE CÂMBIO ---
class FXProvider:
    def __init__(self):
        self.audit = []
        
    def _get_backup_rate(self, target_currency):
        with requests_cache.disabled():
            try:
                pair_map = {"BRL": "USD-BRL", "EUR": "EUR-USD"}
                pair = pair_map.get(target_currency)
                if not pair: return None
                
                url = f"https://economia.awesomeapi.com.br/last/{pair}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                key = pair.replace("-", "")
                
                if target_currency == "BRL": return float(data[key]['ask'])
                elif target_currency == "EUR": return 1 / float(data[key]['ask'])
            except: return None

    def get_rate(self, target_currency):
        self.audit = [] 
        if target_currency == "USD": return 1.0
        TOURIST_SPREAD = 1.045 
        
        try:
            import yfinance as yf
            if target_currency == "BRL":
                ticker = yf.Ticker("BRL=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    return hist['Close'].iloc[-1] * TOURIST_SPREAD
            elif target_currency == "EUR":
                ticker = yf.Ticker("EURUSD=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    return 1 / hist['Close'].iloc[-1]
        except: pass

        backup = self._get_backup_rate(target_currency)
        if backup:
            return backup * TOURIST_SPREAD if target_currency == "BRL" else backup

        fallback = {"BRL": 5.90, "EUR": 0.92}
        return fallback.get(target_currency, 1.0)

# --- 4. GEOLOCALIZAÇÃO ---
class GeoCostProvider:
    def __init__(self):
        self.audit = []
        self.geolocator = Nominatim(user_agent="takeitiz_app_v11_audit")
        
        self.SEASONALITY_MATRIX = {
            'norte_temperado': [0.80, 0.80, 0.90, 0.95, 1.00, 1.10, 1.15, 1.15, 1.00, 0.95, 0.85, 1.00],
            'sul_tropical':    [1.10, 1.05, 0.90, 0.85, 0.80, 0.80, 1.00, 0.85, 0.90, 0.95, 1.00, 1.10],
            'inverno_fugitivo':[1.10, 1.10, 1.05, 0.95, 0.85, 0.80, 0.90, 0.80, 0.75, 0.85, 0.95, 1.15],
            'sul_frio':        [0.80, 0.75, 0.80, 0.90, 0.95, 1.05, 1.15, 1.00, 0.90, 0.85, 1.00, 1.05],
            'padrao':          [1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.05, 1.05, 1.0, 1.0, 1.0, 1.05]
        }
        
    def _normalize(self, text):
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower().strip()

    def get_data(self, destination):
        # Retorna (idx, profile, modifiers)
        self.audit = [] 
        dest_clean = self._normalize(destination)
        
        # 1. Busca Exata
        for city_key, data in database.CITIES.items():
            if self._normalize(city_key) == dest_clean or (len(city_key) > 4 and self._normalize(city_key) in dest_clean):
                return data['idx'], data['profile'], data.get('modifiers', {})

        # 2. Busca por Inferência
        if "brasil" in dest_clean or "brazil" in dest_clean or any(x in dest_clean for x in [" sp", " rj", " mg", " rs", " ba"]):
             return database.DEFAULTS['BR']['idx'], database.DEFAULTS['BR']['profile'], {}
        if "usa" in dest_clean or "estados unidos" in dest_clean:
            return database.DEFAULTS['US']['idx'], database.DEFAULTS['US']['profile'], {}

        # 3. Busca por Satélite
        try:
            location = self.geolocator.geocode(destination, language='en', timeout=2)
            if location:
                address = location.raw.get('address', {})
                country = address.get('country_code', '').lower()
                state = address.get('state', '').lower()
                
                profile = 'padrao'
                if country in ['br', 'ar', 'uy', 'cl']: profile = 'sul_tropical'
                elif country in ['us', 'gb', 'fr', 'es', 'it', 'de']: profile = 'norte_temperado'
                elif 'florida' in state: profile = 'inverno_fugitivo'
                
                idx = 100
                if country == 'us': idx = 140
                elif country in ['gb', 'fr', 'ch']: idx = 120
                elif profile == 'norte_temperado': idx = 115
                elif profile == 'sul_tropical': idx = 95
                
                return idx, profile, {}
        except: pass

        return 100, 'padrao', {}

# --- 5. HOTELARIA ---
class AccommodationProvider:
    def estimate_adr(self, price_index, style_pct):
        BASE_HOTEL_USD = 120.0
        city_factor = price_index / 100.0
        style_factor = np.exp(1.6 * (style_pct - 0.45))
        return BASE_HOTEL_USD * city_factor * style_factor

# --- 6. MOTOR ---
class CostEngine:
    def __init__(self):
        self.fx = FXProvider()
        self.geo = GeoCostProvider()
        self.hotel = AccommodationProvider()

    def calculate_cost(self, destination, days, travelers, style, currency, vibe="tourist_mix", start_date=None):
        usd_rate = self.fx.get_rate(currency)
        idx, profile, modifiers = self.geo.get_data(destination)
        
        season_factor = 1.0
        if start_date:
            matrix = self.geo.SEASONALITY_MATRIX.get(profile, self.geo.SEASONALITY_MATRIX['padrao'])
            season_factor = matrix[start_date.month - 1]

        style_key = style.lower()
        if "super" in style_key: style_key = "super_luxo"
        elif "econ" in style_key: style_key = "econômico"
        
        style_cfg = StyleConfig.SETTINGS.get(style_key, StyleConfig.SETTINGS['moderado'])
        vibe_mult = VibeConfig.MULTIPLIERS.get(vibe.lower(), VibeConfig.MULTIPLIERS['tourist_mix'])
        
        breakdown_usd = {}
        daily_life_usd = 0
        
        for cat, base in BASE_SPEND_USD_ANCHOR.items():
            life_season = 1 + (season_factor - 1) * 0.5
            cat_mod = modifiers.get(cat, 1.0) 
            val = base * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat] * life_season * cat_mod
            breakdown_usd[cat] = val
            daily_life_usd += val
            
        rooms = math.ceil(travelers / 2)
        lodging_mod = modifiers.get('lodging', 1.0)
        adr_usd = self.hotel.estimate_adr(idx, style_cfg['hotel_pct']) * season_factor * lodging_mod
        
        total_hotel = adr_usd * rooms * days
        final = (total_hotel + (daily_life_usd * travelers * days)) * usd_rate
        
        return {
            "total": final,
            "daily_avg": (final / days) / travelers,
            "breakdown": {
                'lodging': total_hotel * usd_rate,
                'food': breakdown_usd['food'] * travelers * days * usd_rate,
                'transport': breakdown_usd['transport'] * travelers * days * usd_rate,
                'activities': (breakdown_usd['activities'] + breakdown_usd['nightlife']) * travelers * days * usd_rate,
                'misc': breakdown_usd['misc'] * travelers * days * usd_rate
            }
        }

engine = CostEngine()
