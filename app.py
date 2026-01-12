import streamlit as st
import engine
from datetime import date, timedelta

# --- Configuração da Página ---
st.set_page_config(
    page_title="TakeItIz",
    page_icon="🧳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Mobile First (COM A CORREÇÃO DE TOPO) ---
st.markdown("""
    <style>
    /* Esconder menu hamburger e rodapé para parecer App nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* --- O SEGREDO DO TOPO --- */
    /* Isso remove a margem padrão gigante do Streamlit */
    .block-container {
        padding-top: 1.5rem !important; /* Puxa para cima */
        padding-bottom: 1rem !important;
    }
    
    /* Botões grandes para o dedo (Touch Friendly) */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    
    /* Ajustes finos nos inputs */
    .stTextInput, .stDateInput, .stSelectbox, .stSlider {
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
# Usando container para garantir alinhamento
with st.container():
    st.markdown("## TakeItIz 🧳") 
    st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
    st.caption("*(Estimativa de custos locais: Hospedagem, Alimentação e Transporte)*")
    st.write("---")

# --- Inputs Mobile ---

# 1. Destino
dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Londres...")

# 2. Datas (Fundamental para Sazonalidade)
travel_dates = st.date_input(
    "Qual o período?",
    value=(), # Começa vazio
    min_value=date.today(),
    help="Selecione a data de ida e a data de volta",
    format="DD/MM/YYYY"
)

# Lógica para calcular dias automaticamente
days_calc = 0
start_date = None

if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    delta = end_date - start_date
    days_calc = delta.days + 1 # Inclui o dia da volta
elif len(travel_dates) == 1:
    st.caption("👆 Selecione a data de volta no calendário.")

# 3. Viajantes e Moeda
col_viaj, col_moeda = st.columns(2)
with col_viaj:
    travelers = st.slider("Pessoas", 1, 5, 2)
with col_moeda:
    currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

# 4. Vibe
st.write("**Qual a sua Vibe?**")
style = st.select_slider(
    label="Vibe",
    options=["Econômico", "Moderado", "Conforto", "Luxo"],
    value="Moderado",
    label_visibility="collapsed"
)

st.write("") 

# --- Botão de Cálculo ---
if st.button("💰 Calcular Orçamento", type="primary"):
    
    # Validações
    if not dest:
        st.warning("Por favor, diga para onde você vai!")
    elif days_calc == 0:
        st.warning("Por favor, selecione as datas de Ida e Volta.")
    else:
        # --- O Motor Trabalhando ---
        with st.spinner(f'Consultando custos para {days_calc} dias em {dest}...'):
            # Chama engine
            total, breakdown, daily = engine.calculate_cost(dest, days_calc, travelers, style.lower(), currency)
            
        # --- O Resultado (Ticket) ---
        st.write("")
        
        # Container visual (Efeito Card)
        with st.container():
            st.markdown(f"### 🎫 Orçamento: {dest}")
            
            # Data formatada
            date_str = ""
            if start_date:
                date_str = f" • {start_date.strftime('%d/%m')}"
            
            st.caption(f"{days_calc} dias{date_str} • {travelers} pessoas • Vibe {style}")
            
            # Valor Total
            st.metric(label="Custo Estimado (Terrestre)", value=f"{currency} {total:,.2f}")
            
            st.write("---")
            
            # Breakdown
            c1, c2, c3 = st.columns(3)
            c1.metric("Hospedagem", f"{int(breakdown['accom'])}")
            c2.metric("Comida", f"{int(breakdown['food'])}")
            c3.metric("Transporte", f"{int(breakdown['transport'])}")
            
            st.caption(f"*Custo médio por pessoa/dia: {currency} {daily:,.2f}*")

        # --- Amenities ---
        st.write("---")
        st.subheader("💡 Explore sua Vibe")
        
        # Link Google Maps
        google_query = f"top attractions in {dest} {style} style"
        google_url = f"https://www.google.com/search?q={google_query.replace(' ', '+')}"
        
        st.markdown(f"""
        <a href="{google_url}" target="_blank">
            <button style="
                width: 100%;
                background-color: white;
                color: #1E88E5;
                border: 2px solid #1E88E5;
                padding: 10px;
                border-radius: 10px;
                cursor: pointer;
                font-weight: bold;">
                📍 Ver Atrações (Maps)
            </button>
        </a>
        """, unsafe_allow_html=True)
