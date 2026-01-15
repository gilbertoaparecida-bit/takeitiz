import streamlit as st
import engine
import amenities
import share
from datetime import date
import urllib.parse

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Takeitiz",
    page_icon="icon.png", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ASSETS ---
DOMAIN = "https://takeitiz.com.br"
ICON_URL = f"{DOMAIN}/icon.png"

# --- CSS ---
st.markdown("""
    <style>
    /* Ocultar Elementos Padrão */
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    [data-testid="stFooter"] {display: none !important;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden; display: none !important;}
    .stDeployButton {display:none;}
    
    /* Layout Mobile */
    .block-container {
        padding-top: 1.5rem !important; 
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Grid de Monetização */
    .monetize-grid {
        display: grid; 
        grid-template-columns: 1fr 1fr; 
        gap: 10px; 
        margin-top: 10px;
    }
    .monetize-btn {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 12px 5px;
        text-align: center;
        text-decoration: none !important;
        color: #31333F !important;
        transition: transform 0.1s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .monetize-btn:active { transform: scale(0.98); background-color: #F5F5F5; }
    .btn-icon { font-size: 24px; margin-bottom: 5px; }
    .btn-label { font-size: 13px; font-weight: 600; font-family: sans-serif; }
    
    /* Preço Hero */
    .price-hero {
        font-family: 'Roboto', sans-serif; font-size: 46px; font-weight: 800;
        color: #1E88E5; text-align: center; line-height: 1.0; margin-top: 10px;
    }
    .price-sub { font-size: 14px; color: #757575; text-align: center; margin-bottom: 25px; }
    
    /* Branding */
    .brand-container { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
    .brand-title { font-size: 32px; font-weight: 900; color: #31333F; letter-spacing: -1px; }
    .brand-icon { width: 35px; height: 35px; border-radius: 6px; }
    .flight-warning { font-size: 14px; color: #888; font-style: italic; margin-top: 0px; margin-bottom: 20px; }
    
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f"""
    <div class="brand-container">
        <img src="{ICON_URL}" class="brand-icon">
        <div class="brand-title">Takeitiz</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
st.markdown('<p class="flight-warning">(não inclui passagens aéreas)</p>', unsafe_allow_html=True)
st.write("---")

# --- ESTADO ---
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# --- INPUTS ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Orlando, Nordeste...")
travel_dates = st.date_input("Período da viagem", value=[], min_value=date.today(), format="DD/MM/YYYY")

days_calc = 0
start_date = None
if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    days_calc = (end_date - start_date).days + 1
    if days_calc < 1: days_calc = 1

c1, c2 = st.columns(2)
with c1: travelers = st.slider("Pessoas", 1, 6, 2)
with c2: currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

style = st.select_slider("Estilo", 
    options=["Econômico", "Moderado", "Conforto", "Luxo", "Super Luxo (Exclusivo)"], 
    value="Moderado")

vibe_display = st.selectbox("Vibe da Viagem", 
    ["Tourist Mix (Clássico)", "Cultura (História/Arte)", "Gastro (Comer Bem)", 
     "Natureza (Relax/Trilhas)", "Festa (Vida Noturna)", "Familiar (Com Crianças)", 
     "Business (A Trabalho)"])

vibe_map = {
    "Tourist Mix (Clássico)": "tourist_mix", "Cultura (História/Arte)": "cultura",
    "Gastro (Comer Bem)": "gastro", "Natureza (Relax/Trilhas)": "natureza",
    "Festa (Vida Noturna)": "festa", "Familiar (Com Crianças)": "familiar",
    "Business (A Trabalho)": "business"
}

# --- CÁLCULO ---
st.write("")
if st.button("💰 Calcular Investimento", type="primary", use_container_width=True):
    if not dest or days_calc == 0:
        st.warning("⚠️ Por favor, informe o destino e as datas (ida e volta).")
    else:
        with st.spinner('O Concierge está fazendo as contas...'):
            res = engine.engine.calculate_cost(dest, days_calc, travelers, style.lower(), currency, vibe_map[vibe_display], start_date)
            st.session_state.result = res
            st.session_state.calculated = True

# --- EXIBIÇÃO DO RESULTADO (SÓ APARECE SE CALCULAR) ---
if st.session_state.calculated:
    res = st.session_state.result
    st.success("✅ Orçamento pronto!")
    
    # 1. Valores
    def fmt(v): return f"{currency} {v:,.2f}".replace(',','X').replace('.',',').replace('X','.')
    st.markdown(f'<div class="price-hero">{fmt(res["daily_avg"])}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="price-sub">por pessoa / dia<br><b>Total: {fmt(res["total"])}</b></div>', unsafe_allow_html=True)

    # 2. Ticket
    with st.expander("📸 Baixar Resumo para Stories"):
        ticket_img = share.TicketGenerator().create_ticket(dest, res['total'], res['daily_avg'], days_calc, vibe_map[vibe_display], currency)
        st.download_button("💾 Download Imagem", ticket_img, file_name=f"takeitiz_{dest}.png", mime="image/png", use_container_width=True)

    # 3. Detalhes
    with st.expander("📊 Ver detalhes dos gastos"):
        bk = res['breakdown']
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Hospedagem", fmt(bk['lodging']), delta_color="off")
        col_b.metric("Alimentação", fmt(bk['food']), delta_color="off")
        col_c.metric("Lazer/Transp.", fmt(bk['transport'] + bk['activities'] + bk['misc']), delta_color="off")

    st.write("---")
    
    # 4. CONCIERGE PERSONALIZADO
    st.subheader("🛎️ Concierge Digital")
    
    # Concierge: Gastronomia removida pois já está fixa
    user_choices = st.multiselect(
        label=f"Além do básico, o que você quer curtir em {dest}?",
        options=["Compras", "Vida Noturna", "Arte & Cultura", "Natureza", "Agenda de Eventos", "Atrações/Coworking"],
        default=[] # Começa limpo pois os essenciais já estão lá
    )

    # Gerar Links com Vibe
    links_data = amenities.AmenitiesGenerator().generate_concierge_links(dest, style.lower(), start_date, days_calc, vibe_map[vibe_display])
    
    # Montagem do Grid
    html_buttons = ""
    
    # A. Botões Obrigatórios (Fixos)
    fixed_keys = ["flight", "hotel", "food", "insurance"]
    for key in fixed_keys:
        item = links_data[key]
        html_buttons += f'<a href="{item["url"]}" target="_blank" class="monetize-btn"><span class="btn-icon">{item["icon"]}</span><span class="btn-label">{item["label"]}</span></a>'
        
    # B. Botões Dinâmicos (Concierge)
    selection_map = {
        "Compras": "shopping",
        "Vida Noturna": "night",
        "Arte & Cultura": "culture",
        "Natureza": "nature",
        "Agenda de Eventos": "event",
        "Atrações/Coworking": "attr"
    }
    
    for choice in user_choices:
        key = selection_map.get(choice)
        if key and key in links_data:
            item = links_data[key]
            html_buttons += f'<a href="{item["url"]}" target="_blank" class="monetize-btn"><span class="btn-icon">{item["icon"]}</span><span class="btn-label">{item["label"]}</span></a>'

    # Renderização
    st.markdown(f'<div class="monetize-grid">{html_buttons}</div>', unsafe_allow_html=True)
    
    # 5. Metodologia
    with st.expander("ℹ️ Metodologia"):
        st.write("Cálculos baseados em dados proprietários calibrados manualmente para o perfil brasileiro.")

# --- RODAPÉ FIXO (FORA DO IF - SEMPRE VISÍVEL) ---
st.divider()

# Mensagem de Viralização para trazer novos usuários
msg_text = f"Descubra quanto custa sua próxima viagem em segundos! ✈️ Orçamento de voos, hotéis e lazer no Takeitiz. Acesse: {DOMAIN}"
msg_encoded = urllib.parse.quote(msg_text)

st.markdown(f"""
<div style="text-align:center; margin-bottom: 20px;">
    <a href="https://wa.me/?text={msg_encoded}" target="_blank" style="text-decoration:none; color: #25D366; font-weight:bold;">
       📲 Enviar no WhatsApp
    </a>
</div>
""", unsafe_allow_html=True)
