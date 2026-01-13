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
# Base: Madrid (100)
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
        self.geolocator = Nominatim(user_agent="takeitiz_app_v3_global")
        self.COUNTRY_MAP = {
            'br': 'brasil', 'us': 'america do norte', 'gb': 'europa', 'fr': 'europa', 
            'it': 'europa', 'de': 'europa', 'es': 'europa', 'pt': 'europa',
            'jp': 'asia', 'cn': 'asia', 'ae': 'oriente medio', 'qa': 'oriente medio',
            'ar': 'america do sul', 'cl': 'america do sul', 'au': 'oceania', 'nz': 'oceania'
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
        
        # --- BASE DE DADOS GLOBAL UNIFICADA (MADRID=100) ---
        # Inclui Europa, Américas, Ásia/África e Brasil Profundo
        self.RAW_INDICES = {
            # EUROPA
            "madrid": 100, "barcelona": 112, "sevilha": 95, "seville": 95, "valencia": 98, "malaga": 97, "granada": 88,
            "bilbao": 108, "sao sebastiao": 125, "san sebastian": 125, "palma de maiorca": 120, "ibiza": 135,
            "santiago de compostela": 90, "lisboa": 95, "lisbon": 95, "porto": 88, "faro": 90, "funchal": 105,
            "paris": 160, "nice": 135, "lyon": 125, "marselha": 118, "bordeaux": 130, "cannes": 155,
            "londres": 175, "london": 175, "edimburgo": 150, "manchester": 135, "dublin": 155,
            "amsterda": 155, "amsterdam": 155, "bruxelas": 125, "berlim": 120, "munique": 150, "frankfurt": 130,
            "roma": 135, "rome": 135, "milao": 145, "milan": 145, "veneza": 160, "florenca": 140, "napoles": 115,
            "zurique": 200, "zurich": 200, "genebra": 195, "viena": 145, "praga": 110, "budapeste": 95,
            "atenas": 105, "santorini": 140, "istambul": 90, "copenhague": 180, "estocolmo": 170, "oslo": 175,
            "reiquiavique": 190, "reykjavik": 190, "moscou": 120, "moscow": 120,

            # AMERICAS
            "nova york": 190, "new york": 190, "nyc": 190, "los angeles": 160, "sao francisco": 185, "las vegas": 145,
            "miami": 155, "orlando": 135, "chicago": 150, "washington": 165, "boston": 170, "honolulu": 200,
            "toronto": 160, "vancouver": 170, "montreal": 135, "cancun": 120, "tulum": 135, "cidade do mexico": 80,
            "punta cana": 125, "havana": 75, "nassau": 170, "buenos aires": 95, "bariloche": 120, "mendoza": 90,
            "santiago": 120, "san pedro de atacama": 135, "cartagena": 100, "bogota": 80, "cusco": 90, "lima": 85,
            "montevideo": 120, "punta del este": 145,

            # ASIA / AFRICA / OCEANIA
            "dubai": 140, "abu dhabi": 130, "doha": 150, "tel aviv": 175, "jerusalem": 150,
            "toquio": 150, "tokyo": 150, "osaka": 140, "seul": 140, "pequim": 115, "xangai": 130, "hong kong": 170,
            "bangkok": 80, "phuket": 105, "chiang mai": 70, "singapura": 160, "bali": 75, "jacarta": 80,
            "hanoi": 70, "ho chi minh": 75, "maldivas": 185, "male": 185, "nova delhi": 70, "mumbai": 85,
            "cidade do cabo": 95, "marraquexe": 85, "cairo": 80, "seychelles": 170, "vitoria seychelles": 170,
            "sidney": 160, "sydney": 160, "melbourne": 150, "auckland": 150, "papeete": 175, "bora bora": 180,

            # BRASIL (Destaques)
            "fernando de noronha": 170, "noronha": 170, "trancoso": 150, "buzios": 140, "jurere": 135,
            "sao miguel dos milagres": 135, "angra dos reis": 130, "campos do jordao": 130,
            "gramado": 125, "maragogi": 125, "itacare": 125, "praia do forte": 125,
            "rio de janeiro": 110, "rio": 110, "sao paulo": 105, "sp": 105, "brasilia": 105,
            "florianopolis": 105, "recife": 90, "salvador": 90, "fortaleza": 90, "manaus": 85,
            "foz do iguacu": 80, "ouro preto": 95, "tiradentes": 105, "bonito": 110, "jalapao": 100,
            "lencois maranhenses": 105, "pipa": 115, "jericoacoara": 110, "capitolio": 95,
            "porto seguro": 120, "arraial d ajuda": 135, "caraiva": 140, "morro de sao paulo": 130,
            "ilhabela": 120, "paraty": 115, "petropolis": 115, "visconde de maua": 115
        }
        
        self.REGIONAL_FALLBACK = {
            'oriente medio': 100, 'europa': 120, 'america do norte': 150, 
            'america do sul': 85, 'brasil': 85, 'asia': 75, 
            'africa': 80, 'oceania': 140, 'default': 100
        }

    def _normalize(self, text):
        # Remove acentos e joga pra minúsculo (ex: "São Paulo" -> "sao paulo")
        return ''.join(c for c in unicodedata.normalize('NFD', text)
                      if unicodedata.category(c) != 'Mn').lower().strip()

    def get_index(self, destination):
        # Normaliza a entrada do usuário
        dest_clean = self._normalize(destination)
        
        # 1. Busca Exata
        # Varre o dicionário normalizando as chaves também
        for city, idx in self.RAW_INDICES.items():
            if self._normalize(city) == dest_clean or self._normalize(city) in dest_clean:
                self.audit.append({"src": "LOCAL", "msg": f"Custo local identificado: {city.title()} (Índice {idx})", "status": "OK"})
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
