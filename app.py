# app.py
# TakeItIz | Anti-Advisor (Streamlit UI v18.1)
# FIX:
# 1. Corrected the broken Google Flights link. Now points to the official URL.

from __future__ import annotations
import datetime as dt
import pandas as pd
import streamlit as st
from engine import TakeItIzEngine
from urllib.parse import quote

st.set_page_config(page_title="TakeItIz", page_icon="🧳", layout="wide")

st.markdown("""
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
      .stDeployButton {display:none;}
      .tiz-box { border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.1); }
      .box-go { background-color: #d1fae5; border-color: #34d399; color: #064e3b; }
      .box-caution { background-color: #fef3c7; border-color: #fcd34d; color: #78350f; }
      .box-stop { background-color: #fee2e2; border-color: #fca5a5; color: #7f1d1d; }
    </style>
    """, unsafe_allow_html=True)

SYMBOL = {"BRL": "R$", "USD": "$", "EUR": "€", "GBP": "£"}
def fmt_money(n, ccy):
    s = f"{n:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{SYMBOL.get(ccy, ccy)} {s}"

# Inicializa motor
engine = TakeItIzEngine()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🗺️ Plano de Viagem")
    city = st.text_input("Destino", value="Recife")
    st.divider()
    today = dt.date.today()
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Ida", today + dt.timedelta(30), format="DD/MM/YYYY")
    end_date = c2.date_input("Volta", today + dt.timedelta(37), format="DD/MM/YYYY")
    travelers = st.number_input("Viajantes", 1, 10, 2)
    st.divider()
    currency = st.selectbox("Moeda", ["BRL", "USD", "EUR", "GBP"])
    budget = st.number_input(f"Budget Diário ({currency})", 200.0, 50000.0, 1500.0, step=100.0)
    style = st.select_slider("Estilo", ["Econômico", "Base", "Equilibrado", "Conforto", "Luxo"], value="Base")
    include_lodging = st.toggle("Incluir Hospedagem", value=True)
    st.divider()
    vibe = st.selectbox("Vibe", ["Mistão (Turista)", "Cultura & Museus", "Gastro & Cafés", "Natureza & Trilha", "Festa & Caos"])
    action = st.button("🚀 Analisar Agora", type="primary", use_container_width=True)

# --- MAIN ---
if not action:
    st.markdown("""<div style="text-align: center; margin-top: 50px;"><h1 style="font-size: 3em;">🧳 TakeItIz</h1><p style="color: grey;">Planejamento direto ao ponto.</p></div>""", unsafe_allow_html=True)
    st.info("👈 Configure sua viagem no menu lateral e clique em Analisar.")

else:
    if not city.strip(): st.stop()
    
    # --- FASE 1: CUSTOS ---
    try:
        with st.spinner(f"🛰️ Localizando {city}..."):
            geo = engine.geocode_city(city)
            if not geo["ok"]:
                st.error("Cidade não encontrada. Tente verificar a grafia.")
                st.stop()
            
            cost_data = engine.calculate_costs(city, geo["country_code"], start_date, end_date, travelers, include_lodging, style.lower(), vibe, currency, geo["lat"])
            est = cost_data["estimate"]
            
            # VEREDITO
            ratio = est / budget if budget > 0 else 999
            if ratio <= 0.9: cls, title = "box-go", "Sinal Verde! 🟢"
            elif ratio <= 1.1: cls, title = "box-caution", "Atenção (Amarelo) 🟡"
            else: cls, title = "box-stop", "Alerta Vermelho 🔴"
            
            msg = f"Estimativa: **{fmt_money(est, currency)}** vs Budget: **{fmt_money(budget, currency)}**"
            st.markdown(f"""<div class="tiz-box {cls}"><div style="font-weight:800; font-size:1.2rem;">{title}</div>{msg}</div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao calcular custos. Detalhes: {str(e)}")
        st.stop()

    # ABAS
    t1, t2, t3 = st.tabs(["💰 Bolso", "🗺️ Mapa", "📅 Smart Agenda"])

    # TAB 1: BOLSO
    with t1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Custo/Dia (Total)", fmt_money(est, currency))
        c2.metric("Faixa Provável", f"{fmt_money(cost_data['range_low'], currency)} - {fmt_money(cost_data['range_high'], currency)}")
        saldo = budget - est
        c3.metric("Saldo", fmt_money(abs(saldo), currency), delta=fmt_money(saldo, currency), delta_color="normal" if saldo >= 0 else "inverse")
        
        st.bar_chart(pd.DataFrame({"Valor": list(cost_data["breakdown"].values())}, index=[k.title() for k in cost_data["breakdown"].keys()]), color="#3b82f6")

    # TAB 2: MAPA
    with t2:
        map_container = st.empty()
        
        with st.status("📡 Escaneando a região...", expanded=True) as status:
            try:
                map_data = engine.fetch_map_data(geo["lat"], geo["lon"], vibe)
                
                if map_data["status"] == "ok" and map_data["items"]:
                    df_map = pd.DataFrame(map_data["items"])
                    def color_map(k): 
                        if k in ["bar", "nightclub"]: return "#ff4b4b" 
                        if k in ["park", "nature", "beach"]: return "#4ade80" 
                        return "#60a5fa"
                    df_map["color"] = df_map["kind"].apply(color_map)
                    
                    status.update(label="Mapa carregado!", state="complete", expanded=False)
                    map_container.map(df_map, latitude="lat", longitude="lon", color="color", size=20)
                    
                    st.dataframe(
                        df_map[["name", "kind", "maps_url"]],
                        column_config={
                            "name": "Local",
                            "kind": "Tipo",
                            "maps_url": st.column_config.LinkColumn("Link", display_text="Ver no Maps")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                
                elif map_data["status"] == "timeout":
                    status.update(label="Servidores de mapa ocupados.", state="complete")
                    st.warning("⚠️ Os servidores de mapa (OpenStreetMap) estão instáveis no momento. Tente novamente em alguns segundos.")
                
                else:
                    status.update(label="Nenhum local encontrado.", state="complete")
                    st.info(f"Não encontramos locais com a vibe '{vibe}' num raio de 12km. Tente a vibe 'Mistão'!")
            except Exception as e:
                status.update(label="Erro no mapa.", state="error")
                st.warning("Não foi possível carregar o mapa (Erro de conexão).")

    # TAB 3: SMART AGENDA (LINK CORRIGIDO)
    with t3:
        st.markdown(f"### O que rola em {city}?")
        q_city = quote(city)
        q_ev = quote(f"events in {city} {start_date.strftime('%B %Y')}")
        
        # LINK CORRIGIDO AQUI:
        link_flights = f"https://www.google.com/travel/flights?q={q_city}"
        
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("🎵 Shows (Songkick)", f"https://www.songkick.com/search?query={q_city}", use_container_width=True)
        with c2: st.link_button("📅 Eventos (Google)", f"https://www.google.com/search?q={q_ev}&ibp=htl;events", use_container_width=True)
        with c3: st.link_button("✈️ Voos (Google)", link_flights, use_container_width=True)

        holidays = engine.fetch_holidays(geo["country_code"], start_date, end_date)
        if holidays:
            st.markdown("---")
            st.caption("Feriados Locais:")
            st.dataframe(pd.DataFrame(holidays), hide_index=True)