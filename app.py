import streamlit as st
import engine
import amenities
from datetime import date

# --- Configuração da Página ---
st.set_page_config(
    page_title="TakeItIz",
    page_icon="🧳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Mobile First ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1.5rem !important; padding-bottom: 3rem !important;}
    
    /* Botões Padrão */
    .stButton > button {width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;}
    
    /* Cards de Resultado */
    div.css-1r6slb0 {background-color: #FFFFFF; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    
    /* Botões de Amenidades (Estilo Card) */
    .amenity-btn {
        display: inline-block;
        width: 100%;
        padding: 12px;
        background-color: #F0F2F6;
        color: #31333F;
        text-align: center;
        border-radius: 10px;
        text-decoration: none;
        font-weight: 600;
        border: 1px solid #E0E0E0;
        margin-bottom: 10px;
        transition: all 0.3s;
    }
    .amenity-btn:hover {
        background-color: #E8EAF0;
        border-color: #1E88E5;
        color: #1E88E5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
with st.container():
    st.markdown("## TakeItIz 🧳") 
    st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
    st.write("---")

# --- Inputs ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Nova York, Paris, Londres...")

travel_dates = st.date_input(
    "Qual o período?",
    value=(),
    min_value=date.today(),
    format="DD/MM/YYYY"
)

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
style = st.select_slider(
    label="Estilo",
    options=["Econômico", "Moderado", "Conforto", "Luxo"],
    value="Moderado",
    label_visibility="collapsed"
)

# --- Vibe Selector ---
st.write("**Qual a Vibe principal?**")
vibe = st.selectbox("Vibe", 
             ["Tourist Mix (Padrão)", "Cultura (Museus)", "Gastro (Comer bem)", "Natureza (Ar livre)", "Festa (Nightlife)", "Familiar (Relax)"],
             label_visibility="collapsed")

vibe_key_map = {
    "Tourist Mix (Padrão)": "tourist_mix",
    "Cultura (Museus)": "cultura",
    "Gastro (Comer bem)": "gastro",
    "Natureza (Ar livre)": "natureza",
    "Festa (Nightlife)": "festa",
    "Familiar (Relax)": "familiar"
}

st.write("") 

# --- Botão Calcular ---
if st.button("💰 Calcular Orçamento", type="primary"):
    if not dest:
        st.warning("Informe o destino!")
    elif days_calc == 0:
        st.warning("Selecione as datas.")
    else:
        with st.spinner('Consultando índices e câmbio atualizados...'):
            # Chamada ao Motor de Custo
            result = engine.engine.calculate_cost(
                destination=dest,
                days=days_calc,
                travelers=travelers,
                style=style.lower(),
                currency=currency,
                vibe=vibe_key_map[vibe],
                start_date=start_date
            )
            
            costs = result
            
        # --- Resultado ---
        st.write("")
        with st.container():
            st.markdown(f"### 🎫 Orçamento: {dest}")
            st.caption(f"{days_calc} dias • {travelers} pessoas • {style}")
            
            # Big Numbers
            total_fmt = f"{currency} {costs['total']:,.2f}"
            st.metric(label="Investimento Total Estimado", value=total_fmt)
            
            # Range
            r_low = costs['range'][0]
            r_high = costs['range'][1]
            st.caption(f"Faixa provável: {currency} {r_low:,.0f} - {currency} {r_high:,.0f}")
            
            # Por Pessoa
            daily_fmt = f"{currency} {costs['daily_avg']:,.2f}"
            st.info(f"💡 Custo médio por pessoa/dia: **{daily_fmt}**")
            
            st.markdown("---")
            
            # Breakdown
            bk = costs['breakdown']
            c1, c2, c3 = st.columns(3)
            c1.metric("🏨 Hotel", f"{int(bk['lodging']):,}")
            c2.metric("🍽️ Comida", f"{int(bk['food']):,}")
            c3.metric("🚌 Lazer", f"{int(bk['transport'] + bk['activities'] + bk['misc']):,}")
            
            # Auditoria
            with st.expander("🔍 Auditoria do Cálculo (Fontes & Índices)"):
                for log in result['audit']:
                    icon = "✅" if log['status'] == "OK" else "⚠️"
                    st.text(f"{icon} [{log['src']}] {log['msg']}")

            # --- AMENITIES (CURADORIA) ---
            st.write("---")
            st.subheader(f"✨ Curadoria Exclusiva: {dest}")
            st.caption("O melhor da cidade selecionado para o seu perfil.")
            
            # Gera os links inteligentes
            gen = amenities.AmenitiesGenerator()
            links = gen.generate_links(
                destination=dest, 
                vibe=vibe_key_map[vibe], 
                style=style.lower(), 
                start_date=start_date
            )
            
            # Layout dos Cards
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown(f"""
                <a href="{links['food']}" target="_blank" class="amenity-btn">
                    🍽️<br>{links['labels']['food_label']}
                </a>
                """, unsafe_allow_html=True)
                
            with col_b:
                st.markdown(f"""
                <a href="{links['event']}" target="_blank" class="amenity-btn">
                    📅<br>{links['labels']['event_label']}
                </a>
                """, unsafe_allow_html=True)
                
            with col_c:
                st.markdown(f"""
                <a href="{links['surprise']}" target="_blank" class="amenity-btn">
                    🎲<br>{links['labels']['surprise_label']}
                </a>
                """, unsafe_allow_html=True)
            
            # Botão Mapa Geral
            st.markdown(f"""
            <a href="{links['attr']}" target="_blank">
                <button style="
                    width: 100%;
                    background-color: white;
                    color: #1E88E5;
                    border: 2px solid #1E88E5;
                    padding: 12px;
                    border-radius: 12px;
                    cursor: pointer;
                    font-weight: bold;
                    margin-top: 10px;">
                    📍 Ver Mapa de Atrações ({style})
                </button>
            </a>
            """, unsafe_allow_html=True)
