# database.py
# Base de Dados Unificada TakeItIz - Fase 3 (Recalibrada)
# Contém dados sanitizados com ajuste de paridade de poder de compra (PPP).

# PERFIS CLIMÁTICOS:
# 'sul_tropical': Alta em Dez/Jan/Fev (Praias BR, América do Sul)
# 'norte_temperado': Alta em Jul/Ago (EUA, Europa)
# 'inverno_fugitivo': Alta em Jan/Fev/Mar (Caribe, Dubai, Tailândia, Nordeste Top)
# 'sul_frio': Alta em Jun/Jul (Serras Brasileiras, Bariloche)

DEFAULTS = {
    "BR": {"idx": 85, "profile": "sul_tropical"},      # Brasil Genérico (Média ajustada)
    "US": {"idx": 140, "profile": "norte_temperado"},  # EUA Genérico
    "EU": {"idx": 120, "profile": "norte_temperado"},  # Europa Genérica
    "WORLD": {"idx": 100, "profile": "padrao"}         # Resto do Mundo
}

CITIES = {
    # --- EUROPA (Âncora: Madrid = 100) ---
    "madrid": {"idx": 100, "profile": "norte_temperado"},
    "barcelona": {"idx": 112, "profile": "norte_temperado"},
    "lisboa": {"idx": 95, "profile": "norte_temperado"},
    "porto": {"idx": 88, "profile": "norte_temperado"},
    "paris": {"idx": 160, "profile": "norte_temperado"},
    "londres": {"idx": 175, "profile": "norte_temperado"},
    "london": {"idx": 175, "profile": "norte_temperado"},
    "amsterda": {"idx": 155, "profile": "norte_temperado"},
    "roma": {"idx": 135, "profile": "norte_temperado"},
    "veneza": {"idx": 160, "profile": "norte_temperado"},
    "zurique": {"idx": 200, "profile": "norte_temperado"},
    "santorini": {"idx": 140, "profile": "norte_temperado"},
    "istambul": {"idx": 85, "profile": "norte_temperado"}, # Ajustado para realidade da Lira Turca
    "praga": {"idx": 105, "profile": "norte_temperado"},
    "atenas": {"idx": 105, "profile": "norte_temperado"},

    # --- AMÉRICA DO NORTE ---
    "nova york": {"idx": 190, "profile": "norte_temperado"},
    "miami": {"idx": 155, "profile": "inverno_fugitivo"},
    "orlando": {"idx": 135, "profile": "inverno_fugitivo"},
    "las vegas": {"idx": 145, "profile": "norte_temperado"},
    "los angeles": {"idx": 160, "profile": "norte_temperado"},
    "cancun": {"idx": 120, "profile": "inverno_fugitivo"},
    "punta cana": {"idx": 125, "profile": "inverno_fugitivo"},
    "cidade do mexico": {"idx": 80, "profile": "sul_tropical"},

    # --- AMÉRICA DO SUL ---
    "buenos aires": {"idx": 90, "profile": "sul_tropical"}, # Ajuste inflação/câmbio blue
    "santiago": {"idx": 115, "profile": "sul_tropical"},
    "mendoza": {"idx": 90, "profile": "sul_tropical"},
    "bariloche": {"idx": 120, "profile": "sul_frio"},
    "ushuaia": {"idx": 125, "profile": "sul_frio"},
    "cartagena": {"idx": 100, "profile": "sul_tropical"},
    "san pedro de atacama": {"idx": 130, "profile": "sul_tropical"},
    "montevideo": {"idx": 115, "profile": "sul_tropical"},

    # --- ÁSIA / ÁFRICA / OCEANIA ---
    "dubai": {"idx": 140, "profile": "inverno_fugitivo"},
    "toquio": {"idx": 150, "profile": "norte_temperado"},
    "bangkok": {"idx": 75, "profile": "inverno_fugitivo"}, # Custo baixo real
    "bali": {"idx": 70, "profile": "inverno_fugitivo"},
    "maldivas": {"idx": 185, "profile": "inverno_fugitivo"},
    "sidney": {"idx": 160, "profile": "sul_tropical"},
    "cidade do cabo": {"idx": 95, "profile": "sul_tropical"},

    # --- BRASIL (RECALIBRADO) ---
    # Capitais e Hubs (Teto ~100-105)
    "rio de janeiro": {"idx": 100, "profile": "sul_tropical"},
    "sao paulo": {"idx": 100, "profile": "sul_tropical"},
    "brasilia": {"idx": 100, "profile": "sul_tropical"},
    "salvador": {"idx": 90, "profile": "sul_tropical"},
    "recife": {"idx": 90, "profile": "sul_tropical"},
    "fortaleza": {"idx": 90, "profile": "sul_tropical"},
    "curitiba": {"idx": 90, "profile": "sul_tropical"},
    "belo horizonte": {"idx": 90, "profile": "sul_tropical"},
    "florianopolis": {"idx": 100, "profile": "sul_tropical"},
    "manaus": {"idx": 85, "profile": "sul_tropical"},
    "vitoria": {"idx": 90, "profile": "sul_tropical"},
    "goiania": {"idx": 85, "profile": "sul_tropical"},
    "belem": {"idx": 80, "profile": "sul_tropical"},

    # Elite / Exclusivos (Acima de 130)
    "fernando de noronha": {"idx": 170, "profile": "sul_tropical"}, # Mantido (Logística Ilha)
    "trancoso": {"idx": 145, "profile": "sul_tropical"}, # Leve ajuste
    "sao miguel dos milagres": {"idx": 130, "profile": "sul_tropical"},
    "caraiva": {"idx": 135, "profile": "sul_tropical"},
    "jurere internacional": {"idx": 130, "profile": "sul_tropical"},

    # Premium / Alta Procura (105-125)
    "gramado": {"idx": 115, "profile": "sul_frio"}, # Ajustado de 125
    "canela": {"idx": 110, "profile": "sul_frio"},
    "campos do jordao": {"idx": 120, "profile": "sul_frio"}, # Ajustado de 130
    "maragogi": {"idx": 115, "profile": "sul_tropical"}, # Ajustado de 125
    "jericoacoara": {"idx": 110, "profile": "sul_tropical"},
    "pipa": {"idx": 110, "profile": "sul_tropical"}, # Ajustado de 115
    "buzios": {"idx": 125, "profile": "sul_tropical"}, # Ajustado de 140
    "angra dos reis": {"idx": 120, "profile": "sul_tropical"},
    "bonito": {"idx": 110, "profile": "sul_tropical"},
    "alter do chao": {"idx": 95, "profile": "sul_tropical"},
    "lencois maranhenses": {"idx": 105, "profile": "sul_tropical"},
    "tief": {"idx": 105, "profile": "sul_tropical"},
    "morro de sao paulo": {"idx": 115, "profile": "sul_tropical"},
    "porto seguro": {"idx": 105, "profile": "sul_tropical"}, # Ajustado de 120
    "itacare": {"idx": 110, "profile": "sul_tropical"},
    "praia do forte": {"idx": 115, "profile": "sul_tropical"},
    "lencois": {"idx": 90, "profile": "sul_tropical"}, # Chapada Diamantina

    # Interior e Litoral Padrão (80-95) - A GRANDE CORREÇÃO
    "caldas novas": {"idx": 90, "profile": "sul_tropical"},
    "olimpia": {"idx": 90, "profile": "sul_tropical"},
    "cabo frio": {"idx": 95, "profile": "sul_tropical"},
    "ubatuba": {"idx": 95, "profile": "sul_tropical"},
    "maresias": {"idx": 105, "profile": "sul_tropical"}, # Litoral SP é caro
    "ilhabela": {"idx": 105, "profile": "sul_tropical"},
    "paraty": {"idx": 105, "profile": "sul_tropical"},
    "ouro preto": {"idx": 90, "profile": "sul_tropical"},
    "tiradentes": {"idx": 95, "profile": "sul_tropical"},
    "visconde de maua": {"idx": 100, "profile": "sul_frio"},
    "petropolis": {"idx": 100, "profile": "sul_frio"},
    "monte verde": {"idx": 105, "profile": "sul_frio"},
    "capitolio": {"idx": 90, "profile": "sul_tropical"},
    "jalapao": {"idx": 95, "profile": "sul_tropical"},
    "chapada dos veadeiros": {"idx": 90, "profile": "sul_tropical"},
    "foz do iguacu": {"idx": 85, "profile": "sul_tropical"},
    "natal": {"idx": 85, "profile": "sul_tropical"},
    "maceio": {"idx": 85, "profile": "sul_tropical"},
    "joao pessoa": {"idx": 80, "profile": "sul_tropical"},
    "porto de galinhas": {"idx": 105, "profile": "sul_tropical"},
    "balneario camboriu": {"idx": 110, "profile": "sul_tropical"},
    "bombinhas": {"idx": 105, "profile": "sul_tropical"},
}
