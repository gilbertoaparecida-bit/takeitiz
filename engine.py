import time
import logging
import math
import numpy as np
import requests_cache
from datetime import datetime

# --- CONFIGURAÇÃO ---
# Cache de 1 hora para chamadas externas (Performance + Proteção de Rate Limit)
requests_cache.install_cache('takeitiz_cache', expire_after=3600)
logging.basicConfig(level=logging.INFO)

# --- 1. A ÂNCORA (GLOBAL BASELINE) ---
# Valores em USD para uma cidade de Índice 100 (Ex: Lisboa/Madrid)
# Atualização: Anual (Inflação Dólar)
BASE_SPEND_USD_ANCHOR = {
    'food': 45.0,       # Almoço executivo + Jantar médio
    'transport': 12.0,  # 2 tickets metrô + 1 Uber curto
    'activities': 25.0, # 1 Ticket de atração média
    'nightlife': 0.0,   # Base é zero (depende da Vibe)
    'misc': 8.0         # Água, café, imprevistos
}

# --- 2. CONFIGURAÇÕES DE PERFIL (MODIFIERS) ---

class VibeConfig:
    # Como a Vibe distorce a Cesta Básica
    MULTIPLIERS = {
        'tourist_mix': {'food': 1.0, 'transport': 1.0, 'activities': 1.0, 'nightlife': 0.5, 'misc': 1.0},
        'cultura':     {'food': 1.0, 'transport': 1.1, 'activities': 1.8, 'nightlife': 0.2, 'misc': 1.0},
        'gastro':      {'food': 1.8, 'transport': 0.8, 'activities': 0.5, 'nightlife': 0.6, 'misc': 1.2},
        'natureza':    {'food': 0.9, 'transport': 1.5, 'activities': 1.4, 'nightlife': 0.1, 'misc': 1.3},
        'festa':       {'food': 0.8, 'transport': 1.5, 'activities': 0.5, 'nightlife': 3.0, 'misc': 1.2},
        'familiar':    {'food': 1.2, 'transport': 1.4, 'activities': 1.1, 'nightlife': 0.0, 'misc': 1.5},
    }

class StyleConfig:
    # Como o Nível de Luxo afeta o preço e a escolha do hotel
    # Hotel_Pct: Percentil da distribuição de preços (0.15 = Econômico, 0.95 = Topo)
    SETTINGS = {
        'econômico': {'factor': 0.60, 'hotel_pct': 0.15},
        'moderado':  {'factor': 1.00, 'hotel_pct': 0.40}, # A referência
        'conforto':  {'factor': 1.60, 'hotel_pct': 0.75},
        'luxo':      {'factor': 3.20, 'hotel_pct': 0.95},
    }

# --- 3. PROVEDORES DE DADOS ---

class FXProvider:
    """Fornece taxas de câmbio Real-Time via Yahoo Finance"""
    def __init__(self):
        self.audit = []

    def get_rate(self, target_currency):
        if target_currency == "USD": return 1.0
        
        pair = f"{target_currency}=X" if target_currency == "BRL" else f"{target_currency}USD=X"
        
        try:
            import yfinance as yf
            # O Yahoo usa convenções diferentes.
            # BRL=X -> Cotação USD/BRL (ex: 6.10)
            # EURUSD=X -> Cotação EUR/USD (ex: 1.08)
            
            if target_currency == "BRL":
                ticker = yf.Ticker("BRL=X")
                hist = ticker.history(period="1d")
                if not hist.empty:
                    rate = hist['Close'].iloc[-1]
                    # Spread de segurança (IOF + Spread bancário ~4.5%)
                    final_rate = rate * 1.045
                    self.audit.append({"src": "FX_API", "msg": f"USD->BRL: {final_rate:.4f} (Live + Spread)", "status": "OK"})
                    return final_rate

            elif target_currency == "EUR":
                ticker = yf.Ticker("EURUSD=X") # Quanto vale 1 Euro em USD
                hist = ticker.history(period="1d")
                if not hist.empty:
                    eur_usd = hist['Close'].iloc[-1]
                    # Se 1 EUR = 1.08 USD, então 1 USD = 1 / 1.08 EUR
                    rate = 1 / eur_usd
                    self.audit.append({"src": "FX_API", "msg": f"USD->EUR: {rate:.4f} (Live)", "status": "OK"})
                    return rate

        except Exception as e:
            self.audit.append({"src": "FX_API", "msg": f"Falha API: {str(e)}", "status": "ERROR"})
        
        # Fallback de Segurança
        fallback = {"BRL": 6.15, "EUR": 0.92}
        val = fallback.get(target_currency, 1.0)
        self.audit.append({"src": "FX_FALLBACK", "msg": f"Usando taxa fixa: {val}", "status": "WARN"})
        return val

class GeoCostProvider:
    """
    Define o Custo Relativo das Cidades.
    Base 100 = Lisboa/Madrid.
    Atualização: Trimestral (via código ou JSON futuro).
    """
    def __init__(self):
        self.audit = []
        # O MAPA DE CALOR DO MUNDO (Indices Relativos)
        self.INDICES = {
            # Top Tier (180+)
            'zurique': 210, 'genebra': 200, 'suíça': 205,
            'nova york': 190, 'nyc': 190, 'nova iorque': 190,
            'singapura': 185, 'oslo': 180, 'islandia': 180,
            
            # High Tier (140-179)
            'londres': 175, 'london': 175,
            'paris': 160, 'frança': 160,
            'amsterdam': 155, 'dublin': 155,
            'copenhagen': 160, 'toquio': 145, 'tokyo': 145, 'tokio': 145,
            'sydney': 150, 'dubai': 150, 'tel aviv': 160,
            
            # Mid Tier (90-139) - A Média Global
            'roma': 115, 'milao': 120, 'veneza': 125,
            'berlim': 115, 'munique': 120,
            'barcelona': 105, 'madrid': 100,
            'lisboa': 95, 'porto': 90, 'portugal': 95,
            'cancun': 110, 'miami': 130, 'orlando': 125, 'disney': 135,
            
            # Economy Tier (60-89)
            'sao paulo': 75, 'sp': 75, 'rio de janeiro': 80, 'rio': 80,
            'santiago': 70, 'chile': 70,
            'atenas': 85, 'grecia': 85,
            'cidade do cabo': 65, 'cape town': 65,
            
            # Budget Tier (< 60)
            'buenos aires': 55, 'argentina': 55,
            'bangkok': 55, 'tailandia': 55, 'phuket': 60,
            'bali': 50, 'indonesia': 50, 'jacarta': 45,
            'budapeste': 60, 'praga': 65,
            'cairo': 40, 'egito': 40, 'vietna': 40, 'hanoi': 40, 'bolivia': 45
        }
        
        self.REGIONAL_FALLBACK = {
            'europa': 120, 'america do norte': 150, 'america do sul': 65,
            'asia': 55, 'africa': 50, 'oceania': 140, 'default': 100
        }

    def get_index(self, destination):
        dest_clean = destination.lower().strip()
        
        # 1. Busca Exata ou Parcial
        for city, idx in self.INDICES.items():
            if city in dest_clean:
                self.audit.append({"src": "GEO_DB", "msg": f"Índice encontrado: {idx} ({city})", "status": "OK"})
                return idx, "high"
        
        # 2. Fallback Regional
        region = "default"
        if any(x in dest_clean for x in ['usa', 'eua', 'canada']): region = 'america do norte'
        elif any(x in dest_clean for x in ['brasil', 'argentina', 'peru', 'colombia']): region = 'america do sul'
        elif any(x in dest_clean for x in ['frança', 'italia', 'alemanha', 'espanha', 'uk']): region = 'europa'
        
        idx = self.REGIONAL_FALLBACK[region]
        self.audit.append({"src": "GEO_FALLBACK", "msg": f"Índice regional usado: {idx} ({region})", "status": "WARN"})
        return idx, "low"

class AccommodationProvider:
    """Calcula Hospedagem usando Curva de Distribuição Log-Normal baseada no Índice"""
    def __init__(self):
        self.audit = []
        
    def estimate_adr(self, price_index, style_pct):
        # Base: Hotel Standard em cidade Index 100 custa USD 120
        BASE_HOTEL_USD = 120.0
        
        # Fator Cidade: Se Index 190 -> 1.9x
        city_factor = price_index / 100.0
        
        # Fator Estilo (Curva Estatística)
        # Transforma o percentil (0.15 a 0.95) em um multiplicador de preço
        # Log-Normal simula bem preços reais (cauda longa para luxo)
        # Resulta em: Econ ~0.5x | Base ~1.0x | Luxo ~3.5x
        style_factor = np.exp(1.6 * (style_pct - 0.45))
        
        estimated = BASE_HOTEL_USD * city_factor * style_factor
        self.audit.append({"src": "HOTEL_ALGO", "msg": f"Diária Est. (USD): {estimated:.2f} (Pct: {style_pct})", "status": "OK"})
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
        t_start = time.time()
        
        # 1. Normalização
        style_clean = style.lower() if style.lower() in StyleConfig.SETTINGS else "moderado"
        vibe_clean = vibe.lower() if vibe.lower() in VibeConfig.MULTIPLIERS else "tourist_mix"
        
        # 2. Dados Base
        usd_rate = self.fx.get_rate(currency)
        self._log(self.fx)
        
        idx, confidence = self.geo.get_index(destination)
        self._log(self.geo)
        
        # 3. Sazonalidade (Simples)
        season_factor = 1.0
        if start_date:
            month = start_date.month
            # Alta: Dez, Jan, Jun, Jul, Ago
            if month in [12, 1, 6, 7, 8]:
                season_factor = 1.25 # +25%
                self.audit_log.append({"src": "SEASON", "msg": "Alta Temporada (+25%)", "status": "INFO"})
        
        # 4. Cálculo Lifestyle (Comida, Transp, Lazer)
        style_cfg = StyleConfig.SETTINGS[style_clean]
        vibe_mult = VibeConfig.MULTIPLIERS[vibe_clean]
        
        daily_lifestyle_usd = 0
        breakdown_usd = {}
        
        for cat, base_val in BASE_SPEND_USD_ANCHOR.items():
            # Fórmula Mágica:
            # Base * (IndiceCidade/100) * FatorEstilo * FatorVibe * Sazonalidade(leve)
            val = base_val * (idx / 100.0) * style_cfg['factor'] * vibe_mult[cat]
            # Sazonalidade afeta menos comida/transporte, mas afeta
            val *= (1 + (season_factor - 1) * 0.5) 
            
            breakdown_usd[cat] = val
            daily_lifestyle_usd += val
            
        # 5. Cálculo Hotel (Impacto Sazonal Completo)
        rooms = math.ceil(travelers / 2)
        adr_usd = self.hotel.estimate_adr(idx, style_cfg['hotel_pct'])
        self._log(self.hotel)
        
        adr_usd *= season_factor # Hotel sofre full com temporada
        total_hotel_trip_usd = adr_usd * rooms * days
        
        # 6. Totais e Conversão
        total_lifestyle_trip_usd = daily_lifestyle_usd * travelers * days
        total_trip_usd = total_lifestyle_trip_usd + total_hotel_trip_usd
        
        final_total = total_trip_usd * usd_rate
        daily_avg_person = (final_total / days) / travelers
        
        # 7. Margem de Erro (Range)
        margin = 0.12 if confidence == "high" else 0.25
        
        # 8. Breakdown Final (Na moeda alvo)
        breakdown_final = {
            'lodging': total_hotel_trip_usd * usd_rate,
            'food': breakdown_usd['food'] * travelers * days * usd_rate,
            'transport': breakdown_usd['transport'] * travelers * days * usd_rate,
            'activities': breakdown_usd['activities'] * travelers * days * usd_rate + (breakdown_usd['nightlife'] * travelers * days * usd_rate),
            'misc': breakdown_usd['misc'] * travelers * days * usd_rate
        }

        self.audit_log.append({"src": "ENGINE", "msg": f"Calc em {time.time()-t_start:.3f}s", "status": "DONE"})

        return {
            "total": final_total,
            "daily_avg": daily_avg_person,
            "range": [final_total * (1-margin), final_total * (1+margin)],
            "breakdown": breakdown_final,
            "audit": self.audit_log
        }

# Instância Singleton
engine = CostEngine()
