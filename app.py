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
    
    # Manifesto Android
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

    # HTML MINIFICADO (Sem indentação para evitar bugs visuais)
    meta_tags = f"""
<head>
<meta name="apple-mobile-web-app-title" content="TakeItIz">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="{APP_ICON_URL}">
<link rel="manifest" href="{data_url}">
</head>
    """
    st.markdown(meta_tags, unsafe_allow_html=True)

    # Instruções (Recolhido)
    with st.expander("📲 Instalar App (Tela Cheia)", expanded=False):
        st.caption("Devido à hospedagem gratuita, o ícone de instalação pode aparecer como 'Streamlit', mas o app funcionará normalmente.")
        col_ios, col_android = st.columns(2)
        with col_ios:
            st.markdown("**iPhone**")
            st.caption("1. Botão **Compartilhar**")
            st.caption("2. **Adicionar à Tela de Início**")
        with col_android:
            st.markdown("**Android**")
            st.caption("1. Menu **(3 pontos)**")
            st.caption("2. **Adicionar à Tela Inicial**")

# Executa
setup_pwa()

# --- CSS ELEGANCE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1.0rem !important; padding-bottom: 3rem !important;}
    
    .stButton > button {width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;}
    
    div.css-1r6slb0 {background-color: #FFFFFF; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    
    /* BOTÕES GRID */
    .amenity-btn {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 100%; height: 100px; padding: 10px; background-color: #FFFFFF; color: #31333F !important;
        text-align: center; border-radius: 12px; text-decoration: none !important;
        font-weight: 600; border: 1px solid #E0E0E0; margin-bottom: 0px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s ease-in-out;
    }
    .amenity-btn:hover, .amenity-btn:active {
        background-color: #F8F9FB; border-color: #1E88E5; color: #1E88E5 !important;
        transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .amenity-icon { font-size: 24px; margin-bottom: 5px; }
    .amenity-text { font-size: 13px; line-height: 1.2; }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
with st.container():
    st.markdown("## TakeItIz 🧳") 
    st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
    st.caption("*(não inclui passagens aéreas)*")
    st.write("---")

# --- Inputs ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Nova York, Paris, Londres...")

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

# --- ÁREA DE NOTIFICAÇÃO ---
msg_placeholder = st.empty() 

# --- Botão Calcular ---
if st.button("💰 Calcular Orçamento", type="primary"):
    
    if not dest:
        msg_placeholder.error("⚠️ Ei, faltou dizer o destino acima!")
        
    else:
        with st.spinner('Consultando índices e câmbio atualizados...'):
            result = engine.engine.calculate_cost(
                destination=dest, days=days_calc, travelers=travelers,
                style=style.lower(), currency=currency,
                vibe=vibe_key_map[vibe], start_date=start_date
            )
            costs = result
            
            msg_placeholder.success("✅ Orçamento pronto! Role para baixo 👇")
            
        # --- Resultado ---
        st.write("")
        with st.container():
            st.markdown(f"### 🎫 Orçamento: {dest}")
            st.caption(f"{days_calc} dias • {travelers} pessoas • {style}")
            
            total_fmt = f"{currency} {costs['total']:,.2f}"
            st.metric(label="Investimento Total Estimado", value=total_fmt)
            
            r_low, r_high = costs['range']
            st.caption(f"Faixa provável: {currency} {r_low:,.0f} - {r_high:,.0f}")
            
            daily_fmt = f"{currency} {costs['daily_avg']:,.2f}"
            st.info(f"💡 Custo médio por pessoa/dia: **{daily_fmt}**")
            
            # --- SHARE TICKET ---
            ticket_gen = share.TicketGenerator()
            ticket_img = ticket_gen.create_ticket(
                destination=dest, total_value=costs['total'], 
                daily_value=costs['daily_avg'], days=days_calc, 
                vibe=vibe_key_map[vibe], currency=currency
            )
            
            st.download_button(
                label="📸 Baixar Ticket Oficial",
                data=ticket_img,
                file_name=f"ticket_takeitiz_{dest}.png",
                mime="image/png",
                use_container_width=True
            )

            st.markdown("---")
            
            bk = costs['breakdown']
            c1, c2, c3 = st.columns(3)
            c1.metric("🏨 Hotel", f"{int(bk['lodging']):,}")
            c2.metric("🍽️ Comida", f"{int(bk['food']):,}")
            c3.metric("🚌 Lazer", f"{int(bk['transport'] + bk['activities'] + bk['misc']):,}")
            
            # --- CÁLCULOS: VARIÁVEIS ---
            with st.expander("ℹ️ Como chegamos neste valor?"):
                for log in result['audit']:
                    icon = "✅" if log['status'] == "OK" else "⚠️"
                    st.text(f"{icon} {log['msg']}")

            # --- AMENITIES (GRID OTIMIZADO) ---
            st.write("---")
            st.subheader(f"✨ Curadoria: {dest}")
            
            gen = amenities.AmenitiesGenerator()
            links = gen.generate_links(
                destination=dest, vibe=vibe_key_map[vibe], 
                style=style.lower(), start_date=start_date
            )
            
            # Linha 1: Logística
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.markdown(f"""
                <a href="{links['flight']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">✈️</span>
                    <span class="amenity-text">{links['labels']['flight_label']}</span>
                </a>""", unsafe_allow_html=True)
            with row1_col2:
                st.markdown(f"""
                <a href="{links['hotel']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🛏️</span>
                    <span class="amenity-text">{links['labels']['hotel_label']}</span>
                </a>""", unsafe_allow_html=True)
            
            # Linha 2: Experiência
            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                st.markdown(f"""
                <a href="{links['food']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🍽️</span>
                    <span class="amenity-text">{links['labels']['food_label']}</span>
                </a>""", unsafe_allow_html=True)
            with row2_col2:
                st.markdown(f"""
                <a href="{links['event']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">📅</span>
                    <span class="amenity-text">{links['labels']['event_label']}</span>
                </a>""", unsafe_allow_html=True)
            
            # Linha 3: Destaque
            st.markdown(f"""
            <a href="{links['surprise']}" target="_blank" class="amenity-btn">
                <span class="amenity-icon">🎲</span>
                <span class="amenity-text">{links['labels']['surprise_label']}</span>
            </a>""", unsafe_allow_html=True)

            # Mapa
            st.markdown(f"""
            <a href="{links['attr']}" target="_blank">
                <button style="width: 100%; background-color: white; color: #1E88E5; border: 2px solid #1E88E5; padding: 12px; border-radius: 12px; cursor: pointer; font-weight: bold; margin-top: 10px;">📍 Ver Mapa de Atrações</button>
            </a>""", unsafe_allow_html=True)
