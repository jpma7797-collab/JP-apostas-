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
.stInfo { background-color: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; min-height: 180px; }
.stWarning { background-color: rgba(255, 204, 0, 0.05) !important; border: 1px solid rgba(255, 204, 0, 0.2) !important; min-height: 180px; }
.stSuccess { background-color: rgba(0, 200, 83, 0.08) !important; border: 1px solid rgba(0, 200, 83, 0.2) !important; min-height: 250px; }
.stError { background-color: rgba(255, 75, 75, 0.08) !important; border: 1px solid rgba(255, 75, 75, 0.2) !important; min-height: 250px; }
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

# --- CÉREBRO JP: O MOTOR AVANÇADO ORIGINAL ---
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
    poisson_c = float(comp['poisson_distribution']['home'].replace('%',''))
    poisson_f = float(comp['poisson_distribution']['away'].replace('%',''))
    poisson_total = poisson_c + poisson_f
    
    # ESTRUTURA: [Mercado, Justificativa, Odd Simulada, Score, Categoria]
    pool = []

    # 1. RESULTADO E HANDICAP
    if win_c > 60:
        pool.append([f"Vitória: {casa_nome}", "Domínio mandante.", 1.55, win_c, "Resultado"])
        pool.append([f"Handicap Asiático: {casa_nome} -1.0", "Margem segura.", 1.95, win_c + att_c, "Handicap"])
    elif win_f > 60:
        pool.append([f"Vitória: {fora_nome}", "Visitante favorito.", 1.65, win_f, "Resultado"])
    elif abs(win_c - win_f) <= 15:
        pool.append(["Empate no 1º Tempo", "Jogo estudado.", 2.10, empate + def_c + def_f, "HT"])

    # 2. GOLS
    if poisson_total > 65:
        pool.append(["Mais de 2.5 Gols", "Jogo aberto.", 1.70, poisson_total, "Gols"])
        pool.append(["Ambas Marcam: Sim", "Poder ofensivo.", 1.80, att_c + att_f, "BTTS"])
    elif poisson_total <= 45:
        pool.append(["Menos de 2.5 Gols", "Defesas fortes.", 1.60, 100 - poisson_total, "Gols"])

    # 3. CHUTES AO GOL E JOGADORES (AQUI VOLTAMOS COM TUDO!)
    if att_c + att_f > 115:
        pool.append(["Total de Chutes ao Gol: Mais de 8.5", "Alto volume ofensivo.", 1.80, att_c + att_f, "Chutes"])
    if att_c > 65:
        pool.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", "Média elite.", 1.75, att_c * 1.5, "Chutes"])
    if att_f > 65:
        pool.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", "Presença no ataque.", 1.85, att_f * 1.5, "Chutes"])
    
    # PROPS DE JOGADOR
    if win_c > 55 and att_c > 60:
        pool.append([f"Jogador: Atacante do {casa_nome} (+1.5 Chutes ao Gol)", "Mandante pressiona.", 2.10, att_c + win_c, "Jogador"])
    elif win_f > 55 and att_f > 60:
        pool.append([f"Jogador: Atacante do {fora_nome} (+1.5 Chutes ao Gol)", "Foco no centroavante.", 2.20, att_f + win_f, "Jogador"])

    # 4. IMPEDIMENTOS E FALTAS
    if att_c > 60 and def_f < 50:
        pool.append([f"Impedimentos ({casa_nome}): Mais de 1.5", "Bola em profundidade.", 1.65, att_c + (100 - def_f), "Impedimento"])
    if def_c < 45 or def_f < 45 or empate > 35:
        pool.append(["Total de Cartões: Mais de 4.5", "Faltas táticas.", 1.80, (100 - def_c) + (100 - def_f), "Cartoes"])
        pool.append(["Total de Faltas: Mais de 24.5", "Jogo truncado.", 1.85, empate * 2.5, "Faltas"])

    # 5. ESCANTEIOS
    if att_c > 75:
        pool.append([f"Escanteios ({casa_nome}): Mais de 5.5", "Pressão lateral.", 1.80, att_c * 1.6, "Cantos"])
    if att_c + att_f > 130:
        pool.append(["Escanteios Totais: Mais de 9.5", "Jogo pelas pontas.", 1.70, att_c + att_f, "Cantos"])

    # Remove duplicates and sort by confidence
    pool.sort(key=lambda x: x[3], reverse=True)
    return {"status": "✅ Oficial" if lineups else "⏳ Provável", "mercados": pool}

# --- INTERFACE PRINCIPAL ---
tab_ia, tab_calc = st.tabs(["🧠 IA - Palpites Pro", "🧮 Calculadora de Odds"])

# ==========================================
# ABA 1: INTELIGÊNCIA ARTIFICIAL
# ==========================================
with tab_ia:
    st.title("JP Apostas Pro 🎯")
    
    # FILTROS DE BUSCA (País -> Liga -> Jogo)
    data_sel = st.date_input("Data dos Jogos:", value=datetime.date.today()).strftime("%Y-%m-%d")
    jogos_dia = api_call("fixtures", {"date": data_sel, "timezone": "America/Sao_Paulo"})
    
    if jogos_dia:
        paises = sorted(list(set([j['league']['country'] for j in jogos_dia])))
        destaques = [f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" for j in jogos_dia if j['league']['country'] == "Brazil" or j['league']['name'] in ["Premier League", "Champions League", "La Liga"]]
        
        c1, c2, c3 = st.columns(3)
        modo = c1.radio("Buscar jogos por:", ["Principais do Dia", "Filtrar por País e Liga"])
        
        jogo_obj = None
        if modo == "Principais do Dia":
            escolha = c2.selectbox("Destaques:", ["Selecione..."] + sorted(destaques))
            for j in jogos_dia:
                if f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})" == escolha:
                    jogo_obj = j
        else:
            p_sel = c2.selectbox("1. Escolha o País:", paises)
            l_sel = c3.selectbox("2. Escolha o Campeonato:", sorted(list(set([j['league']['name'] for j in jogos_dia if j['league']['country'] == p_sel]))))
            lista_f = {f"{j['teams']['home']['name']} x {j['teams']['away']['name']}": j for j in jogos_dia if j['league']['country'] == p_sel and j['league']['name'] == l_sel}
            j_nome = st.selectbox("3. Selecione o Jogo:", ["Selecione..."] + list(lista_f.keys()))
            if j_nome != "Selecione...": jogo_obj = lista_f[j_nome]

        if st.button("🧠 PROCESSAR INTELIGÊNCIA ARTIFICIAL", type="primary", use_container_width=True) and jogo_obj:
            intel = motor_de_analise_avancada(jogo_obj['fixture']['id'], jogo_obj['teams']['home']['name'], jogo_obj['teams']['away']['name'])
            
            if intel and len(intel['mercados']) > 0:
                st.success(f"**Análise Completa:** {jogo_obj['teams']['home']['name']} vs {jogo_obj['teams']['away']['name']}")
                
                # SEPARAÇÃO DOS MERCADOS
                # Seguros: Odds baixas/médias e alto score
                seguros = [m for m in intel['mercados'] if m[2] <= 1.80]
                # Ousados: Chutes, Jogadores, Handicap e Odds mais altas
                ousados = [m for m in intel['mercados'] if m[4] in ["Chutes", "Jogador", "Handicap", "Faltas", "Impedimento"] or m[2] > 1.80]
                
                # Garante que tenha listas caso algum jogo tenha pouca info
                if len(seguros) < 3: seguros = intel['mercados']
                if len(ousados) < 3: ousados = intel['mercados']

                # OPÇÃO DE ESCOLHA (O QUE O USUÁRIO QUER VER)
                st.markdown("---")
                visao = st.radio(
                    "O que você deseja gerar para este jogo?", 
                    ["Melhores Entradas (Aposta Simples)", "Criar Aposta (6 Bilhetes Prontos)"], 
                    horizontal=True
                )
                st.markdown("---")
                
                if visao == "Melhores Entradas (Aposta Simples)":
                    st.subheader("🏆 Top 3 Entradas Individuais de Maior Valor")
                    cols_s = st.columns(3)
                    for i, col in enumerate(cols_s):
                        if i < len(intel['mercados']):
                            m = intel['mercados'][i]
                            col.metric(f"Confiança: {round(m[3], 1)}%", f"Odd {m[2]:.2f}")
                            col.info(f"**Mercado:** {m[0]}\n\n*{m[1]}*")
                            
                elif visao == "Criar Aposta (6 Bilhetes Prontos)":
                    # --- 3 BILHETES SEGUROS ---
                    st.subheader("🛡️ BILHETES CONSERVADORES (Alta Confiança)")
                    col_s1, col_s2, col_s3 = st.columns(3)
                    for i, col in enumerate([col_s1, col_s2, col_s3]):
                        # Pega de 3 a 4 seleções para cada bilhete múltiplo
                        qtd_selecoes = min(random.randint(3, 4), len(seguros))
                        itens = random.sample(seguros, qtd_selecoes)
                        
                        odd_f = 1.0
                        for x in itens: odd_f *= x[2]
                        
                        col.success(f"**Bilhete Seguro {i+1}**\n\n**Odd Total: {odd_f:.2f}**\n\n" + "\n\n".join([f"✅ {x[0]} (Odd {x[2]:.2f})" for x in itens]))

                    # --- 3 BILHETES OUSADOS ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("🔥 BILHETES OUSADOS (Estatísticas Avançadas / Lucro Alto)")
                    col_o1, col_o2, col_o3 = st.columns(3)
                    for i, col in enumerate([col_o1, col_o2, col_o3]):
                        # Pega de 3 a 4 seleções, garantindo que use os mercados avançados
                        qtd_selecoes = min(random.randint(3, 4), len(ousados))
                        itens = random.sample(ousados, qtd_selecoes)
                        
                        odd_f = 1.0
                        for x in itens: odd_f *= x[2]
                        
                        col.error(f"**Bilhete Ousado {i+1}**\n\n**Odd Total: {odd_f:.2f}**\n\n" + "\n\n".join([f"⚡ {x[0]} (Odd {x[2]:.2f})" for x in itens]))


# ==========================================
# ABA 2: CALCULADORA MANUAL
# ==========================================
with tab_calc:
    st.header("🧮 Simulador de Retornos Manual")
    
    tipo_calc = st.radio("Tipo de cálculo:", ["Aposta Simples", "Criar Múltipla"], horizontal=True, key="calc_tipo")
    
    if tipo_calc == "Aposta Simples":
        c1, c2 = st.columns(2)
        odd = c1.number_input("Odd:", min_value=1.01, value=1.50)
        valor = c2.number_input("Valor (R$):", min_value=1.0, value=10.0)
        if st.button("Calcular Ganho"):
            st.success(f"Retorno: R$ {odd * valor:.2f} | Lucro: R$ {(odd * valor) - valor:.2f}")
            
    else:
        qtd = st.number_input("Nº de seleções:", min_value=2, max_value=15, value=3)
        odds_lista = []
        cols = st.columns(3)
        for i in range(int(qtd)):
            with cols[i % 3]:
                o = st.number_input(f"Odd {i+1}:", min_value=1.01, value=1.50, key=f"odd_m_{i}")
                odds_lista.append(o)
        
        valor_m = st.number_input("Valor Total (R$):", min_value=1.0, value=10.0, key="val_m")
        if st.button("Calcular Múltipla"):
            total_odd = 1.0
            for x in odds_lista: total_odd *= x
            res = total_odd * valor_m
            st.warning(f"Odd Total: {total_odd:.2f}")
            st.success(f"Retorno: R$ {res:.2f} | Lucro: R$ {res - valor_m:.2f}")
