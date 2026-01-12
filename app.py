import streamlit as st
import engine
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
    .stButton > button {width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;}
    div.css-1r6slb0 {background-color: #FFFFFF; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
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

# --- Vibe Selector (Novo UX) ---
st.write("**Qual a Vibe principal?**")
vibe = st.selectbox("Vibe", 
             ["Tourist Mix (Padrão)", "Cultura (Museus)", "Gastro (Comer bem)", "Natureza (Ar livre)", "Festa (Nightlife)", "Familiar (Relax)"],
             label_visibility="collapsed")
# Mapeia o label bonito para a chave do engine
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
            # Chamada Segura com Argumentos Nomeados
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
            
            # Range (Honestidade Intelectual)
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
            c3.metric("🚌 Lazer/Move", f"{int(bk['transport'] + bk['activities'] + bk['misc']):,}")
            
            # Auditoria (Transparência)
            with st.expander("🔍 Auditoria do Cálculo (Fontes & Índices)"):
                for log in result['audit']:
                    icon = "✅" if log['status'] == "OK" else "⚠️"
                    st.text(f"{icon} [{log['src']}] {log['msg']}")
