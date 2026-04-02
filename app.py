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
.stInfo { background-color: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; min-height: 250px; }
.stSuccess { background-color: rgba(0, 200, 83, 0.1) !important; border: 1px solid rgba(0, 200, 83, 0.3) !important; min-height: 280px; padding: 15px; border-radius: 10px; }
.stError { background-color: rgba(255, 75, 75, 0.1) !important; border: 1px solid rgba(255, 75, 75, 0.3) !important; min-height: 280px; padding: 15px; border-radius: 10px; }
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

# --- CÉREBRO JP: MOTOR DE ANÁLISE RECALIBRADO ---
def motor_de_analise_avancada(f_id, casa_nome, fora_nome):
    data = api_call("predictions", {"fixture": f_id})
    lineups = api_call("fixtures/lineups", {"fixture": f_id})
    if not data: return None
    
    p = data[0]
    comp = p['comparison']
    perc = p['predictions']['percent']
    
    win_c = float(perc['home'].replace('%',''))
    win_f = float(perc['away'].replace('%',''))
    empate = float(perc['draw'].replace('%',''))
    att_c = float(comp['att']['home'].replace('%',''))
    att_f = float(comp['att']['away'].replace('%',''))
    def_c = float(comp['def']['home'].replace('%',''))
    def_f = float(comp['def']['away'].replace('%',''))
    poisson_total = float(comp['poisson_distribution']['home'].replace('%','')) + float(comp['poisson_distribution']['away'].replace('%',''))
    
    pool = []
    
    # 1. RESULTADOS (Agora entende jogos equilibrados)
    if win_c >= 55: pool.append([f"Vitória: {casa_nome}", f"Favoritismo do mandante ({win_c}%).", 1.65, win_c])
    elif win_f >= 55: pool.append([f"Vitória: {fora_nome}", f"Visitante favorito ({win_f}%).", 1.75, win_f])
    
    if 40 <= win_c < 55: pool.append([f"Empate Anula: {casa_nome}", f"Jogo duro, mas mandante com ligeira vantagem ({win_c}%).", 1.40, win_c + 15])
    elif 40 <= win_f < 55: pool.append([f"Empate Anula: {fora_nome}", f"Visitante perigoso com proteção ({win_f}%).", 1.50, win_f + 15])
    
    # 2. GOLS (Métricas mais acessíveis)
    if poisson_total >= 55: pool.append(["Mais de 1.5 Gols", f"Tendência sólida para pelo menos 2 gols ({poisson_total:.1f}%).", 1.35, poisson_total + 10])
    if poisson_total >= 65: pool.append(["Mais de 2.5 Gols", f"Índice de gols muito alto ({poisson_total:.1f}%).", 1.80, poisson_total])
    if (att_c + att_f)/2 >= 55: pool.append(["Ambas Marcam: Sim", f"Produção ofensiva dos dois lados (Média: {(att_c + att_f)/2:.1f}%).", 1.75, (att_c + att_f)/2])
    
    # 3. CHUTES AO GOL
    if att_c >= 55: pool.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", f"Mandante com boa presença no ataque ({att_c}%).", 1.70, att_c])
    if att_f >= 55: pool.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", f"Visitante finaliza bem ({att_f}%).", 1.75, att_f])
    
    # 4. CARTÕES
    score_cartoes = (200 - (def_c + def_f)) / 2
    if score_cartoes >= 50: pool.append(["Mais de 4.5 Cartões", f"Defesas que costumam parar o jogo (Score: {score_cartoes:.1f}).", 1.65, score_cartoes])
    
    # 5. ESCANTEIOS
    if att_c >= 60: pool.append([f"Escanteios ({casa_nome}): Mais de 4.5", f"Time usa bastante as linhas de fundo.", 1.60, att_c])
    if att_c + att_f >= 110: pool.append(["Mais de 8.5 Escanteios na partida", f"Volume ofensivo alto gera cantos.", 1.75, (att_c+att_f)/2])
    
    # 6. JOGADOR
    if win_c >= 50 and att_c >= 60: pool.append([f"Atacante {casa_nome} (+1.5 Chutes)", f"Ataque vai depender do camisa 9.", 2.10, (win_c + att_c)/2])

    pool.sort(key=lambda x: x[3], reverse=True)
    return {"status": "✅ Oficial" if lineups else "⏳ Provável", "mercados": pool}

# --- FUNÇÃO HELPER ROBUSTA ---
def gerar_bilhetes_diversos(mercados_pool, cor_classe, titulo_prefixo):
    if not mercados_pool:
        st.warning(f"Aguardando mais dados para o {titulo_prefixo}.")
        return

    cols = st.columns(3)
    mercados_restantes = mercados_pool.copy()
    
    for i, col in enumerate(cols):
        # Garante que não vai pedir mais itens do que tem na lista
        max_itens = min(random.randint(3, 4), len(mercados_pool))
        if max_itens < 2: max_itens = len(mercados_pool)
        
        if len(mercados_restantes) >= max_itens:
            itens = random.sample(mercados_restantes, max_itens)
            for item in itens:
                if item in mercados_restantes:
                    mercados_restantes.remove(item)
        else:
            # Se faltar item único, pega da lista principal (permite leve repetição para não quebrar)
            itens = random.sample(mercados_pool, max_itens)
            
        odd_t = 1.0
        for x in itens: odd_t *= x[2]
        
        conteudo_bilhete = f"**{titulo_prefixo} {i+1}**\n\n**Odd: {odd_t:.2f}**\n\n"
        for x in itens:
            conteudo_bilhete += f"✅ **{x[0]}**\n_{x[1]}_\n\n"

        if cor_classe == "success": col.success(conteudo_bilhete)
        else: col.error(conteudo_bilhete)

# --- INTERFACE ---
tab_ia, tab_calc = st.tabs(["🧠 IA - Palpites Pro", "🧮 Calculadora"])

with tab_ia:
    st.title("JP Apostas Pro 🎯")
    
    data_sel = st.date_input("Data:", value=datetime.date.today()).strftime("%Y-%m-%d")
    jogos_dia = api_call("fixtures", {"date": data_sel, "timezone": "America/Sao_Paulo"})
    
    if jogos_dia:
        c1, c2, c3 = st.columns(3)
        modo = c1.radio("Busca:", ["Destaques", "Países/Ligas"])
        
        jogo_obj = None
        if modo == "Destaques":
            destaques = [f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" for j in jogos_dia if j['league']['country'] == "Brazil" or j['league']['name'] in ["Premier League", "Champions League", "La Liga"]]
            escolha = c2.selectbox("Principais Jogos:", ["Selecione..."] + sorted(destaques))
            for j in jogos_dia:
                if f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" == escolha:
                    jogo_obj = j
        else:
            paises = sorted(list(set([j['league']['country'] for j in jogos_dia])))
            p_sel = c2.selectbox("País:", paises)
            l_sel = c3.selectbox("Liga:", sorted(list(set([j['league']['name'] for j in jogos_dia if j['league']['country'] == p_sel]))))
            lista_f = {f"{j['teams']['home']['name']} x {j['teams']['away']['name']}": j for j in jogos_dia if j['league']['country'] == p_sel and j['league']['name'] == l_sel}
            j_nome = st.selectbox("Jogo:", ["Selecione..."] + list(lista_f.keys()))
            if j_nome != "Selecione...": jogo_obj = lista_f[j_nome]

        st.markdown("---")
        tipo_analise = st.radio(
            "O que a IA deve gerar?", 
            ["Entradas Simples (Top 3)", "Criar Aposta (6 Bilhetes)"], 
            horizontal=True
        )
        st.markdown("---")

        if st.button("🧠 PROCESSAR ANÁLISE", type="primary", use_container_width=True) and jogo_obj:
            with st.spinner("Analisando dados..."):
                intel = motor_de_analise_avancada(jogo_obj['fixture']['id'], jogo_obj['teams']['home']['name'], jogo_obj['teams']['away']['name'])
            
            # MUDANÇA AQUI: Agora aceita se tiver pelo menos 2 mercados, sem dar erro!
            if intel and len(intel['mercados']) >= 2:
                mercados = intel['mercados']
                
                if tipo_analise == "Entradas Simples (Top 3)":
                    st.subheader("🏆 Melhores Entradas Individuais")
                    cols = st.columns(3)
                    for i in range(min(3, len(mercados))):
                        m = mercados[i]
                        cols[i].metric(f"Confiança: {round(m[3], 1)}%", f"Odd {m[2]:.2f}")
                        cols[i].info(f"**{m[0]}**\n\n{m[1]}")
                
                else:
                    m_seguros = [x for x in mercados if x[3] >= 70]
                    m_ousados = [x for x in mercados if x[3] < 70]
                    
                    if len(m_seguros) < 3: m_seguros = mercados[:min(5, len(mercados))]
                    if len(m_ousados) < 3: m_ousados = mercados[max(0, len(mercados)-5):]

                    st.subheader("🛡️ BILHETES CONSERVADORES (Diferentes entre si)")
                    gerar_bilhetes_diversos(m_seguros, "success", "Bilhete Seguro")

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.subheader("🔥 BILHETES OUSADOS (Diferentes entre si)")
                    gerar_bilhetes_diversos(m_ousados, "error", "Bilhete Ousado")
            else:
                st.warning("Jogo com pouquíssimas informações na base de dados no momento.")

# --- ABA CALCULADORA ---
with tab_calc:
    st.header("🧮 Calculadora de Retorno")
    calc_modo = st.radio("Cálculo:", ["Simples", "Múltipla"], horizontal=True, key="calc_global")
    if calc_modo == "Simples":
        o = st.number_input("Odd:", 1.01, 100.0, 1.50)
        v = st.number_input("Valor:", 1.0, 10000.0, 10.0)
        if st.button("Calcular"): st.success(f"Retorno: R$ {o*v:.2f}")
    else:
        n = st.number_input("Seleções:", 2, 15, 3)
        total_o = 1.0
        for i in range(int(n)):
            total_o *= st.number_input(f"Odd {i+1}:", 1.01, 50.0, 1.50, key=f"calc_m_{i}")
        v_m = st.number_input("Valor Total:", 1.0, 10000.0, 10.0)
        if st.button("Calcular Múltipla"):
            st.warning(f"Odd Total: {total_o:.2f} | Retorno: R$ {total_o*v_m:.2f}")
