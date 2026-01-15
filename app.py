import streamlit as st
import engine
import amenities
import share
from datetime import date
import base64

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Takeitiz",
    page_icon="icon.png", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ASSETS ---
DOMAIN = "https://takeitiz.com.br"
ICON_URL = f"{DOMAIN}/icon.png"

# --- CSS NUCLEAR (Clean UI & Branding) ---
st.markdown("""
    <style>
    /* 1. Esconder Header, Footer e Hamburger do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden; display: none !important;}
    .stDeployButton {display:none;}
    
    /* 2. Esconder Botão Fullscreen e Badges */
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    
    /* 3. Layout Mobile Otimizado */
    .block-container {
        padding-top: 1.5rem !important; 
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* 4. Estilo dos Botões de Monetização (Grid) */
    .monetize-grid {
        display: grid; 
        grid-template-columns: 1fr 1fr; 
        gap: 10px; 
        margin-top: 10px;
    }
    .monetize-btn {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 12px 5px;
        text-align: center;
        text-decoration: none !important;
        color: #31333F !important;
        transition: transform 0.1s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .monetize-btn:active { transform: scale(0.98); background-color: #F5F5F5; }
    .btn-icon { font-size: 24px; margin-bottom: 5px; }
    .btn-label { font-size: 13px; font-weight: 600; font-family: sans-serif; }
    
    /* 5. Preço Hero */
    .price-hero {
        font-family: 'Roboto', sans-serif; font-size: 46px; font-weight: 800;
        color: #1E88E5; text-align: center; line-height: 1.0; margin-top: 10px;
    }
    .price-sub { font-size: 14px; color: #757575; text-align: center; margin-bottom: 25px; }
    
    /* 6. Branding Header (Restaurado para Esquerda/Grande) */
    .brand-container { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
    .brand-title { font-size: 32px; font-weight: 900; color: #31333F; letter-spacing: -1px; }
    .brand-icon { width: 35px; height: 35px; border-radius: 6px; }
    
    /* 7. Aviso de Passagem */
    .flight-warning { font-size: 14px; color: #888; font-style: italic; margin-top: 0px; margin-bottom: 20px; }
    
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO (RESTAURADO) ---
st.markdown(f"""
    <div class="brand-container">
        <img src="{ICON_URL}" class="brand-icon">
        <div class="brand-title">Takeitiz</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
st.markdown('<p class="flight-warning">(não inclui passagens aéreas)</p>', unsafe_allow_html=True)
st.write("---")

# --- ESTADO E LÓGICA ---
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# --- FORMULÁRIO ---
dest = st.text_input("Para onde vamos?", placeholder="Ex: Paris, Orlando, Nordeste...")
travel_dates = st.date_input("Período da viagem", value=[], min_value=date.today(), format="DD/MM/YYYY")

days_calc = 0
start_date = None
if len(travel_dates) == 2:
    start_date, end_date = travel_dates
    days_calc = (end_date - start_date).days + 1
    if days_calc < 1: days_calc = 1

c1, c2 = st.columns(2)
with c1: travelers = st.slider("Pessoas", 1, 6, 2)
with c2: currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"])

style = st.select_slider("Estilo", options=["Econômico", "Moderado", "Conforto", "Luxo"], value="Moderado")
vibe_display = st.selectbox("Vibe da Viagem", 
    ["Tourist Mix (Clássico)", "Cultura (História/Arte)", "Gastro (Comer Bem)", 
     "Natureza (Relax/Trilhas)", "Festa (Vida Noturna)", "Familiar (Com Crianças)"])

vibe_map = {
    "Tourist Mix (Clássico)": "tourist_mix", "Cultura (História/Arte)": "cultura",
    "Gastro (Comer Bem)": "gastro", "Natureza (Relax/Trilhas)": "natureza",
    "Festa (Vida Noturna)": "festa", "Familiar (Com Crianças)": "familiar"
}

# --- BOTÃO DE AÇÃO ---
st.write("")
if st.button("💰 Calcular Investimento", type="primary", use_container_width=True):
    if not dest or days_calc == 0:
        st.warning("⚠️ Por favor, informe o destino e as datas (ida e volta).")
    else:
        with st.spinner('Consultando nossa base de dados...'):
            res = engine.engine.calculate_cost(dest, days_calc, travelers, style.lower(), currency, vibe_map[vibe_display], start_date)
            st.session_state.result = res
            st.session_state.calculated = True

# --- RESULTADO ---
if st.session_state.calculated:
    res = st.session_state.result
    
    # Flash Verde Restaurado
    st.success("✅ Orçamento pronto!")
    
    # 1. Big Number
    def fmt(v): return f"{currency} {v:,.2f}".replace(',','X').replace('.',',').replace('X','.')
    
    st.markdown(f'<div class="price-hero">{fmt(res["daily_avg"])}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="price-sub">por pessoa / dia<br><b>Total: {fmt(res["total"])}</b></div>', unsafe_allow_html=True)

    # 2. Ticket Download
    st.subheader("📸 Salvar Resumo")
    ticket_img = share.TicketGenerator().create_ticket(dest, res['total'], res['daily_avg'], days_calc, vibe_map[vibe_display], currency)
    
    st.download_button(
        label="💾 Baixar Imagem (Para Stories)",
        data=ticket_img,
        file_name=f"takeitiz_{dest}.png",
        mime="image/png",
        use_container_width=True
    )
    st.markdown('<p style="font-size:12px; color:#999; text-align:center;">Ao baixar, salve na galeria para postar.</p>', unsafe_allow_html=True)

    # 3. Breakdown
    with st.expander("📊 Ver detalhes dos gastos"):
        bk = res['breakdown']
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Hospedagem", fmt(bk['lodging']), delta_color="off")
        col_b.metric("Alimentação", fmt(bk['food']), delta_color="off")
        col_c.metric("Lazer/Transp.", fmt(bk['transport'] + bk['activities'] + bk['misc']), delta_color="off")

    # 4. Monetização (6 Botões Restaurados e Links com Data)
    st.write("---")
    st.subheader(f"✨ Curadoria: {dest}")
    
    # Passamos start_date e days_calc para gerar link com data
    data = amenities.AmenitiesGenerator().generate_links(dest, vibe_map[vibe_display], style.lower(), start_date, days_calc)
    L = data["links"]
    T = data["labels"]
    I = data["icons"]
    
    st.markdown(f"""
    <div class="monetize-grid">
        <a href="{L['flight']}" target="_blank" class="monetize-btn">
            <span class="btn-icon">{I['flight']}</span>
            <span class="btn-label">{T['flight']}</span>
        </a>
        <a href="{L['hotel']}" target="_blank" class="monetize-btn">
            <span class="btn-icon">{I['hotel']}</span>
            <span class="btn-label">{T['hotel']}</span>
        </a>
        <a href="{L['food']}" target="_blank" class="monetize-btn">
            <span class="btn-icon">{I['food']}</span>
            <span class="btn-label">{T['food']}</span>
        </a>
        <a href="{L['event']}" target="_blank" class="monetize-btn">
            <span class="btn-icon">{I['event']}</span>
            <span class="btn-label">{T['event']}</span>
        </a>
        <a href="{L['attr']}" target="_blank" class="monetize-btn">
            <span class="btn-icon">🎟️</span>
            <span class="btn-label">{T['attr']}</span>
        </a>
        <a href="{L['insurance']}" target="_blank" class="monetize-btn">
            <span class="btn-icon">{I['insurance']}</span>
            <span class="btn-label">{T['insurance']}</span>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # 5. Metodologia
    with st.expander("ℹ️ Metodologia"):
        st.markdown("""
        <div style="font-size: 13px; color: #555;">
        O <b>Takeitiz</b> utiliza um modelo híbrido de <b>Inteligência de Dados + Curadoria Humana</b>:<br><br>
        📊 <b>Índices Proprietários:</b> Nossa base é calibrada manualmente para refletir o comportamento do turista brasileiro, corrigindo distorções de plataformas automáticas.<br>
        🌎 <b>Poder de Compra Real:</b> Aplicamos algoritmos de paridade para que o custo reflita a realidade local, seja em Peso, Dólar ou Euro.<br>
        💱 <b>Câmbio Turismo:</b> Cotação atualizada em tempo real, considerando IOF e spread médio de mercado.<br>
        </div>
        """, unsafe_allow_html=True)
    
    # 6. Share Nativo (Movido para o final absoluto)
    st.divider()
    st.markdown(f"""
    <div style="text-align:center; margin-bottom: 20px;">
        <span style="font-size: 14px; font-weight: bold; color: #1E88E5;">Gostou do cálculo?</span><br>
        <a href="https://wa.me/?text=Acabei%20de%20calcular%20nossa%20viagem%20para%20{dest}%20no%20Takeitiz.%20Vai%20dar%20aprox.%20{fmt(res['daily_avg'])}%20por%20dia.%20Veja%20aqui:%20https://takeitiz.com.br" target="_blank" style="text-decoration:none; color: #25D366; font-weight:bold; font-size: 16px;">
           📲 Enviar no WhatsApp
        </a>
    </div>
    """, unsafe_allow_html=True)
