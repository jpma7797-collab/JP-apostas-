import streamlit as st
import datetime
import requests
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JP Apostas Pro", layout="wide", initial_sidebar_state="collapsed")

# --- SUA CHAVE DA API ---
CHAVE_API = "916bce9d916e28de163631b77d022cfc"

# --- CSS PERSONALIZADO (Ajustado para legibilidade) ---
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

# --- CÉREBRO JP: MOTOR DE ANÁLISE COMPLETO ---
def motor_de_analise_avancada(f_id, casa_nome, fora_nome):
    data = api_call("predictions", {"fixture": f_id})
    lineups = api_call("fixtures/lineups", {"fixture": f_id})
    if not data: return None
    
    p = data[0]
    comp = p['comparison']
    perc = p['predictions']['percent']
    
    win_c = float(perc['home'].replace('%',''))
    win_f = float(perc['away'].replace('%',''))
    att_c = float(comp['att']['home'].replace('%',''))
    att_f = float(comp['att']['away'].replace('%',''))
    def_c = float(comp['def']['home'].replace('%',''))
    def_f = float(comp['def']['away'].replace('%',''))
    poisson_total = float(comp['poisson_distribution']['home'].replace('%','')) + float(comp['poisson_distribution']['away'].replace('%',''))
    
    # ESTRUTURA: [Mercado, Justificativa, Odd Simulada, Score]
    pool = []
    # 1. RESULTADOS
    if win_c > 65: pool.append([f"Vitória: {casa_nome}", f"Dominância clara do mandante ({win_c}%).", 1.55, win_c])
    elif win_f > 65: pool.append([f"Vitória: {fora_nome}", f"Visitante amplamente favorito ({win_f}%).", 1.65, win_f])
    
    # 2. GOLS
    if poisson_total > 70:
        pool.append(["Mais de 2.5 Gols", f"Índice Poisson altíssimo ({poisson_total:.1f}%).", 1.75, poisson_total])
        pool.append(["Ambas Marcam: Sim", f"Poder ofensivo forte de ambos lados (Média: {(att_c + att_f)/2:.1f}%).", 1.80, (att_c + att_f)/2])
    
    # 3. CHUTES AO GOL
    if att_c > 75: pool.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", f"Mandante com alto volume de finalização ({att_c}%).", 1.85, att_c])
    if att_f > 75: pool.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", f"Visitante perigoso no contra-ataque ({att_f}%).", 1.90, att_f])
    
    # 4. CARTÕES
    score_cartoes = (200 - (def_c + def_f)) / 2
    if score_cartoes > 65:
        pool.append(["Mais de 4.5 Cartões", f"Defesas vulneráveis (Média Def.: {(def_c+def_f)/2:.1f}%), jogo deve ser faltoso.", 1.80, score_cartoes])
    
    # 5. ESCANTEIOS
    if att_c > 80: pool.append([f"Escanteios ({casa_nome}): Mais de 5.5", f"Pressão constante do mandante pelas pontas.", 1.70, att_c])
    
    # 6. JOGADOR (PROPS)
    if win_c > 60 and att_c > 70:
        pool.append([f"Atacante {casa_nome} (+1.5 Chutes)", f"Principal referência ofensiva em jogo de domínio.", 2.10, (win_c + att_c)/2])

    # Ordena por score de confiança
    pool.sort(key=lambda x: x[3], reverse=True)
    return {"status": "✅ Oficial" if lineups else "⏳ Provável", "mercados": pool}

# --- FUNÇÃO HELPER PARA GERAR BILHETES DIVERSOS ---
def gerar_bilhetes_diversos(mercados_pool, cor_classe, titulo_prefixo):
    cols = st.columns(3)
    mercados_restantes = mercados_pool.copy()
    
    for i, col in enumerate(cols):
        # Tenta pegar mercados diferentes para cada bilhete
        qtd = random.randint(3, 4)
        
        if len(mercados_restantes) >= qtd:
            itens = random.sample(mercados_restantes, qtd)
            # Remove os itens escolhidos para o próximo bilhete ser diferente
            for item in itens:
                if item in mercados_restantes:
                    mercados_restantes.remove(item)
        else:
            # Se acabarem os mercados únicos, completa com os melhores do pool original
            itens = mercados_restantes + random.sample(mercados_pool, min(qtd - len(mercados_restantes), len(mercados_pool)))
            
        odd_t = 1.0
        for x in itens: odd_t *= x[2]
        
        # Monta o conteúdo do bilhete com a justificativa de volta!
        conteudo_bilhete = f"**{titulo_prefixo} {i+1}**\n\n**Odd: {odd_t:.2f}**\n\n"
        for x in itens:
            conteudo_bilhete += f"✅ **{x[0]}**\n_{x[1]}_\n\n" # {x[1]} é a justificativa

        if cor_classe == "success":
            col.success(conteudo_bilhete)
        else:
            col.error(conteudo_bilhete)

# --- INTERFACE ---
tab_ia, tab_calc = st.tabs(["🧠 IA - Palpites Pro", "🧮 Calculadora"])

with tab_ia:
    st.title("JP Apostas Pro 🎯")
    
    # SELEÇÃO DO JOGO
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
            
            if intel and len(intel['mercados']) >= 4:
                mercados = intel['mercados']
                
                if tipo_analise == "Entradas Simples (Top 3)":
                    st.subheader("🏆 Melhores Entradas Individuais")
                    cols = st.columns(3)
                    for i in range(min(3, len(mercados))):
                        m = mercados[i]
                        cols[i].metric(f"Confiança: {round(m[3], 1)}%", f"Odd {m[2]:.2f}")
                        cols[i].info(f"**{m[0]}**\n\n{m[1]}")
                
                else:
                    # SEPARAÇÃO INTELIGENTE (Score >= 75 é seguro)
                    m_seguros = [x for x in mercados if x[3] >= 75]
                    m_ousados = [x for x in mercados if x[3] < 75]
                    
                    # Fallback garantindo pelo menos alguns mercados
                    if len(m_seguros) < 4: m_seguros = mercados[:min(5, len(mercados))]
                    if len(m_ousados) < 4: m_ousados = mercados[max(0, len(mercados)-5):]

                    st.subheader("🛡️ BILHETES CONSERVADORES (Diferentes entre si)")
                    gerar_bilhetes_diversos(m_seguros, "success", "Bilhete Seguro")

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.subheader("🔥 BILHETES OUSADOS (Diferentes entre si)")
                    gerar_bilhetes_diversos(m_ousados, "error", "Bilhete Ousado")
            else:
                st.warning("Dados insuficientes para este jogo gerar bilhetes variados.")

# --- ABA CALCULADORA (MANTIDA IGUAL) ---
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
