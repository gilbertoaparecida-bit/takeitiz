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
                
                if target_currency == "BRL":
                    return float(data[key]['ask'])
                elif target_currency == "EUR":
                    return 1 / float(data[key]['ask'])
            except Exception as e:
                self.audit.append({"src": "DEBUG", "msg": f"Erro Backup: {str(e)}", "status": "WARN"})
                return None

    def get_rate(self, target_currency):
        self.audit = [] 
        if target_currency == "USD": return 1.0
        
        try:
            import yfinance as yf
            if target_currency == "BRL":
                ticker = yf.Ticker("BRL=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    rate = hist['Close'].iloc[-1]
                    final = rate * 1.045
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

        backup = self._get_backup_rate(target_currency)
        if backup:
            final = backup * 1.045 if target_currency == "BRL" else backup
            self.audit.append({"src": "CÂMBIO", "msg": f"⚠️ Yahoo instável. Usando Backup (BC): {final:.2f}", "status": "INFO"})
            return final

        fallback = {"BRL": 6.15, "EUR": 0.92}
        val = fallback.get(target_currency, 1.0)
        self.audit.append({"src": "CÂMBIO", "msg": f"⛔ APIs Offline. Usando taxa fixa: {val}", "status": "WARN"})
        return val

# --- 4. GEOLOCALIZAÇÃO E PERFIL CLIMÁTICO ---
class OnlineGeoLocator:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="takeitiz_app_v9_clean")
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
                if country == 'us' and 'florida' in state: return 'inverno_fugitivo', location.address
                return self.COUNTRY_PROFILE_MAP.get(country, 'padrao'), location.address
        except: return None, None
        return None, None

class GeoCostProvider:
    def __init__(self):
        self.audit = []
        self.online_locator = OnlineGeoLocator()
        
        # MATRIZ DE SAZONALIDADE INTELIGENTE (Meses 0 a 11 / Jan a Dez)
        # Lógica: Base 1.0 = Preço Padrão de Alta Temporada.
        # Valores < 1.0 = Descontos de Baixa/Média Temporada.
        # Valores > 1.0 = Apenas leve ágio para Pico Extremo.
        
        self.SEASONALITY_MATRIX = {
            # EUA/Europa: Baixa no inverno (Jan-Mar), Média na Primavera/Outono, Alta no Verão
            'norte_temperado': [0.80, 0.80, 0.90, 0.95, 1.00, 1.10, 1.15, 1.15, 1.00, 0.95, 0.85, 1.00],
            
            # Brasil Praia/Verão: Alta no verão, Baixa no outono, Repique em Julho
            'sul_tropical':    [1.10, 1.05, 0.90, 0.85, 0.80, 0.80, 1.00, 0.85, 0.90, 0.95, 1.00, 1.10],
            
            # Caribe/Nordeste Top: Foge do inverno do norte. Alta no começo do ano.
            'inverno_fugitivo':[1.10, 1.10, 1.05, 0.95, 0.85, 0.80, 0.90, 0.80, 0.75, 0.85, 0.95, 1.15],
            
            # Serras (Gramado/Bariloche): Baixa no verão, Graduação no Outono, Pico no Inverno
            'sul_frio':        [0.80, 0.75, 0.80, 0.90, 0.95, 1.05, 1.15, 1.00, 0.90, 0.85, 1.00, 1.05],
            
            # Padrão Mundial (Sem sazonalidade agressiva)
            'padrao':          [1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.05, 1.05, 1.0, 1.0, 1.0, 1.05]
        }
        
    def _normalize(self, text):
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower().strip()

    def get_index_and_profile(self, destination):
        self.audit = [] 
        dest_clean = self._normalize(destination)
        
        # 1. Busca Exata no Database (Otimizado)
        # Tenta match exato ou "contém"
        for city_key, data in database.CITIES.items():
            if self._normalize(city_key) == dest_clean or (len(city_key) > 4 and self._normalize(city_key) in dest_clean):
                self.audit.append({"src": "DATABASE", "msg": f"Dados locais encontrados: {city_key.title()}", "status": "OK"})
                return data['idx'], data['profile']

        # 2. Busca por Inferência (Fallback Rápido)
        if "brasil" in dest_clean or "brazil" in dest_clean or any(x in dest_clean for x in [" sp", " rj", " mg", " rs", " ba", " sc"]):
             self.audit.append({"src": "SISTEMA", "msg": "Cidade BR não mapeada. Usando média nacional.", "status": "INFO"})
             return database.DEFAULTS['BR']['idx'], database.DEFAULTS['BR']['profile']
             
        if "usa" in dest_clean or "estados unidos" in dest_clean:
            return database.DEFAULTS['US']['idx'], database.DEFAULTS['US']['profile']

        # 3. Busca por Satélite (Fallback Lento)
        self.audit.append({"src": "WEB", "msg": "Consultando satélite para local desconhecido...", "status": "INFO"})
        prof, address = self.online_locator.identify_profile(destination)
        
        idx = 100 # Padrão Madrid
        if prof:
            self.audit.append({"src": "WEB", "msg": f"Localizado: {address[:30]}...", "status": "OK"})
            if prof == 'sul_tropical': idx = 95
            if prof == 'norte_temperado': idx = 115
            return idx, prof

        self.audit.append({"src": "SISTEMA", "msg": "Local não encontrado. Usando base mundial.", "status": "WARN"})
        return 100, 'padrao'

# --- 5. PREÇO DE HOTELARIA ---
class AccommodationProvider:
    def __init__(self):
        self.audit = []
    def estimate_adr(self, price_index, style_pct):
        self.audit = [] 
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
        
        # 1. Câmbio
        usd_rate = self.fx.get_rate(currency)
        self.audit_log.extend(self.fx.audit)
        
        # 2. Geografia e Clima
        idx, profile = self.geo.get_index_and_profile(destination)
        self.audit_log.extend(self.geo.audit)
        
        # 3. Sazonalidade
        season_factor = 1.0
        if start_date:
            month_idx = start_date.month - 1
            matrix = self.geo.SEASONALITY_MATRIX.get(profile, self.geo.SEASONALITY_MATRIX['padrao'])
            season_factor = matrix[month_idx]
            
            # Cálculo de Porcentagem para Log
            pct = int((season_factor - 1) * 100)
            sign = "+" if pct > 0 else ""
            msg_sazonal = "Média Temporada"
            if pct <= -10: msg_sazonal = "Baixa Temporada (Desconto)"
            if pct >= 10: msg_sazonal = "Alta Temporada (Pico)"
            
            self.audit_log.append({"src": "DATA", "msg": f"Sazonalidade ({start_date.strftime('%B')}) [{profile}]: {sign}{pct}% - {msg_sazonal}", "status": "INFO"})

        # 4. Cálculo
        style_cfg = StyleConfig.SETTINGS.get(style.lower(), StyleConfig.SETTINGS['moderado'])
        vibe_mult = VibeConfig.MULTIPLIERS.get(vibe.lower(), VibeConfig.MULTIPLIERS['tourist_mix'])
        
        breakdown_usd = {}
        daily_life_usd = 0
        
        for cat, base in BASE_SPEND_USD_ANCHOR.items():
            # A sazonalidade afeta menos a comida/lazer do que o hotel (peso 0.5)
            life_season = 1 + (season_factor - 1) * 0.5
            val = base * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat] * life_season
            breakdown_usd[cat] = val
            daily_life_usd += val
            
        rooms = math.ceil(travelers / 2)
        # Hotel absorve a sazonalidade cheia (peso 1.0)
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
