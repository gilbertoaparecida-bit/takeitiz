import random
from datetime import datetime

# --- 1. BANCO DE DADOS INTELIGENTE (Mock Data) ---
# Tier 1: Sudeste Asiático, Bolívia, Índia (Mochilão/Barato)
# Tier 2: América do Sul (capitais), Leste Europeu, África do Sul
# Tier 3: Europa do Sul (PT, ES, IT), Brasil (Turístico), EUA (Interior)
# Tier 4: Europa do Norte (UK, FR, DE), Japão, Austrália, Canadá
# Tier 5: Suíça, EUA (NY/SF/LA), Singapura, Escandinávia (Topo do Mundo)

COST_TIERS = {
    1: 50,   
    2: 90,   
    3: 150,  
    4: 240,  
    5: 380   
}

# Dicionário de Cidades Expandido (Variações PT/EN)
KNOWN_CITIES = {
    # TIER 5 - O Topo da Pirâmide
    "nova york": 5, "new york": 5, "nyc": 5, "nova iorque": 5, "ny": 5,
    "suíça": 5, "suica": 5, "zurich": 5, "zurique": 5, "genebra": 5, "geneva": 5,
    "singapura": 5, "singapore": 5,
    "são francisco": 5, "san francisco": 5, "california": 5, "los angeles": 5,
    "oslo": 5, "copenhagen": 5, "reikjavik": 5, "islandia": 5, "noruega": 5,
    
    # TIER 4 - Metrópoles Caras
    "paris": 4, "frança": 4, "franca": 4,
    "londres": 4, "london": 4, "inglaterra": 4, "uk": 4, "reino unido": 4,
    "amsterdam": 4, "holanda": 4,
    "dublin": 4, "irlanda": 4,
    "toquio": 4, "tokyo": 4, "tokio": 4, "japao": 4, "japão": 4,
    "sidney": 4, "sydney": 4, "melbourne": 4, "australia": 4,
    "vancouver": 4, "toronto": 4, "canada": 4,
    "dubai": 4, "emirados": 4,

    # TIER 3 - O Padrão Turístico
    "roma": 3, "rome": 3, "italia": 3, "milao": 3, "veneza": 3,
    "madrid": 3, "barcelona": 3, "espanha": 3,
    "lisboa": 3, "lisbon": 3, "porto": 3, "portugal": 3,
    "rio de janeiro": 3, "rio": 3, "rj": 3,
    "são paulo": 3, "sao paulo": 3, "sp": 3, "brasil": 3,
    "miami": 3, "orlando": 3, "disney": 3, "florida": 3,
    "berlim": 3, "berlin": 3, "munique": 3, "alemanha": 3,
    
    # TIER 2 - Custo Benefício
    "buenos aires": 2, "argentina": 2,
    "santiago": 2, "chile": 2,
    "budapeste": 2, "hungria": 2,
    "praga": 2, "republica tcheca": 2,
    "cancun": 2, "mexico": 2,
    "cidade do cabo": 2, "cape town": 2, "africa do sul": 2,
    "istambul": 2, "turquia": 2,
    "atenas": 2, "grecia": 2, "santorini": 2,

    # TIER 1 - Econômicos
    "la paz": 1, "bolivia": 1,
    "bangkok": 1, "tailandia": 1, "phuket": 1,
    "bali": 1, "indonesia": 1, "jacarta": 1, "jakarta": 1,
    "hanoi": 1, "vietna": 1, "vietnam": 1,
    "india": 1, "nova delhi": 1,
    "cairo": 1, "egito": 1,
    "colombia": 1, "bogota": 1, "cartagena": 1
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
    
    # Verão Norte (Jun-Ago)
    is_north_summer = month in [6, 7, 8]
    # Verão Sul (Dez-Fev)
    is_south_summer = month in [12, 1, 2]
    
    # Palavras-chave para identificar região
    europe_usa = ["paris", "londres", "london", "york", "iorque", "roma", "rome", "madrid", "lisboa", "lisbon", "amsterdam", "disney", "california", "berlim", "munique", "zurique", "zurich", "toquio", "tokyo", "japao"]
    south_america = ["rio", "paulo", "buenos", "santiago", "bahia", "nordeste", "florianopolis", "cape town", "cidade do cabo"]

    if any(k in city for k in europe_usa) and is_north_summer:
        factor = 1.30 # +30% Alta Norte
    elif any(k in city for k in south_america) and is_south_summer:
        factor = 1.30 # +30% Alta Sul
        
    return factor

# --- 4. FUNÇÃO PRINCIPAL ---
def calculate_cost(dest, days, travelers, vibe, currency, start_date=None):
    
    # A. Identificar o Custo Base (Normalização)
    dest_lower = dest.lower().strip() 
    tier = 3 # Default se não achar nada
    
    # Tenta achar correspondência
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
    
    # Custo de Experiência (Tickets/Shows)
    # Vibe Luxo gasta muito mais em tickets
    ticket_budget_usd = 20 * vibe_factor 
    
    total_daily_person_usd = daily_person_usd + ticket_budget_usd
    total_trip_usd = total_daily_person_usd * days * travelers
    
    # E. Conversão
    if currency == "BRL":
        rate = CURRENCY_RATES["BRL"]
    elif currency == "EUR":
        rate = CURRENCY_RATES["EUR"]
    else:
        rate = 1.0
        
    final_total = total_trip_usd * rate
    final_daily = total_daily_person_usd * rate

    # F. Breakdown Ajustado
    breakdown = {
        "accom": final_total * 0.45,   
        "food": final_total * 0.35,
        "transport": final_total * 0.20
    }
    
    return final_total, breakdown, final_daily
