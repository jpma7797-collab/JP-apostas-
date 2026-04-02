import streamlit as st
import datetime
import requests
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JP Apostas Pro", layout="wide", initial_sidebar_state="collapsed")

# --- SUA CHAVE DA API ---
CHAVE_API = "916bce9d916e28de163631b77d022cfc"

# --- CSS PREMIUM (VISUAL DE CASA DE APOSTAS) ---
st.markdown('''
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"], header, footer { display: none !important; }

.stApp {
    background-color: #0b0e14;
    background-image: radial-gradient(circle at top, #1a2130 0%, #0b0e14 100%);
    color: #ffffff;
}

.main .block-container { padding-top: 2rem; max-width: 95%; }

h1, h2, h3 { color: #ffffff !important; font-weight: 700 !important; }

.bet-card {
    background-color: #151923;
    border: 1px solid #242b3d;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    transition: transform 0.2s ease;
}
.bet-card:hover {
    transform: translateY(-2px);
    border-color: #38435f;
}

.bet-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #a0aec0;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 15px;
    border-bottom: 1px solid #242b3d;
    padding-bottom: 10px;
}

.odd-box {
    display: inline-block;
    background-color: #00e676;
    color: #000000;
    font-size: 1.3rem;
    font-weight: 800;
    padding: 8px 16px;
    border-radius: 6px;
    margin-bottom: 20px;
    box-shadow: 0 4px 10px rgba(0, 230, 118, 0.2);
}
.odd-box.ousado {
    background-color: #ff5252;
    box-shadow: 0 4px 10px rgba(255, 82, 82, 0.2);
    color: #ffffff;
}

.bet-item { margin-bottom: 15px; }
.bet-market {
    font-size: 1.05rem;
    font-weight: 600;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}
.bet-reason {
    font-size: 0.85rem;
    color: #718096;
    margin-top: 4px;
    padding-left: 28px;
    font-style: italic;
}
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

# --- CÉREBRO JP: LÓGICA E CATEGORIAS MANTIDAS ---
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
    
    # RESULTADOS (Categoria: 'resultado')
    if win_c >= 55: pool.append([f"Vitória: {casa_nome}", f"Favoritismo do mandante ({win_c}%).", 1.65, win_c, "resultado"])
    elif win_f >= 55: pool.append([f"Vitória: {fora_nome}", f"Visitante favorito ({win_f}%).", 1.75, win_f, "resultado"])
    elif 40 <= win_c < 55: pool.append([f"Empate Anula: {casa_nome}", f"Jogo duro, mas mandante com ligeira vantagem ({win_c}%).", 1.40, win_c + 15, "resultado"])
    elif 40 <= win_f < 55: pool.append([f"Empate Anula: {fora_nome}", f"Visitante perigoso com proteção ({win_f}%).", 1.50, win_f + 15, "resultado"])
    
    # GOLS (Categoria: 'gols')
    if poisson_total >= 65: 
        pool.append(["Mais de 2.5 Gols", f"Índice de gols muito alto ({poisson_total:.1f}%).", 1.80, poisson_total, "gols"])
    elif poisson_total >= 55: 
        pool.append(["Mais de 1.5 Gols", f"Tendência sólida para pelo menos 2 gols ({poisson_total:.1f}%).", 1.35, poisson_total + 10, "gols"])
        
    if (att_c + att_f)/2 >= 55: 
        pool.append(["Ambas Marcam: Sim", f"Produção ofensiva dos dois lados.", 1.75, (att_c + att_f)/2, "ambas"])
    
    # CHUTES AO GOL
    if att_c >= 55: pool.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", f"Mandante com boa presença no ataque.", 1.70, att_c, "chutes_casa"])
    if att_f >= 55: pool.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", f"Visitante finaliza bem.", 1.75, att_f, "chutes_fora"])
    
    # CARTÕES
    score_cartoes = (200 - (def_c + def_f)) / 2
    if score_cartoes >= 50: pool.append(["Mais de 4.5 Cartões", f"Defesas que costumam parar o jogo.", 1.65, score_cartoes, "cartoes"])
    
    # ESCANTEIOS
    if att_c + att_f >= 110: 
        pool.append(["Mais de 8.5 Escanteios na partida", f"Volume ofensivo alto gera cantos.", 1.75, (att_c+att_f)/2, "escanteios"])
    elif att_c >= 60: 
        pool.append([f"Escanteios ({casa_nome}): Mais de 4.5", f"Time usa bastante as linhas de fundo.", 1.60, att_c, "escanteios"])
    
    # JOGADOR
    if win_c >= 50 and att_c >= 60: pool.append([f"Atacante {casa_nome} (+1.5 Chutes)", f"Ataque vai depender do camisa 9.", 2.10, (win_c + att_c)/2, "jogador"])

    pool.sort(key=lambda x: x[3], reverse=True)
    return {"status": "✅ Oficial" if lineups else "⏳ Provável", "mercados": pool}

# --- FUNÇÃO HELPER COM HTML/CSS INJETADO SEM RECUOS PARA NÃO VAZAR ---
def gerar_bilhetes_diversos(mercados_pool, tipo_bilhete, titulo_prefixo):
    if not mercados_pool:
        st.warning(f"Aguardando mais dados precisos para gerar {titulo_prefixo}.")
        return

    bilhetes_gerados = []
    mercados_disponiveis = mercados_pool.copy()

    for i in range(3):
        if len(mercados_disponiveis) < 2: break 

        qtd_desejada = random.randint(2, 3)
        bilhete_atual = []
        categorias_usadas = set()
        itens_removidos_nesta_rodada = []

        random.shuffle(mercados_disponiveis)
        for m in mercados_disponiveis:
            categoria = m[4]
            if categoria not in categorias_usadas:
                bilhete_atual.append(m)
                categorias_usadas.add(categoria)
                itens_removidos_nesta_rodada.append(m)
            if len(bilhete_atual) == qtd_desejada: break
                
        if len(bilhete_atual) >= 2:
            bilhetes_gerados.append(bilhete_atual)
            for item in itens_removidos_nesta_rodada: mercados_disponiveis.remove(item)
        else: break

    if not bilhetes_gerados:
        st.warning(f"A IA utilizou os melhores mercados disponíveis e não há mais opções isoladas para formar múltiplos bilhetes aqui.")
        return

    cols = st.columns(len(bilhetes_gerados))
    for i, col in enumerate(cols):
        bilhete = bilhetes_gerados[i]
        odd_t = 1.0
        for x in bilhete: odd_t *= x[2]
        
        classe_odd = "ousado" if tipo_bilhete == "ousado" else ""
        icone_titulo = "🔥" if tipo_bilhete == "ousado" else "🛡️"
        
        # HTML todo em uma linha/sem recuos para o Streamlit não achar que é código Markdown
        html_card = f'<div class="bet-card"><div class="bet-title">{icone_titulo} {titulo_prefixo} {i+1}</div><div class="odd-box {classe_odd}">Odd: {odd_t:.2f}</div>'
        for x in bilhete:
            html_card += f'<div class="bet-item"><div class="bet-market">🎯 {x[0]}</div><div class="bet-reason">{x[1]}</div></div>'
        html_card += '</div>'
        
        col.markdown(html_card, unsafe_allow_html=True)

# --- INTERFACE PRINCIPAL ---
tab_ia, tab_calc = st.tabs(["🧠 Cérebro JP IA", "🧮 Calculadora de Lucro"])

with tab_ia:
    st.markdown("<h1>JP Apostas Pro <span style='color: #00e676;'>🎯</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; margin-bottom: 30px;'>Inteligência Artificial para análises e criação de bilhetes.</p>", unsafe_allow_html=True)
    
    data_sel = st.date_input("Data dos Jogos:", value=datetime.date.today()).strftime("%Y-%m-%d")
    jogos_dia = api_call("fixtures", {"date": data_sel, "timezone": "America/Sao_Paulo"})
    
    if jogos_dia:
        c1, c2, c3 = st.columns(3)
        modo = c1.radio("Modo de Busca:", ["Destaques", "Países/Ligas"])
        
        jogo_obj = None
        if modo == "Destaques":
            destaques = [f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" for j in jogos_dia if j['league']['country'] == "Brazil" or j['league']['name'] in ["Premier League", "Champions League", "La Liga"]]
            escolha = c2.selectbox("Principais Jogos:", ["Selecione..."] + sorted(destaques))
            for j in jogos_dia:
                if f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" == escolha:
                    jogo_obj = j
        else:
            paises = sorted(list(set([j['league']['country'] for j in jogos_dia])))
            p_sel = c2.selectbox("Filtrar por País:", paises)
            l_sel = c3.selectbox("Filtrar por Liga:", sorted(list(set([j['league']['name'] for j in jogos_dia if j['league']['country'] == p_sel]))))
            lista_f = {f"{j['teams']['home']['name']} x {j['teams']['away']['name']}": j for j in jogos_dia if j['league']['country'] == p_sel and j['league']['name'] == l_sel}
            j_nome = st.selectbox("Selecione a Partida:", ["Selecione..."] + list(lista_f.keys()))
            if j_nome != "Selecione...": jogo_obj = lista_f[j_nome]

        st.markdown("<br>", unsafe_allow_html=True)
        tipo_analise = st.radio("Estratégia da IA:", ["Entradas Simples (Top 3)", "Criar Aposta (Bilhetes Prontos)"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 PROCESSAR ANÁLISE COMPLETA", type="primary", use_container_width=True) and jogo_obj:
            with st.spinner("O Cérebro JP está cruzando os dados da partida..."):
                intel = motor_de_analise_avancada(jogo_obj['fixture']['id'], jogo_obj['teams']['home']['name'], jogo_obj['teams']['away']['name'])
            
            if intel and len(intel['mercados']) >= 2:
                mercados = intel['mercados']
                
                if tipo_analise == "Entradas Simples (Top 3)":
                    st.markdown("### 🏆 Melhores Entradas Individuais")
                    cols = st.columns(min(3, len(mercados)))
                    for i in range(min(3, len(mercados))):
                        m = mercados[i]
                        card_simples = f'<div class="bet-card"><div class="bet-title">Recomendação {i+1}</div><div class="odd-box">Odd: {m[2]:.2f}</div><div class="bet-item"><div class="bet-market">🎯 {m[0]}</div><div class="bet-reason">Confiança: {round(m[3], 1)}%<br>{m[1]}</div></div></div>'
                        cols[i].markdown(card_simples, unsafe_allow_html=True)
                
                else:
                    # SEPARAÇÃO ESTRITA: >= 65 é Seguro. Menos que 65 é Ousado. Sem copiar itens de um para o outro.
                    m_seguros = [x for x in mercados if x[3] >= 65]
                    m_ousados = [x for x in mercados if x[3] < 65]

                    st.markdown("### 🛡️ BILHETES CONSERVADORES")
                    gerar_bilhetes_diversos(m_seguros, "seguro", "Bilhete Seguro")

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown("### 🔥 BILHETES OUSADOS")
                    gerar_bilhetes_diversos(m_ousados, "ousado", "Bilhete Ousado")
            else:
                st.warning("Jogo com pouquíssimas informações na base de dados no momento.")

# --- ABA CALCULADORA ---
with tab_calc:
    st.markdown("### 🧮 Calculadora de Retorno")
    calc_modo = st.radio("Modo de Cálculo:", ["Aposta Simples", "Aposta Múltipla"], horizontal=True, key="calc_global")
    if calc_modo == "Aposta Simples":
        o = st.number_input("Sua Odd:", 1.01, 100.0, 1.50)
        v = st.number_input("Valor Apostado (R$):", 1.0, 10000.0, 10.0)
        if st.button("Calcular Lucro"): 
            st.markdown(f"<div class='odd-box'>Retorno Potencial: R$ {o*v:.2f}</div>", unsafe_allow_html=True)
    else:
        n = st.number_input("Quantidade de Seleções:", 2, 15, 3)
        total_o = 1.0
        for i in range(int(n)):
            total_o *= st.number_input(f"Odd da seleção {i+1}:", 1.01, 50.0, 1.50, key=f"calc_m_{i}")
        v_m = st.number_input("Valor Total Apostado (R$):", 1.0, 10000.0, 10.0)
        if st.button("Calcular Lucro da Múltipla"):
            st.markdown(f"<div class='odd-box'>Odd Final: {total_o:.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='odd-box ousado'>Retorno Potencial: R$ {total_o*v_m:.2f}</div>", unsafe_allow_html=True)
