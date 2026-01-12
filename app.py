import streamlit as st
import engine
from datetime import date, timedelta

# --- Configuração da Página ---
st.set_page_config(
    page_title="TakeItIz",
    page_icon="🧳",  # Mudança para Mala (Bagagem/Estadia)
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Mobile First ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    div.css-1r6slb0.e1tzin5v2 {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
col_logo, col_text = st.columns([1, 5])

# Título e Manchete
st.markdown("## TakeItIz 🧳") 
st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
st.caption("*(Estimativa de custos locais: Hospedagem, Alimentação e Transporte)*")
st.write("---")


# --- Inputs Mobile ---

# 1. Destino
dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Londres...")

# 2. Datas (Fundamental para Sazonalidade)
# O usuario seleciona um intervalo (Ida e Volta)
cols_date = st.columns(1)
travel_dates = st.date_input(
    "Qual o período?",
    value=(), # Começa vazio para forçar a escolha
    min_value=date.today(),
    help="Selecione a data de ida e a data de volta",
    format="DD/MM/YYYY"
)

# Lógica para calcular dias automaticamente baseada na escolha
days_calc = 0
start_date = None

if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    delta = end_date - start_date
    days_calc = delta.days + 1 # Inclui o dia da volta
elif len(travel_dates) == 1:
    st.caption("Seleccione também a data de volta no calendário.")

# 3. Viajantes e Moeda (Lado a lado para economizar espaço vertical)
col_viaj, col_moeda = st.columns(2)
with col_viaj:
    travelers = st.slider("Pessoas", 1, 5, 2)
with col_moeda:
    currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

# 4. Vibe (Slider)
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
    
    # Validações antes de chamar o motor
    if not dest:
        st.warning("Por favor, diga para onde você vai!")
    elif days_calc == 0:
        st.warning("Por favor, selecione as datas de Ida e Volta.")
    else:
        # --- O Motor Trabalhando ---
        with st.spinner(f'Consultando custos para {days_calc} dias em {dest}...'):
            
            # Aqui no futuro passaremos o 'start_date' para o engine calcular sazonalidade
            # Por enquanto, passamos a quantidade de dias calculada
            total, breakdown, daily = engine.calculate_cost(dest, days_calc, travelers, style.lower(), currency)
            
        # --- O Resultado (Ticket) ---
        st.write("")
        
        with st.container():
            st.markdown(f"### 🎫 Orçamento: {dest}")
            # Formatação de data bonita (Ex: 10/10 a 17/10)
            date_str = ""
            if start_date:
                date_str = f" • {start_date.strftime('%d/%m')}"
            
            st.caption(f"{days_calc} dias{date_str} • {travelers} pessoas • Vibe {style}")
            
            # Valor Total
            st.metric(label="Custo Estimado (Terrestre)", value=f"{currency} {total:,.2f}")
            
            st.write("---")
            
            # Breakdown Visual
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
