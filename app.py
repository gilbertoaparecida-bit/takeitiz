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

# --- CSS REFINADO (GRID SYSTEM & TYPOGRAPHY) ---
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
    
    /* Card de Container Geral */
    div.css-1r6slb0 {
        background-color: #FFFFFF; border-radius: 15px; 
        padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* AMENITIES GRID BUTTONS */
    .amenity-btn {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 100%; height: 85px; /* Altura reduzida para mobile */
        padding: 8px; background-color: #FFFFFF; color: #31333F !important;
        text-align: center; border-radius: 12px; text-decoration: none !important;
        font-weight: 600; border: 1px solid #E0E0E0; 
        margin-bottom: 0px; /* Importante para o Grid */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease-in-out;
    }
    .amenity-btn:hover, .amenity-btn:active {
        background-color: #F0F7FF; border-color: #1E88E5; color: #1E88E5 !important;
        transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .amenity-icon { font-size: 22px; margin-bottom: 4px; }
    .amenity-text { font-size: 12px; line-height: 1.1; font-weight: 500; }
    
    /* Tipografia de Preço */
    .price-hero {
        font-family: 'Roboto', sans-serif; font-size: 42px; font-weight: 800;
        color: #1E88E5; text-align: center; line-height: 1.0; margin-bottom: 5px;
    }
    .price-sub {
        font-size: 14px; color: #757575; text-align: center; margin-bottom: 20px;
    }
    
    /* Titulo da Marca */
    .brand-title {
        font-size: 26px; font-weight: 900; color: #31333F; letter-spacing: -1px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
with st.container():
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.markdown('<div class="brand-title">TakeItIz 🧳</div>', unsafe_allow_html=True)
    st.caption("Planejamento financeiro de viagens baseado em dados.")
    st.write("---")

# --- Inputs ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Miami, Paris, Cancún...")

# Datas
today = date.today()
tomorrow = today + timedelta(days=1)
travel_dates = st.date_input("Qual o período?", value=(today, tomorrow), min_value=today, format="DD/MM/YYYY")

days_calc = 0
start_date = None
if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    delta = end_date - start_date
    days_calc = delta.days + 1

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
        msg_placeholder.error("⚠️ Ei, faltou dizer o destino acima!")
        
    else:
        with st.spinner('Consultando índices globais e câmbio...'):
            result = engine.engine.calculate_cost(
                destination=dest, days=days_calc, travelers=travelers,
                style=style.lower(), currency=currency,
                vibe=vibe_key_map[vibe], start_date=start_date
            )
            costs = result
            
            msg_placeholder.empty() # Limpa mensagem de loading
            
        # --- Resultado (NOVO LAYOUT) ---
        st.write("")
        with st.container():
            st.markdown(f"### 🎫 Orçamento: {dest}")
            st.caption(f"{days_calc} dias • {travelers} pessoas • {style}")
            
            # --- 1. PREÇO HERO (Por Pessoa/Dia) ---
            daily_fmt = f"{currency} {costs['daily_avg']:,.0f}"
            total_fmt = f"{currency} {costs['total']:,.2f}"
            
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
                c1.metric("🏨 Hotel", f"{int(bk['lodging']):,}")
                c2.metric("🍽️ Comida", f"{int(bk['food']):,}")
                c3.metric("🚌 Lazer", f"{int(bk['transport'] + bk['activities'] + bk['misc']):,}")
                
                st.divider()
                st.caption("ℹ️ Memória de Cálculo (Auditoria):")
                for log in result['audit']:
                    icon = "✅" if log['status'] == "OK" else "⚠️"
                    st.text(f"{icon} {log['msg']}")

            # --- AMENITIES (GRID LAYOUT) ---
            st.write("---")
            st.subheader(f"✨ Curadoria: {dest}")
            
            gen = amenities.AmenitiesGenerator()
            links = gen.generate_links(
                destination=dest, vibe=vibe_key_map[vibe], 
                style=style.lower(), start_date=start_date
            )
            
            # Grid 2x2 Manual com gap pequeno
            col1, col2 = st.columns(2, gap="small")
            
            with col1:
                st.markdown(f'<a href="{links["flight"]}" target="_blank" class="amenity-btn"><span class="amenity-icon">✈️</span><span class="amenity-text">{links["labels"]["flight_label"]}</span></a>', unsafe_allow_html=True)
                st.write("") # Spacer
                st.markdown(f'<a href="{links["food"]}" target="_blank" class="amenity-btn"><span class="amenity-icon">🍽️</span><span class="amenity-text">{links["labels"]["food_label"]}</span></a>', unsafe_allow_html=True)
                
            with col2:
                st.markdown(f'<a href="{links["hotel"]}" target="_blank" class="amenity-btn"><span class="amenity-icon">🛏️</span><span class="amenity-text">{links["labels"]["hotel_label"]}</span></a>', unsafe_allow_html=True)
                st.write("") # Spacer
                st.markdown(f'<a href="{links["event"]}" target="_blank" class="amenity-btn"><span class="amenity-icon">📅</span><span class="amenity-text">{links["labels"]["event_label"]}</span></a>', unsafe_allow_html=True)
            
            # Botões Largos (Full Width)
            st.write("")
            st.markdown(f'<a href="{links["surprise"]}" target="_blank" class="amenity-btn" style="height: auto; padding: 12px; background-color: #FFF3E0; border-color: #FFB74D;"><span class="amenity-icon">🎲</span><span class="amenity-text">{links["labels"]["surprise_label"]}</span></a>', unsafe_allow_html=True)

            st.markdown(f'<a href="{links["attr"]}" target="_blank"><button style="width: 100%; background-color: white; color: #1E88E5; border: 2px solid #1E88E5; padding: 12px; border-radius: 12px; cursor: pointer; font-weight: bold; margin-top: 15px;">📍 Ver Mapa de Atrações</button></a>', unsafe_allow_html=True)
