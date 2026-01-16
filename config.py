# config.py
# PAINEL DE CONTROLE DO TAKEITIZ
# Atualize este arquivo sempre que precisar mudar Cotações ou IDs de Parceiros.

# --- 1. CÂMBIO MANUAL (FALLBACK) ---
# Usado quando as APIs automáticas falham. 
# Atualize toda sexta-feira se desejar precisão máxima.
EXCHANGE_RATE_BRL_FALLBACK = 6.00  # Teto seguro para o Dólar
EXCHANGE_RATE_EUR_FALLBACK = 0.95  # Paridade Euro/Dólar (1 EUR = ~1.05 USD, invertido 0.95)

# --- 2. MONETIZAÇÃO (IDs de Afiliado) ---
# Deixe em branco ("") se não tiver o ID ainda. O sistema usará links padrão/Google.

# BOOKING.COM (Hospedagem)
# Seu AID (Affiliate ID). Ex: "1234567"
BOOKING_AID = "" 

# VIATOR (Passeios & Atrações)
# Seu PID (Partner ID). Ex: "P00012345"
VIATOR_PID = "" 
VIATOR_SUBID = "takeitiz_app" # Para você rastrear a origem no relatório deles

# SEGUROS PROMO (Seguro Viagem)
# Seu Código de Parceiro ou Link com parâmetros. 
# Se vazio, mantém busca no Google (melhor UX que link quebrado).
SEGUROS_PROMO_CODE = "" 

# SKYSCANNER / KAYAK (Voos)
# Como não temos a origem do usuário, mantemos Google Flights por padrão.
# Deixe vazio por enquanto.
FLIGHT_PARTNER_ID = ""
