import random
from datetime import datetime

# --- 1. BANCO DE DADOS INTELIGENTE (Mock Data) ---
# Classificamos destinos por "Custo Base Diário" em Dólares (USD)
# Isso inclui: Hospedagem Simples + Alimentação + Transporte Básico
COST_TIERS = {
    1: 60,   # Barato (Ex: Bolívia, Tailândia, interior do Brasil)
    2: 100,  # Médio-Baixo (Ex: Buenos Aires, Leste Europeu, Portugal fora de época)
    3: 150,  # Médio (Ex: Espanha, Itália, Capitais do BR)
    4: 220,  # Caro (Ex: Paris, Londres, Amsterdam)
    5: 350   # Muito Caro (Ex: Suíça, Nova York, Singapura)
}

# Dicionário de Cidades Conhecidas (Para mapear o Tier)
# Normalizamos tudo para minúsculas para facilitar a busca
KNOWN_CITIES = {
    # Tier 5
    "nova york": 5, "new york": 5, "suíça": 5, "zurich": 5, "singapura": 5,
    # Tier 4
    "paris": 4, "londres": 4, "london": 4, "amsterdam": 4, "dublin": 4, "toquio": 4,
    # Tier 3
    "roma": 3, "rome": 3, "madrid": 3, "barcelona": 3, "lisboa": 3, "rio de janeiro": 3, "são paulo": 3,
    # Tier 2
    "buenos aires": 2, "santiago": 2, "budapeste": 2, "praga": 2, "cancun": 2,
    # Tier 1
    "la paz": 1, "bangkok": 1, "bali": 1, "hanoi": 1, "nordeste": 2
}

# --- 2. CONFIGURAÇÕES DE MERCADO ---
# Fatores de multiplicação baseados na escolha do usuário
VIBE_MULTIPLIERS = {
    "econômico": 0.7,   # Hostel, street food, metrô
    "moderado": 1.0,    # Hotel 3*, bistrô, uber/metrô (Base)
    "conforto": 1.6,    # Hotel 4*, restaurantes bons, táxi
    "luxo": 2.8         # Hotel 5*, menu degustação, motorista
}

CURRENCY_RATES = {
    "USD": 1.0,
    "BRL": 6.10, # Dólar Turismo + Spread (Margem de segurança)
    "EUR": 0.92
}

# --- 3. LÓGICA DE SAZONALIDADE ---
def get_seasonality_factor(city_name, month):
    """Retorna o ágio de alta temporada baseado no hemisfério/mês"""
    city = city_name.lower()
    factor = 1.0
    
    # Alta Temporada Europa/EUA (Verão do Norte)
    is_north_summer = month in [6, 7, 8]
    # Alta Temporada América do Sul (Verão do Sul)
    is_south_summer = month in [12, 1, 2]
    
    europe_usa_keywords = ["paris", "londres", "york", "roma", "madrid", "lisboa", "amsterdam", "disney"]
    south_america_keywords = ["rio", "paulo", "buenos", "santiago", "bahia", "nordeste"]

    if any(k in city for k in europe_usa_keywords) and is_north_summer:
        factor = 1.30 # +30% em Julho/Agosto na Europa
    elif any(k in city for k in south_america_keywords) and is_south_summer:
        factor = 1.30 # +30% no Reveillon/Carnaval no Sul
        
    return factor

# --- 4. FUNÇÃO PRINCIPAL ---
def calculate_cost(dest, days, travelers, vibe, currency, start_date=None):
    
    # A. Identificar o Custo Base do Destino
    dest_lower = dest.lower()
    tier = 3 # Começa assumindo Tier Médio (Global Average)
    
    # Tenta achar correspondência exata ou parcial
    for key, val in KNOWN_CITIES.items():
        if key in dest_lower:
            tier = val
            break
            
    base_daily_cost_usd = COST_TIERS[tier]
    
    # B. Aplicar Vibe
    vibe_factor = VIBE_MULTIPLIERS.get(vibe, 1.0)
    
    # C. Aplicar Sazonalidade (Se tiver data)
    season_factor = 1.0
    if start_date:
        season_factor = get_seasonality_factor(dest, start_date.month)
    
    # D. Cálculo Final (Em USD)
    # Custo Diário Pessoa = Base * Vibe * Sazonalidade
    daily_person_usd = base_daily_cost_usd * vibe_factor * season_factor
    
    # Adicionar "Custo de Experiência" (Tickets/Shows)
    # Quanto mais luxuosa a vibe, mais tickets caros se assume
    ticket_budget_usd = 15 * vibe_factor 
    total_daily_person_usd = daily_person_usd + ticket_budget_usd
    
    total_trip_usd = total_daily_person_usd * days * travelers
    
    # E. Conversão de Moeda
    rate = CURRENCY_RATES.get(currency, 1.0)
    
    # Se a moeda alvo não é USD, convertemos (USD -> Moeda Alvo)
    # Ex: 100 USD * 6.10 = 610 BRL
    # Nota: Se a moeda for EUR, precisamos dividir pelo rate do par EURUSD ou usar lógica cruzada.
    # Simplificação para MVP: Base é USD.
    if currency == "BRL":
        final_total = total_trip_usd * CURRENCY_RATES["BRL"]
        final_daily = total_daily_person_usd * CURRENCY_RATES["BRL"]
    elif currency == "EUR":
        final_total = total_trip_usd * 0.92 # USD to EUR
        final_daily = total_daily_person_usd * 0.92
    else:
        final_total = total_trip_usd
        final_daily = total_daily_person_usd

    # F. Breakdown (Quebra de custos para o gráfico)
    # Regra de bolso: 40% Hospedagem, 35% Comida, 15% Transporte, 10% Extras
    breakdown = {
        "accom": final_total * 0.40,
        "food": final_total * 0.35,
        "transport": final_total * 0.25 # Inclui tickets aqui para simplificar visualização
    }
    
    return final_total, breakdown, final_daily
