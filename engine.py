import time
import logging
import math
import numpy as np
import requests_cache
from datetime import datetime

# --- CONFIGURAÇÃO ---
requests_cache.install_cache('takeitiz_cache', expire_after=3600)
logging.basicConfig(level=logging.INFO)

# --- 1. A ÂNCORA (GLOBAL BASELINE) ---
# Base: Lisboa/Madrid (Index 100)
BASE_SPEND_USD_ANCHOR = {
    'food': 45.0,       
    'transport': 12.0,  
    'activities': 25.0, 
    'nightlife': 0.0,   
    'misc': 8.0         
}

# --- 2. CONFIGURAÇÕES DE PERFIL ---

class VibeConfig:
    MULTIPLIERS = {
        'tourist_mix': {'food': 1.0, 'transport': 1.0, 'activities': 1.0, 'nightlife': 0.5, 'misc': 1.0},
        'cultura':     {'food': 1.0, 'transport': 1.1, 'activities': 1.8, 'nightlife': 0.2, 'misc': 1.0},
        'gastro':      {'food': 1.8, 'transport': 0.8, 'activities': 0.5, 'nightlife': 0.6, 'misc': 1.2},
        'natureza':    {'food': 0.9, 'transport': 1.5, 'activities': 1.6, 'nightlife': 0.1, 'misc': 1.3}, # Ecoturismo tem transfer caro
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

# --- 3. PROVEDORES DE DADOS ---

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
                    self.audit.append({"src": "CÂMBIO", "msg": f"Dólar Turismo (c/ impostos): R$ {final_rate:.2f}", "status": "OK"})
                    return final_rate

            elif target_currency == "EUR":
                ticker = yf.Ticker("EURUSD=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    eur_usd = hist['Close'].iloc[-1]
                    rate = 1 / eur_usd
                    self.audit.append({"src": "CÂMBIO", "msg": f"Paridade Euro/Dólar atualizada: {rate:.2f}", "status": "OK"})
                    return rate

        except Exception:
            pass
        
        fallback = {"BRL": 6.15, "EUR": 0.92}
        val = fallback.get(target_currency, 1.0)
        self.audit.append({"src": "CÂMBIO", "msg": f"Taxa de referência usada: {val}", "status": "WARN"})
        return val

class GeoCostProvider:
    def __init__(self):
        self.audit = []
        self.INDICES = {
            # --- MUNDO (Mantido) ---
            'zurique': 210, 'genebra': 200, 'suíça': 205,
            'nova york': 190, 'nyc': 190,
            'londres': 175, 'paris': 160, 'amsterdam': 155,
            'roma': 115, 'barcelona': 105, 'madrid': 100, 'lisboa': 95,
            'miami': 130, 'orlando': 125, 'disney': 135,
            'buenos aires': 55, 'santiago': 70, 'cancun': 110,
            
            # --- BRASIL: O GRANDE ESPECIALISTA 🇧🇷 ---
            
            # Tier Premium (Caro como Europa)
            'fernando de noronha': 135, 'noronha': 135,
            'trancoso': 110, 'caraiva': 105,
            'jericoacoara': 100, 'jeri': 100,
            'sao miguel dos milagres': 100, 'milagres': 100,
            
            # Tier Inverno/Luxo (Serras)
            'gramado': 95, 'canela': 90,
            'campos do jordao': 95,
            'monte verde': 85,
            
            # Tier Capitais Caras
            'sao paulo': 80, 'sp': 80,
            'rio de janeiro': 85, 'rio': 85, 'rj': 85,
            'brasilia': 80, 'bsb': 80,
            'florianopolis': 85, 'floripa': 85, 'jurere': 95,
            
            # Tier Ecoturismo (Logística cara, embora comida ok)
            'bonito': 90, # Passeios tabelados e caros
            'alter do chao': 80, 'alter': 80, # Barco caro
            'lençois maranhenses': 85, 'barreirinhas': 85,
            'jalapao': 85, # 4x4 mandatório
            'chapada dos veadeiros': 75, 'alto paraiso': 75, 'sao jorge': 80,
            'chapada diamantina': 70, 'lencois': 70,
            'chapada dos guimaraes': 70,
            'foz do iguacu': 75,
            
            # Tier Litoral & Capitais Turísticas (Médio)
            'salvador': 70, 'recife': 65, 'fortaleza': 65,
            'maceio': 70, 'maragogi': 80,
            'porto de galinhas': 80,
            'natal': 65, 'pipa': 75,
            'joao pessoa': 60,
            'balneario camboriu': 85,
            'arraial do cabo': 70, 'buzios': 85, 'angra dos reis': 80,
            'ubatuba': 70, 'ilhabela': 80,
            'porto seguro': 65, 'arraial dajuda': 75,
            'itacare': 75, 'morro de sao paulo': 80,
            
            # Tier Capitais Negócios/Norte/Centro
            'belo horizonte': 65, 'bh': 65,
            'curitiba': 70, 'porto alegre': 65,
            'goiania': 60, 'manaus': 70, 'belem': 65,
            'vitoria': 65, 'vila velha': 60,
            
            # Tier Histórico/Interior (Econômico)
            'ouro preto': 60, 'tiradentes': 65, 'mariana': 55,
            'diamantina': 55, 'sao joao del rei': 55,
            'caldas novas': 60, 'olimpia': 65,
            'petropolis': 70, 'paraty': 75, # Paraty é mais cara que média histórica
        }
        
        # Fallbacks Inteligentes
        self.REGIONAL_FALLBACK = {
            'europa': 120, 
            'america do norte': 150, 
            'america do sul': 65,
            'brasil': 65, # Média nacional se não achar cidade
            'asia': 55, 
            'africa': 50, 
            'oceania': 140, 
            'default': 100
        }

    def get_index(self, destination):
        dest_clean = destination.lower().strip()
        
        # 1. Busca Exata
        for city, idx in self.INDICES.items():
            if city in dest_clean:
                self.audit.append({"src": "LOCAL", "msg": f"Base de custos Brasil/Mundo: {city.title()} (Índice {idx})", "status": "OK"})
                return idx, "high"
        
        # 2. Fallback Regional
        region = "default"
        if any(x in dest_clean for x in ['brasil', 'brazil', 'bahia', 'minas', 'nordeste', 'sul']): region = 'brasil'
        elif any(x in dest_clean for x in ['usa', 'eua', 'canada']): region = 'america do norte'
        elif any(x in dest_clean for x in ['argentina', 'peru', 'chile', 'uruguai']): region = 'america do sul'
        elif any(x in dest_clean for x in ['frança', 'italia', 'alemanha', 'espanha', 'uk']): region = 'europa'
        
        idx = self.REGIONAL_FALLBACK.get(region, 100)
        self.audit.append({"src": "LOCAL", "msg": f"Destino específico não mapeado. Usando média: {region.title()}", "status": "WARN"})
        return idx, "low"

class AccommodationProvider:
    def __init__(self):
        self.audit = []
        
    def estimate_adr(self, price_index, style_pct):
        # Base Index 100 (Lisboa) = USD 120
        BASE_HOTEL_USD = 120.0
        city_factor = price_index / 100.0
        
        # Curva exponencial para diferenciar bem Luxo de Econômico
        style_factor = np.exp(1.6 * (style_pct - 0.45))
        
        estimated = BASE_HOTEL_USD * city_factor * style_factor
        self.audit.append({"src": "HOTEL", "msg": f"Diária média estimada para o seu perfil: U$ {estimated:.2f}", "status": "OK"})
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
            # Alta temporada global + Férias Brasil (Dez, Jan, Jul)
            if month in [12, 1, 6, 7]:
                season_factor = 1.30 # +30% na alta
                self.audit_log.append({"src": "DATA", "msg": "Alta Temporada (Férias/Verão) detectada (+30%)", "status": "INFO"})
            # Carnaval (Fev/Março) - Estimativa simples, ideal seria API de feriados
            elif month in [2, 3]:
                season_factor = 1.15
        
        style_cfg = StyleConfig.SETTINGS[style_clean]
        vibe_mult = VibeConfig.MULTIPLIERS[vibe_clean]
        
        daily_lifestyle_usd = 0
        breakdown_usd = {}
        
        for cat, base_val in BASE_SPEND_USD_ANCHOR.items():
            # Cálculo base
            val = base_val * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat]
            # Sazonalidade afeta consumo (preço dinâmico em praia/turismo)
            val *= (1 + (season_factor - 1) * 0.4) 
            breakdown_usd[cat] = val
            daily_lifestyle_usd += val
            
        rooms = math.ceil(travelers / 2)
        adr_usd = self.hotel.estimate_adr(idx, style_cfg['hotel_pct'])
        self._log(self.hotel)
        
        adr_usd *= season_factor # Hotel sofre 100% do impacto da sazonalidade
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
