import streamlit as st
import engine
import amenities
import share
from datetime import date, timedelta
import base64
import json

# --- Configuração da Página ---
st.set_page_config(
    page_title="TakeItIz",
    page_icon="🧳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- FUNÇÕES UTILITÁRIAS ---
def format_brl(value, currency_symbol):
    """Transforma 1200.50 em 1.200,50"""
    val_str = f"{value:,.2f}"
    val_str = val_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{currency_symbol} {val_str}"

# --- FUNÇÃO PWA (APP NATIVO) ---
def setup_pwa():
    APP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/201/201623.png"
    
    manifest = {
        "name": "TakeItIz",
        "short_name": "TakeItIz",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#FFFFFF",
        "theme_color": "#FFFFFF",
        "icons": [{"src": APP_ICON_URL, "sizes": "192x192", "type": "image/png"}]
    }
    manifest_json = json.dumps(manifest)
    b64_manifest = base64.b64encode(manifest_json.encode()).decode()
    data_url = f"data:application/manifest+json;base64,{b64_manifest}"

    meta_tags = f"""
    <head>
        <meta name="apple-mobile-web-app-title" content="TakeItIz">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <link rel="apple-touch-icon" href="{APP_ICON_URL}">
        <link rel="manifest" href="{data_url}">
        <style>
            @media all and (display-mode: standalone) {{
                #install-banner {{ display: none !important; }}
            }}
        </style>
    </head>
    """
    st.markdown(meta_tags, unsafe_allow_html=True)

    st.markdown("""
    <div id="install-banner" style="border: 1px solid #f0f2f6; border-radius: 10px; padding: 10px; margin-bottom: 20px; background-color: white;">
        <details>
            <summary style="cursor: pointer; font-weight: bold; color: #31333F;">📲 Instalar App (Tela Cheia)</summary>
            <div style="margin-top: 10px; font-size: 14px; color: #555;">
                <p>O app funcionará melhor se adicionado à tela de início.</p>
                <div style="display: flex; gap: 20px;">
                    <div><strong>iPhone:</strong> Compartilhar > Tela de Início</div>
                    <div><strong>Android:</strong> Menu > Instalar App</div>
                </div>
            </div>
        </details>
    </div>
    """, unsafe_allow_html=True)

setup_pwa()

# --- CSS REFINADO (GRID SYSTEM REAL & TYPOGRAPHY) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 0.5rem !important; padding-bottom: 3rem !important;}
    
    /* Botão Principal */
    .stButton > button {
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;
        background-color: #1E88E5; color: white; border: none;
    }
    .stButton > button:hover { background-color: #1565C0; }
    
    /* Container Geral */
    div.css-1r6slb0 {
        background-color: #FFFFFF; border-radius: 15px; 
        padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* GRID REAL PARA AMENITIES (Força 2 colunas no mobile) */
    .amenity-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 12px;
    }
    
    /* Botões do Grid */
    .amenity-btn {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 100%; height: 85px; 
        padding: 5px; background-color: #FFFFFF; color: #31333F !important;
        text-align: center; border-radius: 12px; text-decoration: none !important;
        font-weight: 600; border: 1px solid #E0E0E0; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease-in-out;
    }
    .amenity-btn:hover {
        background-color: #F0F7FF; border-color: #1E88E5; color: #1E88E5 !important;
        transform: translateY(-2px);
    }
    .amenity-icon { font-size: 24px; margin-bottom: 4px; }
    .amenity-text { font-size: 12px; line-height: 1.1; font-weight: 500; }
    
    /* Tipografia de Preço */
    .price-hero {
        font-family: 'Roboto', sans-serif; font-size: 42px; font-weight: 800;
        color: #1E88E5; text-align: center; line-height: 1.0; margin-bottom: 5px;
    }
    .price-sub {
        font-size: 14px; color: #757575; text-align: center; margin-bottom: 20px;
    }
    
    /* Titulo da Marca (Aumentado) */
    .brand-title {
        font-size: 32px; font-weight: 900; color: #31333F; letter-spacing: -1px; margin-bottom: 0px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
with st.container():
    c1, c2 = st.columns([0.85, 0.15])
    with c1:
        st.markdown('<div class="brand-title">TakeItIz 🧳</div>', unsafe_allow_html=True)
    
    st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
    st.caption("*(não inclui passagens aéreas)*")
    st.write("---")

# --- Inputs ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Miami, Paris, Cancún...")

# Datas
today = date.today()
# CORREÇÃO UX: Iniciar com value=[] força o modo de seleção limpo
travel_dates = st.date_input("Qual o período?", value=[], min_value=today, format="DD/MM/YYYY")

days_calc = 0
start_date = None

if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    delta = end_date - start_date
    days_calc = delta.days + 1
elif len(travel_dates) == 1:
    st.caption("📅 Selecione a data de volta para concluir o período.")

col_viaj, col_moeda = st.columns(2)
with col_viaj:
    travelers = st.slider("Pessoas", 1, 5, 2)
with col_moeda:
    currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

st.write("**Estilo da Viagem**")
style = st.select_slider("Estilo", options=["Econômico", "Moderado", "Conforto", "Luxo"], value="Moderado", label_visibility="collapsed")

st.write("**Qual a Vibe principal?**")
vibe_options = ["Tourist Mix (Padrão)", "Cultura (Museus)", "Gastro (Comer bem)", "Natureza (Ar livre)", "Festa (Nightlife)", "Familiar (Relax)"]
vibe = st.selectbox("Vibe", vibe_options, label_visibility="collapsed")

vibe_key_map = {
    "Tourist Mix (Padrão)": "tourist_mix", "Cultura (Museus)": "cultura",
    "Gastro (Comer bem)": "gastro", "Natureza (Ar livre)": "natureza",
    "Festa (Nightlife)": "festa", "Familiar (Relax)": "familiar"
}

st.write("") 
msg_placeholder = st.empty() 

# --- Botão Calcular ---
if st.button("💰 Calcular Orçamento", type="primary"):
    
    if not dest:
        msg_placeholder.error("⚠️ Ei, você esqueceu de incluir o destino!")
    elif days_calc == 0:
        msg_placeholder.error("⚠️ Selecione as datas de ida e volta.")
    else:
        with st.spinner('Consultando índices globais e câmbio...'):
            result = engine.engine.calculate_cost(
                destination=dest, days=days_calc, travelers=travelers,
                style=style.lower(), currency=currency,
                vibe=vibe_key_map[vibe], start_date=start_date
            )
            costs = result
            
            msg_placeholder.success("✅ Cálculo concluído. Role a página. 👇")
            
        # --- Resultado (NOVO LAYOUT) ---
        st.write("")
        with st.container():
            st.markdown(f"### 🎫 Orçamento: {dest}")
            st.caption(f"{days_calc} dias • {travelers} pessoas • {style}")
            
            # --- 1. PREÇO HERO (Por Pessoa/Dia) ---
            daily_fmt = format_brl(costs['daily_avg'], currency)
            total_fmt = format_brl(costs['total'], currency)
            
            st.markdown(f'<div class="price-hero">{daily_fmt}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="price-sub">por pessoa / dia<br>Total Estimado: {total_fmt}</div>', unsafe_allow_html=True)
            
            # --- SHARE TICKET ---
            ticket_gen = share.TicketGenerator()
            ticket_img = ticket_gen.create_ticket(
                destination=dest, total_value=costs['total'], 
                daily_value=costs['daily_avg'], days=days_calc, 
                vibe=vibe_key_map[vibe], currency=currency
            )
            
            st.download_button(
                label="📸 Baixar Ticket (Story)",
                data=ticket_img,
                file_name=f"takeitiz_{dest}.png",
                mime="image/png",
                use_container_width=True
            )

            # --- BREAKDOWN ---
            with st.expander("📊 Detalhes do Custo"):
                bk = costs['breakdown']
                c1, c2, c3 = st.columns(3)
                
                # Formatação simples para os cards pequenos
                h_val = f"{int(bk['lodging']):,}".replace(',', '.')
                f_val = f"{int(bk['food']):,}".replace(',', '.')
                l_val = f"{int(bk['transport'] + bk['activities'] + bk['misc']):,}".replace(',', '.')

                c1.metric("🏨 Hotel", h_val)
                c2.metric("🍽️ Comida", f_val)
                c3.metric("🚌 Lazer", l_val)
                
                st.divider()
                st.caption("ℹ️ Memória de Cálculo (Auditoria):")
                for log in result['audit']:
                    icon = "✅" if log['status'] == "OK" else "⚠️"
                    st.text(f"{icon} {log['msg']}")

            # --- AMENITIES (GRID LAYOUT HTML PURO) ---
            st.write("---")
            st.subheader(f"✨ Curadoria: {dest}")
            
            gen = amenities.AmenitiesGenerator()
            links = gen.generate_links(
                destination=dest, vibe=vibe_key_map[vibe], 
                style=style.lower(), start_date=start_date
            )
            
            # Grid Manual em HTML (Garante 2 colunas no Mobile)
            html_grid = f"""
            <div class="amenity-grid">
                <a href="{links["flight"]}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">✈️</span><span class="amenity-text">{links["labels"]["flight_label"]}</span>
                </a>
                <a href="{links["hotel"]}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🛏️</span><span class="amenity-text">{links["labels"]["hotel_label"]}</span>
                </a>
                <a href="{links["food"]}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🍽️</span><span class="amenity-text">{links["labels"]["food_label"]}</span>
                </a>
                <a href="{links["event"]}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">📅</span><span class="amenity-text">{links["labels"]["event_label"]}</span>
                </a>
            </div>
            
            <a href="{links["surprise"]}" target="_blank" class="amenity-btn" style="height: auto; padding: 12px; background-color: #FFF3E0; border-color: #FFB74D; margin-bottom: 15px;">
                <span class="amenity-icon">🎲</span><span class="amenity-text">{links["labels"]["surprise_label"]}</span>
            </a>

            <a href="{links["attr"]}" target="_blank">
                <button style="width: 100%; background-color: white; color: #1E88E5; border: 2px solid #1E88E5; padding: 12px; border-radius: 12px; cursor: pointer; font-weight: bold;">
                📍 Ver Mapa de Atrações
                </button>
            </a>
            """
            st.markdown(html_grid, unsafe_allow_html=True)
