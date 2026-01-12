import random
from datetime import datetime

# --- 1. BANCO DE DADOS INTELIGENTE (Mock Data) ---
COST_TIERS = {
    1: 60,   # Barato
    2: 100,  # Médio-Baixo
    3: 150,  # Médio
    4: 220,  # Caro
    5: 350   # Muito Caro
}

# Dicionário de Cidades Conhecidas
KNOWN_CITIES = {
    "nova york": 5, "new york": 5, "suíça": 5, "zurich": 5, "singapura": 5,
    "paris": 4, "londres": 4, "london": 4, "amsterdam": 4, "dublin": 4, "toquio": 4,
    "roma": 3, "rome": 3, "madrid": 3, "barcelona": 3, "lisboa": 3, "rio de janeiro": 3, "são paulo": 3,
    "buenos aires": 2, "santiago": 2, "budapeste": 2, "praga": 2, "cancun": 2,
    "la paz": 1, "bangkok": 1, "bali": 1, "hanoi": 1, "nordeste": 2
}

# --- 2. CONFIGURAÇÕES DE MERCADO ---
VIBE_MULTIPLIERS = {
    "econômico": 0.7,
    "moderado": 1.0,
    "conforto": 1.6,
    "luxo": 2.8
}

CURRENCY_RATES = {
    "USD": 1.0,
    "BRL": 6.10,
    "EUR": 0.92
}

# --- 3. LÓGICA DE SAZONALIDADE ---
def get_seasonality_factor(city_name, month):
    city = city_name.lower()
    factor = 1.0
    
    # Alta Temporada Europa/EUA (Verão do Norte)
    is_north_summer = month in [6, 7, 8]
    # Alta Temporada América do Sul (Verão do Sul)
    is_south_summer = month in [12, 1, 2]
    
    europe_usa_keywords = ["paris", "londres", "york", "roma", "madrid", "lisboa", "amsterdam", "disney"]
    south_america_keywords = ["rio", "paulo", "buenos", "santiago", "bahia", "nordeste"]

    if any(k in city for k in europe_usa_keywords) and is_north_summer:
        factor = 1.30
    elif any(k in city for k in south_america_keywords) and is_south_summer:
        factor = 1.30
        
    return factor

# --- 4. FUNÇÃO PRINCIPAL ---
# Atenção: O erro acontece se esta definição não for encontrada
def calculate_cost(dest, days, travelers, vibe, currency, start_date=None):
    
    # A. Identificar o Custo Base
    dest_lower = dest.lower()
    tier = 3 
    
    for key, val in KNOWN_CITIES.items():
        if key in dest_lower:
            tier = val
            break
            
    base_daily_cost_usd = COST_TIERS[tier]
    
    # B. Aplicar Vibe
    vibe_factor = VIBE_MULTIPLIERS.get(vibe, 1.0)
    
    # C. Aplicar Sazonalidade
    season_factor = 1.0
    if start_date:
        season_factor = get_seasonality_factor(dest, start_date.month)
    
    # D. Cálculo Final
    daily_person_usd = base_daily_cost_usd * vibe_factor * season_factor
    ticket_budget_usd = 15 * vibe_factor 
    total_daily_person_usd = daily_person_usd + ticket_budget_usd
    
    total_trip_usd = total_daily_person_usd * days * travelers
    
    # E. Conversão
    if currency == "BRL":
        final_total = total_trip_usd * CURRENCY_RATES["BRL"]
        final_daily = total_daily_person_usd * CURRENCY_RATES["BRL"]
    elif currency == "EUR":
        final_total = total_trip_usd * 0.92 
        final_daily = total_daily_person_usd * 0.92
    else:
        final_total = total_trip_usd
        final_daily = total_daily_person_usd

    # F. Breakdown
    breakdown = {
        "accom": final_total * 0.40,
        "food": final_total * 0.35,
        "transport": final_total * 0.25 
    }
    
    return final_total, breakdown, final_daily
