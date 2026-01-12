import streamlit as st
import engine
import pandas as pd

# --- Configuração da Página (Mobile Friendly) ---
st.set_page_config(
    page_title="TakeItIz",
    page_icon="✈️",
    layout="centered", # 'Centered' fica melhor em celular que 'Wide'
    initial_sidebar_state="collapsed"
)

# --- CSS para Estilização Mobile ---
# Isso esconde o menu padrão e deixa os botões mais largos (touch friendly)
st.markdown("""
    <style>
    /* Esconder menu hamburger do Streamlit para parecer App nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo do Card de Resultado */
    div.css-1r6slb0.e1tzin5v2 {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Aumentar botões para o dedo */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho (Branding) ---
st.title("TakeItIz ✈️")
st.caption("Planejamento financeiro de viagens")
st.write("---")

# --- Inputs (A Zona do Dedão) ---
# Tudo vertical, sem colunas lado a lado que quebram no celular

col_dest, col_days = st.columns([2, 1]) 
with col_dest:
    dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Londres...")
with col_days:
    days = st.number_input("Dias", min_value=1, value=7)

# Usando colunas apenas para inputs pequenos ficarem alinhados
col_viaj, col_moeda = st.columns(2)
with col_viaj:
    travelers = st.slider("Pessoas", 1, 5, 2)
with col_moeda:
    currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

# Seleção de Vibe (Horizontal para fácil clique)
st.write("**Qual a sua Vibe?**")
style = st.select_slider(
    label="Vibe", # Label escondido pelo visual acima
    options=["Econômico", "Moderado", "Conforto", "Luxo"],
    value="Moderado",
    label_visibility="collapsed"
)

st.write("") # Espaço em branco
if st.button("💰 Calcular Orçamento", type="primary"):
    
    if not dest:
        st.warning("Por favor, digite um destino!")
    else:
        # --- O Motor Trabalhando ---
        with st.spinner(f'Calculando custos para {dest}...'):
            # Chama o motor antigo (engine.py) - Ele ainda funciona!
            total, breakdown, daily = engine.calculate_cost(dest, days, travelers, style.lower(), currency)
            
            # Ajuste técnico rápido para compatibilidade com o motor antigo
            # (O motor antigo retorna breakdown como dicionário simples)
            
        # --- O Resultado (Ticket Visual) ---
        st.write("")
        st.success("Cálculo realizado!")
        
        # Container = O "Cartão" visual
        with st.container():
            st.markdown(f"### 🎫 Seu Orçamento: {dest}")
            st.caption(f"{days} dias • {travelers} pessoas • Vibe {style}")
            
            # O "Big Number"
            st.metric(label="Custo Total Estimado", value=f"{currency} {total:,.2f}")
            
            st.write("---")
            
            # Detalhamento Simples
            st.markdown("**Onde você vai gastar:**")
            
            # Exibindo como progresso ou métricas simples
            c1, c2, c3 = st.columns(3)
            c1.metric("Hospedagem", f"{int(breakdown['accom'])}")
            c2.metric("Comida", f"{int(breakdown['food'])}")
            c3.metric("Transporte", f"{int(breakdown['transport'])}")
            
            st.caption("*Valores estimados. Não inclui passagens aéreas.*")

        # --- Amenities (Links Externos) ---
        st.write("---")
        st.subheader("💡 Explore sua Vibe")
        
        # Link inteligente para o Google
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
                📍 Ver Atrações no Google Maps
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # Link para Songkick (Exemplo)
        songkick_url = f"https://www.songkick.com/search?query={dest}"
        st.markdown(f"""
        <a href="{songkick_url}" target="_blank">
            <button style="
                width: 100%;
                background-color: white;
                color: #FF4B4B;
                border: 2px solid #FF4B4B;
                padding: 10px;
                border-radius: 10px;
                cursor: pointer;
                font-weight: bold;">
                🎸 Ver Shows e Eventos (Songkick)
            </button>
        </a>
        """, unsafe_allow_html=True)

