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
.stInfo { background-color: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; min-height: 200px; }
.stWarning { background-color: rgba(255, 204, 0, 0.05) !important; border: 1px solid rgba(255, 204, 0, 0.2) !important; min-height: 200px; }
.stSuccess { background-color: rgba(0, 200, 83, 0.08) !important; border: 1px solid rgba(0, 200, 83, 0.2) !important; min-height: 200px; }
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

# --- CÉREBRO JP: SCANNER DE MERCADOS AVANÇADOS ---
def motor_de_analise_avancada(f_id, casa_nome, fora_nome):
    data = api_call("predictions", {"fixture": f_id})
    lineups = api_call("fixtures/lineups", {"fixture": f_id})
    if not data: return None
    
    p = data[0]
    comp = p['comparison']
    perc = p['predictions']['percent']
    
    # EXTRAÇÃO DE DADOS BRUTOS
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
    
    # ESTRUTURA: [Mercado, Justificativa, Odd Simulada, Score (Confiança), Categoria]
    pool_mercados = []

    # ==========================================
    # 1. MERCADOS DE RESULTADO (MATCH ODDS)
    # ==========================================
    if win_c > 60:
        pool_mercados.append([f"Vitória: {casa_nome}", f"Dominância de {win_c}% baseada no histórico recente.", 1.55, win_c, "Resultado"])
        pool_mercados.append([f"Handicap Asiático: {casa_nome} -1.0", "Projeção de vitória por margem segura.", 1.95, win_c + att_c, "Handicap"])
    elif win_f > 60:
        pool_mercados.append([f"Vitória: {fora_nome}", f"Visitante amplamente favorito ({win_f}%).", 1.65, win_f, "Resultado"])
        pool_mercados.append([f"Handicap Asiático: {fora_nome} -1.0", "Diferença técnica justifica handicap negativo.", 2.05, win_f + att_f, "Handicap"])
    elif abs(win_c - win_f) <= 15:
        pool_mercados.append(["Empate no 1º Tempo", "Equilíbrio absoluto. Jogo deve começar estudado.", 2.10, empate + def_c + def_f, "HT"])
        pool_mercados.append(["Margem de Vitória: 1 Gol (Qualquer Time)", "Confronto muito parelho, decidido no detalhe.", 2.25, empate * 2, "Especiais"])

    # ==========================================
    # 2. MERCADOS DE GOLS (COM EXCLUSIVIDADE)
    # ==========================================
    if poisson_total > 65:
        pool_mercados.append(["Mais de 2.5 Gols", f"Índice Poisson altíssimo ({poisson_total}%). Tendência de jogo aberto.", 1.70, poisson_total, "Gols"])
        pool_mercados.append(["Ambas Marcam: Sim", "Poder ofensivo forte de ambos os lados.", 1.80, att_c + att_f, "BTTS"])
        pool_mercados.append(["Gol no 1º Tempo: Mais de 0.5", "Estatísticas indicam pressão inicial.", 1.40, (att_c + att_f) * 0.8, "Gols_HT"])
    elif poisson_total <= 45:
        pool_mercados.append(["Menos de 2.5 Gols", "Sistemas defensivos superam os ataques.", 1.60, 100 - poisson_total, "Gols"])
        pool_mercados.append(["Ambas Marcam: Não", "Cenário favorável para ao menos um time passar em branco.", 1.85, def_c + def_f, "BTTS"])

    # ==========================================
    # 3. ESTATÍSTICAS AVANÇADAS: CHUTES AO GOL
    # ==========================================
    # Total de Chutes
    if att_c + att_f > 115:
        pool_mercados.append(["Total de Chutes ao Gol: Mais de 8.5", "Ambos os times possuem alto volume de finalização.", 1.80, att_c + att_f, "Chutes_Totais"])
    elif def_c + def_f > 130:
        pool_mercados.append(["Total de Chutes ao Gol: Menos de 7.5", "Marcação forte deve bloquear a maioria das finalizações.", 1.75, def_c + def_f, "Chutes_Totais"])

    # Chutes por Time
    if att_c > 65:
        pool_mercados.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", f"Média ofensiva do mandante é elite ({att_c}%).", 1.75, att_c * 1.5, "Chutes_Time"])
    if att_f > 65:
        pool_mercados.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", "Visitante tem forte presença no terço final.", 1.85, att_f * 1.5, "Chutes_Time"])

    # Prop de Jogador (Chutes)
    if win_c > 55 and att_c > 60:
        pool_mercados.append([f"Jogador: Principal Atacante do {casa_nome} (+1.5 Chutes ao Gol)", "Domínio do mandante fará a bola chegar no centroavante.", 2.10, att_c + win_c, "Jogador"])
    elif win_f > 55 and att_f > 60:
        pool_mercados.append([f"Jogador: Principal Atacante do {fora_nome} (+1.5 Chutes ao Gol)", "Transição ofensiva focada no homem de referência.", 2.20, att_f + win_f, "Jogador"])

    # ==========================================
    # 4. IMPEDIMENTOS E FALTAS
    # ==========================================
    # Impedimentos
    if att_c > 60 and def_f < 50:
        pool_mercados.append([f"Impedimentos ({casa_nome}): Mais de 1.5", "Mandante joga em profundidade contra linha alta.", 1.65, att_c + (100 - def_f), "Impedimento"])
    if att_f > 55: # Visitante jogando no contra-ataque gera impedimento
        pool_mercados.append([f"Impedimentos ({fora_nome}): Mais de 1.5", "Estratégia de bola longa do visitante deve forçar linhas.", 1.75, att_f * 1.2, "Impedimento"])
    
    # Faltas e Cartões
    if def_c < 45 or def_f < 45 or empate > 35:
        pool_mercados.append(["Total de Cartões: Mais de 4.5", "Defesas vulneráveis precisarão recorrer a faltas táticas.", 1.80, (100 - def_c) + (100 - def_f), "Cartoes"])
        pool_mercados.append(["Total de Faltas: Mais de 24.5", "Jogo de muito contato físico e transições interrompidas.", 1.85, empate * 2.5, "Faltas"])

    # ==========================================
    # 5. ESCANTEIOS (CANTOS)
    # ==========================================
    if att_c > 75:
        pool_mercados.append([f"Escanteios ({casa_nome}): Mais de 5.5", "Pressão lateral constante do mandante gera cantos.", 1.80, att_c * 1.6, "Cantos_Time"])
    if att_c + att_f > 130:
        pool_mercados.append(["Escanteios Totais: Mais de 9.5", "Jogo frenético com uso intensivo das pontas.", 1.70, att_c + att_f, "Cantos_Totais"])

    # ------------------------------------------
    # ORDENAÇÃO E FILTRAGEM INTELIGENTE
    # ------------------------------------------
    # Ordena pelo Score de Confiança (maior para o menor)
    pool_mercados.sort(key=lambda x: x[3], reverse=True)
    
    mercados_finais = []
    categorias_usadas = set()
    
    # Garante variedade: não pega dois mercados da mesma categoria nos primeiros slots
    for m in pool_mercados:
        if m[4] not in categorias_usadas and len(mercados_finais) < 12:
            mercados_finais.append(m)
            categorias_usadas.add(m[4])
            
    # Preenche o resto com os mercados de maior score, independente da categoria
    for m in pool_mercados:
        if m not in mercados_finais and len(mercados_finais) < 15:
            mercados_finais.append(m)

    return {
        "status_lineup": "✅ Escalação Oficial Lida" if lineups else "⏳ Aguardando Escalação Oficial",
        "mercados": mercados_finais
    }

# --- INTERFACE PRINCIPAL ---
st.title("JP Apostas Pro 🎯")
st.write("Análise Estatística Avançada (Chutes, Posse, Gols e Cartões)")
st.divider()

# SELEÇÃO DE JOGO
data_sel = st.date_input("Selecione a data:").strftime("%Y-%m-%d")
jogos_lista = api_call("fixtures", {"date": data_sel, "timezone": "America/Sao_Paulo"})

if jogos_lista:
    opcoes = {}
    destaques = []
    for j in jogos_lista:
        nome = f"{j['teams']['home']['name']} x {j['teams']['away']['name']} ({j['league']['name']})"
        opcoes[nome] = {"id": j['fixture']['id'], "c": j['teams']['home']['name'], "f": j['teams']['away']['name']}
        if j['league']['country'] == "Brazil" or j['league']['name'] in ["Premier League", "Champions League", "La Liga"]:
            destaques.append(nome)

    t1, t2 = st.tabs(["🔥 Principais Jogos", "🌍 Todos os Jogos"])
    with t1: sel_p = st.selectbox("Destaques:", ["Selecione..."] + sorted(destaques))
    with t2: sel_e = st.selectbox("Explorar:", ["Selecione..."] + sorted(opcoes.keys()))
    jogo_final = sel_p if sel_p != "Selecione..." else sel_e
else:
    st.warning("Nenhum jogo encontrado para esta data.")
    jogo_final = "Selecione..."

st.divider()

if st.button("🧠 PROCESSAR INTELIGÊNCIA ARTIFICIAL", type="primary", use_container_width=True):
    if jogo_final != "Selecione...":
        info = opcoes[jogo_final]
        with st.spinner("Analisando Força Ofensiva, Chutes, Faltas e Mercado de Jogadores..."):
            intel = motor_de_analise_avancada(info['id'], info['c'], info['f'])
        
        if intel and len(intel['mercados']) > 0:
            st.success(f"**Jogo Analisado:** {jogo_final} | {intel['status_lineup']}")
            mercados = intel['mercados']
            
            # --- SEÇÃO 1: MELHORES ENTRADAS INDIVIDUAIS ---
            st.markdown("### 🏆 Top 3 Entradas de Maior Valor (Aposta Simples)")
            c1, c2, c3 = st.columns(3)
            for i, col in enumerate([c1, c2, c3]):
                if i < len(mercados):
                    m = mercados[i]
                    col.metric(f"Score de Confiança: {round(m[3], 1)}", f"Odd {m[2]}")
                    col.info(f"**Mercado:** {m[0]}\n\n**Análise:** {m[1]}")

            # --- SEÇÃO 2: CONSTRUTOR DE BILHETES ---
            st.markdown("### 🎫 Construtor de Bilhetes (Odds Combinadas)")
            b1, b2, b3 = st.columns(3)
            
            # Bilhete 1: Seguro (Odds Baixas/Médias, Alta Confiança)
            with b1:
                st.write("**🛡️ Bilhete Seguro**")
                # Pega os 2 primeiros mercados (os mais prováveis)
                sel_b1 = mercados[:2]
                odd_b1 = round(sel_b1[0][2] * sel_b1[1][2], 2)
                st.success(f"**Odd Combinada: {odd_b1}**\n\n" + "\n".join([f"✅ {x[0]}" for x in sel_b1]))
                
            # Bilhete 2: Focado em Estatísticas de Jogo (Chutes/Faltas/Cantos)
            with b2:
                st.write("**🎯 Bilhete de Estatísticas**")
                # Filtra apenas mercados de ação (ignorando quem vence)
                estatisticas = [m for m in mercados if m[4] in ["Chutes_Totais", "Chutes_Time", "Faltas", "Cartoes", "Cantos_Totais", "Cantos_Time", "Impedimento"]]
                if len(estatisticas) >= 2:
                    sel_b2 = random.sample(estatisticas, 2)
                    odd_b2 = round(sel_b2[0][2] * sel_b2[1][2], 2)
                    st.warning(f"**Odd Combinada: {odd_b2}**\n\n" + "\n".join([f"🎯 {x[0]}" for x in sel_b2]))
                else:
                    st.warning("Dados insuficientes para criar bilhete exclusivo de estatísticas neste jogo.")

            # Bilhete 3: Ousado (Inclui Prop de Jogadores ou Mercados Especiais)
            with b3:
                st.write("**🔥 Bilhete Ousado (Prop Player)**")
                # Tenta achar o mercado de Jogador ou o mercado de maior risco do final da lista
                jogador_prop = [m for m in mercados if m[4] == "Jogador"]
                outros = random.sample(mercados[2:6], 2) if len(mercados) > 6 else mercados[:2]
                sel_b3 = jogador_prop + [outros[0]] if jogador_prop else outros
                
                odd_b3 = 1.0
                for x in sel_b3: odd_b3 *= (x[2] + 0.1) # Bump up odd for "ousado"
                odd_b3 = round(odd_b3, 2)
                
                st.error(f"**Odd Combinada: {odd_b3}**\n\n" + "\n".join([f"⚡ {x[0]}" for x in sel_b3]))
                
    else:
        st.error("Por favor, selecione um jogo na lista antes de iniciar a varredura.")
