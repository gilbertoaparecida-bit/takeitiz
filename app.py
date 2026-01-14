import streamlit as st
import engine
import amenities
import share
from datetime import date, timedelta
import base64
import json

# --- Configuração da Página ---
st.set_page_config(
    page_title="Takeitiz",
    page_icon="icon.png", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURAÇÕES DO DOMÍNIO ---
DOMAIN_URL = "https://takeitiz.com.br"
ICON_URL = f"{DOMAIN_URL}/icon.png"

# --- FUNÇÕES UTILITÁRIAS ---
def format_brl(value, currency_symbol):
    val_str = f"{value:,.2f}"
    val_str = val_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{currency_symbol} {val_str}"

def setup_pwa():
    meta_tags = f"""
    <head>
        <link rel="apple-touch-icon" href="{ICON_URL}">
        <link rel="icon" type="image/png" href="{ICON_URL}">
    </head>
    """
    st.markdown(meta_tags, unsafe_allow_html=True)

setup_pwa()

# --- CSS REFINADO (REMOCÃO TOTAL DE RODAPÉS) ---
st.markdown("""
    <style>
    /* Ocultar Menu Hambúrguer e Rodapés */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden; display: none !important;}
    
    /* Ocultar Viewer Badge (Fullscreen Link) */
    .viewerBadge_container__1QSob {display: none !important;}
    div[data-testid="stDecoration"] {display: none;}
    a[href*="streamlit.app"] {display: none !important;}
    
    /* Ajuste de Padding */
    .block-container {padding-top: 1rem !important; padding-bottom: 3rem !important;}
    
    /* Botões */
    .stButton > button {
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold;
        background-color: #1E88E5; color: white; border: none;
    }
    
    /* Hero de Preço */
    .price-hero {
        font-family: 'Roboto', sans-serif; font-size: 42px; font-weight: 800;
        color: #1E88E5; text-align: center; line-height: 1.0; margin-bottom: 5px;
    }
    .price-sub { font-size: 14px; color: #757575; text-align: center; margin-bottom: 20px; }
    
    /* Branding */
    .brand-container { display: flex; align-items: center; gap: 10px; margin-bottom: 0px; }
    .brand-title { font-size: 32px; font-weight: 900; color: #31333F; letter-spacing: -1px; }
    .brand-icon { width: 35px; height: 35px; border-radius: 6px; }
    
    /* Grid de Amenities */
    .amenity-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;
    }
    .amenity-btn {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        width: 100%; height: 85px; padding: 5px; background-color: #FFFFFF; 
        color: #31333F !important; text-align: center; border-radius: 12px; 
        text-decoration: none !important; font-weight: 600; border: 1px solid #E0E0E0;
    }
    
    .flight-warning { font-size: 12px; color: #888; font-style: italic; margin-top: -5px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
st.markdown(f"""
    <div class="brand-container">
        <img src="{ICON_URL}" class="brand-icon">
        <div class="brand-title">Takeitiz</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("**Saiba quanto você vai gastar no destino escolhido.**")
st.markdown('<p class="flight-warning">(não inclui passagens aéreas)</p>', unsafe_allow_html=True)
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

            # --- TICKET DOWNLOAD (SIMPLIFICADO) ---
            st.markdown("### 📸 Salvar Resumo")
            
            # 1. Gera a imagem (Já vem em bytes do share.py)
            ticket_data = share.TicketGenerator().create_ticket(dest, res['total'], res['daily_avg'], days_calc, vibe_map[vibe], currency)
            
            # 2. Botão de Download Direto
            st.download_button(
                label="💾 Baixar Imagem do Ticket",
                data=ticket_data,  # Passamos direto, sem converter
                file_name=f"takeitiz_{dest}.png",
                mime="image/png",
                use_container_width=True
            )
            st.caption("Ao baixar, use a opção 'Salvar Imagem' do seu celular.")

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
            
            # --- METODOLOGIA ---
            with st.expander("ℹ️ Como funciona o cálculo?"):
                st.markdown("""
                <div style="font-size: 13px; color: #555;">
                O <b>Takeitiz</b> utiliza inteligência de dados para estimar seus gastos:
                <br><br>
                🌎 <b>Custo de Vida:</b> Baseado no banco de dados global <i>Numbeo</i>.<br>
                🍔 <b>Poder de Compra:</b> Ajustado pelo índice <i>Big Mac</i> e inflação local.<br>
                💱 <b>Câmbio:</b> Cotação atualizada em tempo real.<br><br>
                <i>Os valores são estimativas médias para auxiliar no planejamento financeiro.</i>
                </div>
                """, unsafe_allow_html=True)

# --- RODAPÉ COM SHARE ---
st.write("")
st.divider()
st.markdown(f"""
<div style="text-align:center; margin-bottom: 20px;">
    <span style="font-size: 14px; font-weight: bold; color: #1E88E5;">Gostou? Divulgue!</span><br>
    <a href="https://wa.me/?text=Olha%20esse%20app%20que%20calcula%20viagem:%20https://takeitiz.com.br" target="_blank" style="text-decoration:none; color: #25D366; font-weight:bold; font-size: 16px;">
       📲 Enviar no WhatsApp
    </a>
</div>
""", unsafe_allow_html=True)
