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

# --- CONFIGURAÇÕES DO DOMÍNIO (NETLIFY) ---
DOMAIN_URL = "https://takeitiz.com.br"
ICON_URL = f"{DOMAIN_URL}/icon.png"

# --- FUNÇÕES UTILITÁRIAS ---
def format_brl(value, currency_symbol):
    val_str = f"{value:,.2f}"
    val_str = val_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{currency_symbol} {val_str}"

def setup_pwa():
    manifest = {
        "name": "TakeItIz",
        "short_name": "TakeItIz",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#FFFFFF",
        "theme_color": "#1E88E5",
        "icons": [{"src": ICON_URL, "sizes": "192x192", "type": "image/png"}]
    }
    manifest_json = json.dumps(manifest)
    b64_manifest = base64.b64encode(manifest_json.encode()).decode()
    data_url = f"data:application/manifest+json;base64,{b64_manifest}"

    meta_tags = f"""
    <head>
        <meta name="apple-mobile-web-app-title" content="TakeItIz">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <link rel="apple-touch-icon" href="{ICON_URL}">
        <link rel="icon" type="image/png" href="{ICON_URL}">
        <link rel="manifest" href="{data_url}">
    </head>
    """
    st.markdown(meta_tags, unsafe_allow_html=True)

setup_pwa()

# --- CSS REFINADO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem !important; padding-bottom: 3rem !important;}
    
    .stButton > button {
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;
        background-color: #1E88E5; color: white; border: none;
    }
    
    .amenity-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;
    }
    
    .amenity-btn {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 100%; height: 85px; padding: 5px; background-color: #FFFFFF; 
        color: #31333F !important; text-align: center; border-radius: 12px; 
        text-decoration: none !important; font-weight: 600; border: 1px solid #E0E0E0;
    }
    
    .price-hero {
        font-family: 'Roboto', sans-serif; font-size: 42px; font-weight: 800;
        color: #1E88E5; text-align: center; line-height: 1.0; margin-bottom: 5px;
    }
    .price-sub { font-size: 14px; color: #757575; text-align: center; margin-bottom: 20px; }
    
    /* Título com ícone alinhado */
    .brand-container { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
    .brand-title { font-size: 32px; font-weight: 900; color: #31333F; letter-spacing: -1px; }
    .brand-icon { width: 35px; height: 35px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image(ICON_URL, width=60)
    st.markdown("### TakeItIz")
    st.write("Compartilhe o App:")
    msg_encoded = "Olha%20esse%20app%20que%20calcula%20viagem:%20https://takeitiz.com.br"
    st.markdown(f'<a href="https://wa.me/?text={msg_encoded}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">📲 WhatsApp</div></a>', unsafe_allow_html=True)
    st.text_input("Link:", DOMAIN_URL, disabled=True)

# --- Cabeçalho (MALA AZUL OFICIAL) ---
st.markdown(f"""
    <div class="brand-container">
        <img src="{ICON_URL}" class="brand-icon">
        <div class="brand-title">TakeItIz</div>
    </div>
""", unsafe_allow_html=True)
st.markdown("**Quanto custa o seu próximo destino?**")
st.write("---")

# --- Inputs ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Gramado, Toquio...")
travel_dates = st.date_input("Qual o período?", value=[], min_value=date.today(), format="DD/MM/YYYY")

days_calc = 0
start_date = None
if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    days_calc = (end_date - start_date).days + 1
elif len(travel_dates) == 1:
    st.caption("📅 Selecione a data de volta.")

c_viaj, c_moeda = st.columns(2)
with c_viaj: travelers = st.slider("Pessoas", 1, 5, 2)
with c_moeda: currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

style = st.select_slider("Estilo", options=["Econômico", "Moderado", "Conforto", "Luxo"], value="Moderado")
vibe = st.selectbox("Vibe", ["Tourist Mix (Padrão)", "Cultura (Museus)", "Gastro (Comer bem)", "Natureza (Ar livre)", "Festa (Nightlife)", "Familiar (Relax)"])

vibe_map = {"Tourist Mix (Padrão)": "tourist_mix", "Cultura (Museus)": "cultura", "Gastro (Comer bem)": "gastro", "Natureza (Ar livre)": "natureza", "Festa (Nightlife)": "festa", "Familiar (Relax)": "familiar"}

# --- Cálculo ---
if st.button("💰 Calcular Orçamento", type="primary"):
    if not dest or days_calc == 0:
        st.error("⚠️ Preencha o destino e as datas!")
    else:
        with st.spinner('Calculando...'):
            res = engine.engine.calculate_cost(dest, days_calc, travelers, style.lower(), currency, vibe_map[vibe], start_date)
            
            st.success("✅ Orçamento pronto!")
            
            # --- Resultado ---
            st.markdown(f'<div class="price-hero">{format_brl(res["daily_avg"], currency)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="price-sub">por pessoa / dia<br>Total: {format_brl(res["total"], currency)}</div>', unsafe_allow_html=True)

            # --- SHARE TICKET (RECOLHIDO EM EXPANDER) ---
            with st.expander("📸 Gerar Resumo para Story"):
                ticket_img = share.TicketGenerator().create_ticket(dest, res['total'], res['daily_avg'], days_calc, vibe_map[vibe], currency)
                st.image(ticket_img, use_container_width=True)
                st.info("👆 Pressione e segure a imagem para salvar no seu iPhone/Android.")

            # --- BREAKDOWN ---
            with st.expander("📊 Detalhes do Custo"):
                bk = res['breakdown']
                c1, c2, c3 = st.columns(3)
                c1.metric("🏨 Hotel", f"{int(bk['lodging']):,}".replace(',','.'))
                c2.metric("🍽️ Comida", f"{int(bk['food']):,}".replace(',','.'))
                c3.metric("🚌 Lazer+", f"{int(bk['transport']+bk['activities']+bk['misc']):,}".replace(',','.'))

            # --- CURADORIA ---
            st.write("---")
            st.subheader(f"✨ Curadoria: {dest}")
            links = amenities.AmenitiesGenerator().generate_links(dest, vibe_map[vibe], style.lower(), start_date)
            
            html_grid = f"""
            <div class="amenity-grid">
                <a href="{links["flight"]}" target="_blank" class="amenity-btn"><span>✈️</span><span style="font-size:12px">{links["labels"]["flight_label"]}</span></a>
                <a href="{links["hotel"]}" target="_blank" class="amenity-btn"><span>🛏️</span><span style="font-size:12px">{links["labels"]["hotel_label"]}</span></a>
                <a href="{links["food"]}" target="_blank" class="amenity-btn"><span>🍽️</span><span style="font-size:12px">{links["labels"]["food_label"]}</span></a>
                <a href="{links["event"]}" target="_blank" class="amenity-btn"><span>📅</span><span style="font-size:12px">{links["labels"]["event_label"]}</span></a>
            </div>
            """
            st.markdown(html_grid, unsafe_allow_html=True)
