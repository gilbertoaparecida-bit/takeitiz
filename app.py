import streamlit as st
import engine
import amenities
import share
from datetime import date, timedelta

# --- Configuração da Página ---
st.set_page_config(
    page_title="TakeItIz | Planejador de Viagem",
    page_icon="🧳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CAPA SOCIAL (META TAGS) ---
def set_social_headers():
    meta_tags = """
    <head>
        <meta property="og:title" content="TakeItIz 🧳 - Quanto custa sua viagem?" />
        <meta property="og:description" content="Descubra o orçamento real com inteligência de dados." />
        <meta property="og:image" content="https://cdn-icons-png.flaticon.com/512/201/201623.png" />
    </head>
    """
    st.markdown(meta_tags, unsafe_allow_html=True)

set_social_headers()

# --- CSS ELEGANCE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1.5rem !important; padding-bottom: 3rem !important;}
    
    .stButton > button {width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;}
    
    div.css-1r6slb0 {background-color: #FFFFFF; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    
    /* BOTÕES GRID */
    .amenity-btn {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 100%; height: 100px; /* Altura fixa para alinhar */
        padding: 10px; background-color: #FFFFFF; color: #31333F !important;
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
            
            with st.expander("🔍 Auditoria do Cálculo"):
                for log in result['audit']:
                    icon = "✅" if log['status'] == "OK" else "⚠️"
                    st.text(f"{icon} [{log['src']}] {log['msg']}")

            # --- AMENITIES (NOVO GRID 2x2) ---
            st.write("---")
            st.subheader(f"✨ Curadoria: {dest}")
            
            gen = amenities.AmenitiesGenerator()
            links = gen.generate_links(
                destination=dest, vibe=vibe_key_map[vibe], 
                style=style.lower(), start_date=start_date
            )
            
            # Linha 1: Hotel e Comida
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.markdown(f"""
                <a href="{links['hotel']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🛏️</span>
                    <span class="amenity-text">{links['labels']['hotel_label']}</span>
                </a>""", unsafe_allow_html=True)
            with row1_col2:
                st.markdown(f"""
                <a href="{links['food']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🍽️</span>
                    <span class="amenity-text">{links['labels']['food_label']}</span>
                </a>""", unsafe_allow_html=True)
            
            # Linha 2: Agenda e Surpresa
            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                st.markdown(f"""
                <a href="{links['event']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">📅</span>
                    <span class="amenity-text">{links['labels']['event_label']}</span>
                </a>""", unsafe_allow_html=True)
            with row2_col2:
                st.markdown(f"""
                <a href="{links['surprise']}" target="_blank" class="amenity-btn">
                    <span class="amenity-icon">🎲</span>
                    <span class="amenity-text">{links['labels']['surprise_label']}</span>
                </a>""", unsafe_allow_html=True)
            
            # Linha 3: Mapa Full Width
            st.markdown(f"""
            <a href="{links['attr']}" target="_blank">
                <button style="width: 100%; background-color: white; color: #1E88E5; border: 2px solid #1E88E5; padding: 12px; border-radius: 12px; cursor: pointer; font-weight: bold; margin-top: 10px;">📍 Ver Mapa de Atrações</button>
            </a>""", unsafe_allow_html=True)
