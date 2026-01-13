import time
import logging
import math
import numpy as np
import requests_cache
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
                    final_rate = rate * 1.045
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
        self.geolocator = Nominatim(user_agent="takeitiz_app_v2")
        self.COUNTRY_MAP = {
            'br': 'brasil', 'us': 'america do norte', 'gb': 'europa', 'fr': 'europa', 
            'it': 'europa', 'de': 'europa', 'es': 'europa', 'pt': 'europa',
            'jp': 'asia', 'cn': 'asia', 'ae': 'oriente medio', 'qa': 'oriente medio',
            'ar': 'america do sul', 'cl': 'america do sul'
        }

    def identify_region(self, city_name):
        try:
            location = self.geolocator.geocode(city_name, language='en', timeout=2)
            if location:
                address = location.raw.get('address', {})
                country_code = address.get('country_code', '').lower()
                if country_code in self.COUNTRY_MAP:
                    return self.COUNTRY_MAP[country_code], location.address
                return "default", location.address
        except:
            return None, None
        return None, None

class GeoCostProvider:
    def __init__(self):
        self.audit = []
        self.online_locator = OnlineGeoLocator()
        
        # --- BASE DE CONHECIMENTO BILÍNGUE 🇧🇷/🇺🇸 ---
        self.INDICES = {
            # EUA / América do Norte
            'nova york': 190, 'new york': 190, 'nyc': 190,
            'miami': 130, 'orlando': 125, 'disney': 135,
            
            # Europa
            'londres': 175, 'london': 175,
            'paris': 160, 'amsterdam': 155,
            'zurique': 210, 'zurich': 210, 'genebra': 200, 'geneva': 200,
            'roma': 115, 'rome': 115, 'milao': 120, 'milan': 120,
            'barcelona': 105, 'madrid': 100, 'lisboa': 95, 'lisbon': 95,
            
            # Oriente Médio
            'dubai': 150, 'abu dhabi': 145,
            'doha': 140, 'qatar': 140, 'catar': 140,
            'tel aviv': 160, 'jerusalem': 140,
            
            # Brasil
            'fernando de noronha': 135, 'noronha': 135,
            'trancoso': 110, 'gramado': 95, 'campos do jordao': 95,
            'sao paulo': 80, 'sp': 80, 'rio de janeiro': 85, 'rio': 85,
            'brasilia': 80, 'florianopolis': 85, 'bonito': 90,
            'salvador': 70, 'recife': 65, 'fortaleza': 65,
            
            # Latam/Asia
            'buenos aires': 55, 'santiago': 70, 'cancun': 110,
            'bangkok': 55, 'tailandia': 55, 'thailand': 55,
            'toquio': 145, 'tokyo': 145, 'bali': 50
        }
        
        self.REGIONAL_FALLBACK = {
            'oriente medio': 100, 'europa': 120, 'america do norte': 150, 
            'america do sul': 65, 'brasil': 65, 'asia': 55, 
            'africa': 50, 'oceania': 140, 'default': 100
        }

    def get_index(self, destination):
        dest_clean = destination.lower().strip()
        
        # 1. Busca Exata (Dicionário Expandido)
        for city, idx in self.INDICES.items():
            if city in dest_clean:
                self.audit.append({"src": "LOCAL", "msg": f"Custo de vida local identificado: {city.title()} (Índice {idx})", "status": "OK"})
                return idx, "high"
        
        # 2. Tentativa Online
        self.audit.append({"src": "WEB", "msg": "Destino fora da base. Consultando satélite...", "status": "INFO"})
        region_found, full_address = self.online_locator.identify_region(destination)
        if region_found and region_found in self.REGIONAL_FALLBACK:
            idx = self.REGIONAL_FALLBACK[region_found]
            self.audit.append({"src": "WEB", "msg": f"Localizado via satélite: {region_found.title()} -> Usando média regional", "status": "OK"})
            return idx, "medium"

        # 3. Fallback
        idx = 100
        self.audit.append({"src": "LOCAL", "msg": f"Usando média global (Destino não mapeado)", "status": "WARN"})
        return idx, "low"

class AccommodationProvider:
    def __init__(self):
        self.audit = []
    def estimate_adr(self, price_index, style_pct):
        BASE_HOTEL_USD = 120.0
        city_factor = price_index / 100.0
        style_factor = np.exp(1.6 * (style_pct - 0.45))
        estimated = BASE_HOTEL_USD * city_factor * style_factor
        self.audit.append({"src": "HOTEL", "msg": f"Diária média estimada para o seu perfil: U$ {estimated:.0f}", "status": "OK"})
        return estimated

# --- 4. ENGINE PRINCIPAL ---
class CostEngine:
    def __init__(self):
        self.fx = FXProvider()
        self.geo = GeoCostProvider()
        self.hotel = AccommodationProvider()
        self.audit_log = []

    def _log(self, provider):
        self.audit_log.extend(provider.audit)
        provider.audit = []

    def calculate_cost(self, destination, days, travelers, style, currency, vibe="tourist_mix", start_date=None):
        self.audit_log = []
        style_clean = style.lower() if style.lower() in StyleConfig.SETTINGS else "moderado"
        vibe_clean = vibe.lower() if vibe.lower() in VibeConfig.MULTIPLIERS else "tourist_mix"
        
        usd_rate = self.fx.get_rate(currency)
        self._log(self.fx)
        
        idx, confidence = self.geo.get_index(destination)
        self._log(self.geo)
        
        season_factor = 1.0
        if start_date:
            month = start_date.month
            if month in [12, 1, 6, 7]:
                season_factor = 1.30 
                self.audit_log.append({"src": "DATA", "msg": "Alta Temporada: Preços ajustados em +30%", "status": "INFO"})
            elif month in [2, 3]:
                season_factor = 1.15
        
        style_cfg = StyleConfig.SETTINGS[style_clean]
        vibe_mult = VibeConfig.MULTIPLIERS[vibe_clean]
        
        daily_lifestyle_usd = 0
        breakdown_usd = {}
        for cat, base_val in BASE_SPEND_USD_ANCHOR.items():
            val = base_val * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat]
            val *= (1 + (season_factor - 1) * 0.4) 
            breakdown_usd[cat] = val
            daily_lifestyle_usd += val
            
        rooms = math.ceil(travelers / 2)
        adr_usd = self.hotel.estimate_adr(idx, style_cfg['hotel_pct'])
        self._log(self.hotel)
        
        adr_usd *= season_factor
        total_hotel_trip_usd = adr_usd * rooms * days
        total_lifestyle_trip_usd = daily_lifestyle_usd * travelers * days
        total_trip_usd = total_lifestyle_trip_usd + total_hotel_trip_usd
        final_total = total_trip_usd * usd_rate
        daily_avg_person = (final_total / days) / travelers
        
        margin = 0.10 if confidence == "high" else 0.25
        
        breakdown_final = {
            'lodging': total_hotel_trip_usd * usd_rate,
            'food': breakdown_usd['food'] * travelers * days * usd_rate,
            'transport': breakdown_usd['transport'] * travelers * days * usd_rate,
            'activities': breakdown_usd['activities'] * travelers * days * usd_rate + (breakdown_usd['nightlife'] * travelers * days * usd_rate),
            'misc': breakdown_usd['misc'] * travelers * days * usd_rate
        }
        self.audit_log.append({"src": "SISTEMA", "msg": "Cálculo realizado em tempo real.", "status": "DONE"})

        return {
            "total": final_total,
            "daily_avg": daily_avg_person,
            "range": [final_total * (1-margin), final_total * (1+margin)],
            "breakdown": breakdown_final,
            "audit": self.audit_log
        }

engine = CostEngine()
