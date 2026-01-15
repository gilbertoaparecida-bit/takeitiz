# database.py
# Base de Dados TakeItIz - Fase 3 (Clusters & Exceções)
# Adicionado suporte a 'modifiers' para corrigir disparidades locais (ex: Hotel em Lisboa).

# PERFIS CLIMÁTICOS:
# 'sul_tropical': Alta em Dez/Jan/Fev
# 'norte_temperado': Alta em Jul/Ago
# 'inverno_fugitivo': Alta em Jan/Fev/Mar
# 'sul_frio': Alta em Jun/Jul

DEFAULTS = {
    "BR": {"idx": 85, "profile": "sul_tropical"},
    "US": {"idx": 140, "profile": "norte_temperado"}, # Piso base EUA
    "EU": {"idx": 120, "profile": "norte_temperado"}, # Piso base Europa
    "WORLD": {"idx": 100, "profile": "padrao"}
}

CITIES = {
    # --- CLUSTER: CAMA DE OURO (Hotelaria Discrepante) ---
    "lisboa": {"idx": 95, "profile": "norte_temperado", "modifiers": {"lodging": 1.4}}, # Comida barata, Hotel caro
    "amsterda": {"idx": 155, "profile": "norte_temperado", "modifiers": {"lodging": 1.3}},
    "nova york": {"idx": 190, "profile": "norte_temperado", "modifiers": {"lodging": 1.2}}, # Já é caro, hotel pune mais
    
    # --- CLUSTER: TARIFA DE LUXO (Transporte Caro) ---
    "londres": {"idx": 175, "profile": "norte_temperado", "modifiers": {"transport": 1.4}}, # Metrô muito caro
    "london": {"idx": 175, "profile": "norte_temperado", "modifiers": {"transport": 1.4}},

    # --- EUROPA PADRÃO ---
    "madrid": {"idx": 100, "profile": "norte_temperado"},
    "barcelona": {"idx": 112, "profile": "norte_temperado"},
    "porto": {"idx": 88, "profile": "norte_temperado"},
    "paris": {"idx": 160, "profile": "norte_temperado"},
    "roma": {"idx": 135, "profile": "norte_temperado", "modifiers": {"food": 0.9}}, # Comer bem é barato
    "veneza": {"idx": 160, "profile": "norte_temperado"},
    "zurique": {"idx": 200, "profile": "norte_temperado"},
    "santorini": {"idx": 140, "profile": "norte_temperado"},
    "istambul": {"idx": 85, "profile": "norte_temperado"},
    "praga": {"idx": 105, "profile": "norte_temperado"},
    "atenas": {"idx": 105, "profile": "norte_temperado"},

    # --- AMÉRICA DO NORTE ---
    "miami": {"idx": 155, "profile": "inverno_fugitivo"},
    "orlando": {"idx": 135, "profile": "inverno_fugitivo"},
    "las vegas": {"idx": 145, "profile": "norte_temperado"},
    "los angeles": {"idx": 160, "profile": "norte_temperado"},
    "cancun": {"idx": 120, "profile": "inverno_fugitivo"},
    "punta cana": {"idx": 125, "profile": "inverno_fugitivo"},
    "cidade do mexico": {"idx": 80, "profile": "sul_tropical"},

    # --- AMÉRICA DO SUL ---
    "buenos aires": {"idx": 95, "profile": "sul_tropical"}, # Ajustado para realidade 2025
    "santiago": {"idx": 115, "profile": "sul_tropical"},
    "mendoza": {"idx": 95, "profile": "sul_tropical"},
    "bariloche": {"idx": 120, "profile": "sul_frio"},
    "ushuaia": {"idx": 125, "profile": "sul_frio"},
    "cartagena": {"idx": 100, "profile": "sul_tropical"},
    "san pedro de atacama": {"idx": 130, "profile": "sul_tropical"},
    "montevideo": {"idx": 115, "profile": "sul_tropical"},

    # --- ÁSIA / OUTROS ---
    "dubai": {"idx": 140, "profile": "inverno_fugitivo"},
    "toquio": {"idx": 150, "profile": "norte_temperado"},
    "bangkok": {"idx": 75, "profile": "inverno_fugitivo"},
    "bali": {"idx": 70, "profile": "inverno_fugitivo"},
    "maldivas": {"idx": 185, "profile": "inverno_fugitivo"},
    "sidney": {"idx": 160, "profile": "sul_tropical"},
    "cidade do cabo": {"idx": 95, "profile": "sul_tropical"},

    # --- BRASIL ---
    "rio de janeiro": {"idx": 100, "profile": "sul_tropical"},
    "sao paulo": {"idx": 100, "profile": "sul_tropical"},
    "brasilia": {"idx": 100, "profile": "sul_tropical"},
    "salvador": {"idx": 90, "profile": "sul_tropical"},
    "recife": {"idx": 90, "profile": "sul_tropical"},
    "fortaleza": {"idx": 90, "profile": "sul_tropical"},
    "gramado": {"idx": 115, "profile": "sul_frio"},
    "trancoso": {"idx": 145, "profile": "sul_tropical"},
    "fernando de noronha": {"idx": 170, "profile": "sul_tropical"},
    "jericoacoara": {"idx": 110, "profile": "sul_tropical"},
    "pipa": {"idx": 110, "profile": "sul_tropical"},
    "buzios": {"idx": 125, "profile": "sul_tropical"},
    "maragogi": {"idx": 115, "profile": "sul_tropical"},
    "porto de galinhas": {"idx": 105, "profile": "sul_tropical"},
    "balneario camboriu": {"idx": 110, "profile": "sul_tropical"},
    "florianopolis": {"idx": 100, "profile": "sul_tropical"},
    "campos do jordao": {"idx": 120, "profile": "sul_frio"},
    "foz do iguacu": {"idx": 85, "profile": "sul_tropical"},
    "jalapao": {"idx": 95, "profile": "sul_tropical"},
    "lencois maranhenses": {"idx": 105, "profile": "sul_tropical"}
}
