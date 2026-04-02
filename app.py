import streamlit as st
import datetime
import requests
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JP Apostas Pro", layout="wide", initial_sidebar_state="collapsed")

# --- SUA CHAVE DA API ---
CHAVE_API = "916bce9d916e28de163631b77d022cfc"

# --- CSS PERSONALIZADO ---
st.markdown('''
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
.stApp {
    background-image: linear-gradient(rgba(15, 20, 25, 0.95), rgba(15, 20, 25, 0.95)), url("https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070&auto=format&fit=crop");
    background-size: cover; background-position: center; background-attachment: fixed;
}
.main .block-container { padding-top: 1.5rem; max-width: 95%; }
.stMarkdown, .stText, h1, h2, h3, h4 { color: #ffffff !important; }
.stInfo { background-color: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; min-height: 150px; }
.stWarning { background-color: rgba(255, 204, 0, 0.05) !important; border: 1px solid rgba(255, 204, 0, 0.2) !important; min-height: 150px; }
.stSuccess { background-color: rgba(0, 200, 83, 0.08) !important; border: 1px solid rgba(0, 200, 83, 0.2) !important; min-height: 150px; }
.stError { background-color: rgba(255, 75, 75, 0.08) !important; border: 1px solid rgba(255, 75, 75, 0.2) !important; min-height: 150px; }
</style>
''', unsafe_allow_html=True)

# --- FUNÇÕES DE API ---
@st.cache_data(ttl=3600)
def api_call(endpoint, params):
    url = f"https://v3.football.api-sports.io/{endpoint}"
    headers = {'x-apisports-key': CHAVE_API}
    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('response', [])
    except: return []

# --- CÉREBRO JP: MOTOR DE ANÁLISE ---
def motor_de_analise_avancada(f_id, casa_nome, fora_nome):
    data = api_call("predictions", {"fixture": f_id})
    lineups = api_call("fixtures/lineups", {"fixture": f_id})
    if not data: return None
    
    p = data[0]
    comp = p['comparison']
    perc = p['predictions']['percent']
    
    # Extração de Dados
    win_c = float(perc['home'].replace('%',''))
    win_f = float(perc['away'].replace('%',''))
    poisson_c = float(comp['poisson_distribution']['home'].replace('%',''))
    poisson_f = float(comp['poisson_distribution']['away'].replace('%',''))
    att_c = float(comp['att']['home'].replace('%',''))
    att_f = float(comp['att']['away'].replace('%',''))
    
    pool_mercados = []
    
    # Lógica de Mercados
    if win_c > 50: pool_mercados.append([f"Vitória ou Empate: {casa_nome}", 1.35, "Seguro"])
    if win_f > 50: pool_mercados.append([f"Vitória ou Empate: {fora_nome}", 1.40, "Seguro"])
    if (poisson_c + poisson_f) > 60: pool_mercados.append(["Mais de 1.5 Gols", 1.30, "Seguro"])
    if att_c > 60: pool_mercados.append([f"Mais de 3.5 Cantos: {casa_nome}", 1.45, "Seguro"])
    
    pool_mercados.append([f"Vitória Seca: {casa_nome if win_c > win_f else fora_nome}", 2.10, "Ousado"])
    pool_mercados.append(["Ambas Marcam: Sim", 1.85, "Ousado"])
    pool_mercados.append(["Mais de 2.5 Gols", 1.90, "Ousado"])
    pool_mercados.append(["Mais de 9.5 Escanteios", 2.05, "Ousado"])
    pool_mercados.append(["Mais de 4.5 Cartões", 1.80, "Ousado"])

    return {"status": "✅ Oficial" if lineups else "⏳ Provável", "mercados": pool_mercados}

# --- INTERFACE ---
tab_ia, tab_calc = st.tabs(["🧠 IA - Palpites Pro", "🧮 Calculadora"])

with tab_ia:
    st.title("JP Apostas Pro 🎯")
    
    # FILTROS DE BUSCA
    data_sel = st.date_input("Data:", value=datetime.date.today()).strftime("%Y-%m-%d")
    jogos_dia = api_call("fixtures", {"date": data_sel, "timezone": "America/Sao_Paulo"})
    
    if jogos_dia:
        paises = sorted(list(set([j['league']['country'] for j in jogos_dia])))
        destaques = [f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" for j in jogos_dia if j['league']['country'] == "Brazil" or j['league']['name'] in ["Premier League", "Champions League", "La Liga"]]
        
        c1, c2, c3 = st.columns(3)
        modo = c1.radio("Busca:", ["Principais", "Países"])
        
        jogo_obj = None
        if modo == "Principais":
            escolha = c2.selectbox("Destaques:", ["Selecione..."] + sorted(destaques))
            for j in jogos_dia:
                if f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" == escolha:
                    jogo_obj = j
        else:
            p_sel = c2.selectbox("País:", paises)
            l_sel = c3.selectbox("Liga:", sorted(list(set([j['league']['name'] for j in jogos_dia if j['league']['country'] == p_sel]))))
            lista_f = {f"{j['teams']['home']['name']} x {j['teams']['away']['name']}": j for j in jogos_dia if j['league']['country'] == p_sel and j['league']['name'] == l_sel}
            j_nome = st.selectbox("Jogo:", ["Selecione..."] + list(lista_f.keys()))
            if j_nome != "Selecione...": jogo_obj = lista_f[j_nome]

        if st.button("🧠 GERAR BILHETES", type="primary", use_container_width=True) and jogo_obj:
            intel = motor_de_analise_avancada(jogo_obj['fixture']['id'], jogo_obj['teams']['home']['name'], jogo_obj['teams']['away']['name'])
            
            # --- OS 6 BILHETES ---
            seguros = [m for m in intel['mercados'] if m[2] == "Seguro"]
            ousados = [m for m in intel['mercados'] if m[2] == "Ousado"]
            
            st.subheader("🛡️ BILHETES SEGUROS (Alta Confiança)")
            col_s1, col_s2, col_s3 = st.columns(3)
            for i, col in enumerate([col_s1, col_s2, col_s3]):
                itens = random.sample(seguros, 2) if len(seguros) >= 2 else seguros
                odd_f = round(itens[0][1] * (itens[1][1] if len(itens)>1 else 1), 2)
                col.success(f"**Bilhete Seguro {i+1}**\n\nOdd: {odd_f}\n\n" + "\n".join([f"✅ {x[0]}" for x in itens]))

            st.subheader("🔥 BILHETES OUSADOS (Lucro Alto)")
            col_o1, col_o2, col_o3 = st.columns(3)
            for i, col in enumerate([col_o1, col_o2, col_o3]):
                itens = random.sample(ousados, 2) if len(ousados) >= 2 else ousados
                odd_f = round(itens[0][1] * (itens[1][1] if len(itens)>1 else 1), 2)
                col.error(f"**Bilhete Ousado {i+1}**\n\nOdd: {odd_f}\n\n" + "\n".join([f"⚡ {x[0]}" for x in itens]))

with tab_calc:
    tipo = st.radio("Cálculo:", ["Simples", "Múltipla"], horizontal=True, key="calc_tipo")
    if tipo == "Simples":
        o = st.number_input("Odd:", 1.01, 100.0, 1.50)
        v = st.number_input("Valor:", 1.0, 10000.0, 10.0)
        if st.button("Calcular"): st.info(f"Retorno: R$ {o*v:.2f}")
    else:
        n = st.number_input("Seleções:", 2, 10, 3)
        total_o = 1.0
        for i in range(int(n)):
            total_o *= st.number_input(f"Odd {i+1}:", 1.01, 50.0, 1.50, key=f"odd_m_{i}")
        v_m = st.number_input("Valor Total:", 1.0, 10000.0, 10.0, key="val_m")
        if st.button("Calcular Múltipla"):
            st.warning(f"Odd Total: {total_o:.2f} | Retorno: R$ {total_o*v_m:.2f}")
