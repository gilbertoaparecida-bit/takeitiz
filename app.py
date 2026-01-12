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

# --- CSS Mobile First ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove margem do topo */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Botões grandes */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em; /* Um pouco mais alto */
        font-weight: bold;
        font-size: 16px;
    }
    
    /* Card de Resultado (Sombra mais suave e borda arredondada) */
    div.css-1r6slb0.e1tzin5v2, [data-testid="stVerticalBlock"] > [style*="background-color"] {
        background-color: #FFFFFF;
        border: 1px solid #F0F2F6;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Métricas centralizadas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Função Auxiliar de Formatação (R$) ---
def fmt_money(value, currency_symbol):
    return f"{currency_symbol} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Cabeçalho ---
with st.container():
    st.markdown("## TakeItIz 🧳") 
    st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
    st.caption("*(Estimativa de custos locais: Hospedagem, Alimentação e Transporte)*")
    st.write("---")

# --- Inputs ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Londres...")

travel_dates = st.date_input(
    "Qual o período?",
    value=(),
    min_value=date.today(),
    format="DD/MM/YYYY"
)

# Lógica de Dias
days_calc = 0
start_date = None
if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    delta = end_date - start_date
    days_calc = delta.days + 1
elif len(travel_dates) == 1:
    st.caption("👆 Selecione a data de volta.")

col_viaj, col_moeda = st.columns(2)
with col_viaj:
    travelers = st.slider("Pessoas", 1, 5, 2)
with col_moeda:
    currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])
    # Define simbolo visual
    curr_symbol = "R$" if currency == "BRL" else ("€" if currency == "EUR" else "US$")

st.write("**Qual a sua Vibe?**")
style = st.select_slider(
    label="Vibe",
    options=["Econômico", "Moderado", "Conforto", "Luxo"],
    value="Moderado",
    label_visibility="collapsed"
)

st.write("") 

# --- Botão ---
if st.button("💰 Calcular Orçamento", type="primary"):
    
    if not dest:
        st.warning("Diga o destino!")
    elif days_calc == 0:
        st.warning("Selecione as datas.")
    else:
        with st.spinner(f'Calculando...'):
            total, breakdown, daily = engine.calculate_cost(dest, days_calc, travelers, style.lower(), currency, start_date)
            
        # --- RESULTADO POLIDO ---
        st.write("")
        
        # Container com visual "Clean"
        with st.container():
            # Cabeçalho do Ticket
            st.markdown(f"### 🎫 Sua Viagem para {dest}")
            
            date_str = f"• {start_date.strftime('%d/%m')}" if start_date else ""
            st.caption(f"{days_calc} dias {date_str} • {travelers} pessoas • Vibe {style}")
            
            st.markdown("---")
            
            # O "Big Number" (Com formatação bonita)
            total_fmt = fmt_money(total, curr_symbol)
            st.metric(label="Investimento Total Estimado", value=total_fmt)
            
            # Custo por pessoa (O dado que acalma)
            daily_fmt = fmt_money(daily, curr_symbol)
            st.info(f"💡 **Isso dá {daily_fmt}** por pessoa/dia.")
            
            st.markdown("---")
            st.markdown("**Como esse dinheiro será gasto:**")
            
            # Breakdown com Ícones e Formatação
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("🏨 Hotel", fmt_money(breakdown['accom'], curr_symbol).split(" ")[1]) # Hack pra tirar o R$ e caber na tela
            with c2:
                st.metric("🍽️ Comida", fmt_money(breakdown['food'], curr_symbol).split(" ")[1])
            with c3:
                st.metric("🚌 Move", fmt_money(breakdown['transport'], curr_symbol).split(" ")[1])
            
            st.caption("*Valores aproximados para o total do grupo.*")

        # --- Amenities ---
        st.write("---")
        st.subheader("💡 Explore sua Vibe")
        
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
                border-radius: 12px;
                cursor: pointer;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                📍 Ver Atrações no Mapa
            </button>
        </a>
        """, unsafe_allow_html=True)
