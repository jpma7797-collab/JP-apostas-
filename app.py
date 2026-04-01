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
/* Estilo para as abas */
.stTabs [data-baseweb="tab-list"] { gap: 24px; }
.stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: rgba(255, 255, 255, 0.05); border-radius: 8px 8px 0px 0px; padding: 10px 20px;}
.stTabs [aria-selected="true"] { background-color: rgba(0, 200, 83, 0.2) !important; }
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
    
    pool_mercados = []

    if win_c > 60:
        pool_mercados.append([f"Vitória: {casa_nome}", f"Dominância de {win_c}% baseada no histórico recente.", 1.55, win_c, "Resultado"])
        pool_mercados.append([f"Handicap Asiático: {casa_nome} -1.0", "Projeção de vitória por margem segura.", 1.95, win_c + att_c, "Handicap"])
    elif win_f > 60:
        pool_mercados.append([f"Vitória: {fora_nome}", f"Visitante amplamente favorito ({win_f}%).", 1.65, win_f, "Resultado"])
        pool_mercados.append([f"Handicap Asiático: {fora_nome} -1.0", "Diferença técnica justifica handicap negativo.", 2.05, win_f + att_f, "Handicap"])
    elif abs(win_c - win_f) <= 15:
        pool_mercados.append(["Empate no 1º Tempo", "Equilíbrio absoluto. Jogo deve começar estudado.", 2.10, empate + def_c + def_f, "HT"])
        pool_mercados.append(["Margem de Vitória: 1 Gol (Qualquer Time)", "Confronto muito parelho, decidido no detalhe.", 2.25, empate * 2, "Especiais"])

    if poisson_total > 65:
        pool_mercados.append(["Mais de 2.5 Gols", f"Índice Poisson altíssimo ({poisson_total}%). Tendência de jogo aberto.", 1.70, poisson_total, "Gols"])
        pool_mercados.append(["Ambas Marcam: Sim", "Poder ofensivo forte de ambos os lados.", 1.80, att_c + att_f, "BTTS"])
        pool_mercados.append(["Gol no 1º Tempo: Mais de 0.5", "Estatísticas indicam pressão inicial.", 1.40, (att_c + att_f) * 0.8, "Gols_HT"])
    elif poisson_total <= 45:
        pool_mercados.append(["Menos de 2.5 Gols", "Sistemas defensivos superam os ataques.", 1.60, 100 - poisson_total, "Gols"])
        pool_mercados.append(["Ambas Marcam: Não", "Cenário favorável para ao menos um time passar em branco.", 1.85, def_c + def_f, "BTTS"])

    if att_c + att_f > 115:
        pool_mercados.append(["Total de Chutes ao Gol: Mais de 8.5", "Ambos os times possuem alto volume de finalização.", 1.80, att_c + att_f, "Chutes_Totais"])
    elif def_c + def_f > 130:
        pool_mercados.append(["Total de Chutes ao Gol: Menos de 7.5", "Marcação forte deve bloquear a maioria das finalizações.", 1.75, def_c + def_f, "Chutes_Totais"])

    if att_c > 65:
        pool_mercados.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", f"Média ofensiva do mandante é elite ({att_c}%).", 1.75, att_c * 1.5, "Chutes_Time"])
    if att_f > 65:
        pool_mercados.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", "Visitante tem forte presença no terço final.", 1.85, att_f * 1.5, "Chutes_Time"])

    if win_c > 55 and att_c > 60:
        pool_mercados.append([f"Jogador: Principal Atacante do {casa_nome} (+1.5 Chutes ao Gol)", "Domínio do mandante fará a bola chegar no centroavante.", 2.10, att_c + win_c, "Jogador"])
    elif win_f > 55 and att_f > 60:
        pool_mercados.append([f"Jogador: Principal Atacante do {fora_nome} (+1.5 Chutes ao Gol)", "Transição ofensiva focada no homem de referência.", 2.20, att_f + win_f, "Jogador"])

    if att_c > 60 and def_f < 50:
        pool_mercados.append([f"Impedimentos ({casa_nome}): Mais de 1.5", "Mandante joga em profundidade contra linha alta.", 1.65, att_c + (100 - def_f), "Impedimento"])
    if att_f > 55: 
        pool_mercados.append([f"Impedimentos ({fora_nome}): Mais de 1.5", "Estratégia de bola longa do visitante deve forçar linhas.", 1.75, att_f * 1.2, "Impedimento"])
    
    if def_c < 45 or def_f < 45 or empate > 35:
        pool_mercados.append(["Total de Cartões: Mais de 4.5", "Defesas vulneráveis precisarão recorrer a faltas táticas.", 1.80, (100 - def_c) + (100 - def_f), "Cartoes"])
        pool_mercados.append(["Total de Faltas: Mais de 24.5", "Jogo de muito contato físico e transições interrompidas.", 1.85, empate * 2.5, "Faltas"])

    if att_c > 75:
        pool_mercados.append([f"Escanteios ({casa_nome}): Mais de 5.5", "Pressão lateral constante do mandante gera cantos.", 1.80, att_c * 1.6, "Cantos_Time"])
    if att_c + att_f > 130:
        pool_mercados.append(["Escanteios Totais: Mais de 9.5", "Jogo frenético com uso intensivo das pontas.", 1.70, att_c + att_f, "Cantos_Totais"])

    pool_mercados.sort(key=lambda x: x[3], reverse=True)
    
    mercados_finais = []
    categorias_usadas = set()
    
    for m in pool_mercados:
        if m[4] not in categorias_usadas and len(mercados_finais) < 12:
            mercados_finais.append(m)
            categorias_usadas.add(m[4])
            
    for m in pool_mercados:
        if m not in mercados_finais and len(mercados_finais) < 15:
            mercados_finais.append(m)

    return {
        "status_lineup": "✅ Escalação Oficial Lida" if lineups else "⏳ Aguardando Escalação",
        "mercados": mercados_finais
    }

# ==========================================
# ESTRUTURA DE ABAS (TABS) NO TOPO DA PÁGINA
# ==========================================
aba_ia, aba_calc = st.tabs(["🧠 Inteligência Artificial (Jogos)", "🧮 Calculadora de Odds"])

# ==========================================
# ABA 1: INTELIGÊNCIA ARTIFICIAL (SEU CÓDIGO ORIGINAL)
# ==========================================
with aba_ia:
    st.title("Cérebro JP Apostas Pro 🎯")
    st.write("Análise Estatística Avançada (Chutes, Posse, Gols e Cartões)")
    st.divider()

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

        t1, t2 = st.columns(2)
        with t1: sel_p = st.selectbox("🔥 Principais Jogos:", ["Selecione..."] + sorted(destaques))
        with t2: sel_e = st.selectbox("🌍 Explorar Todos os Jogos:", ["Selecione..."] + sorted(opcoes.keys()))
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
                
                # NOVIDADE AQUI: O botão para escolher o que ver na IA!
                visao_ia = st.radio(
                    "O que deseja ver para este jogo?", 
                    ["Melhores Entradas (Simples)", "Construtor de Bilhetes (Múltiplas)"], 
                    horizontal=True
                )
                
                if visao_ia == "Melhores Entradas (Simples)":
                    st.markdown("### 🏆 Top 3 Entradas de Maior Valor")
                    c1, c2, c3 = st.columns(3)
                    for i, col in enumerate([c1, c2, c3]):
                        if i < len(mercados):
                            m = mercados[i]
                            col.metric(f"Score de Confiança: {round(m[3], 1)}", f"Odd {m[2]}")
                            col.info(f"**Mercado:** {m[0]}\n\n**Análise:** {m[1]}")

                elif visao_ia == "Construtor de Bilhetes (Múltiplas)":
                    st.markdown("### 🎫 Bilhetes Prontos (Odds Combinadas)")
                    b1, b2, b3 = st.columns(3)
                    
                    with b1:
                        st.write("**🛡️ Bilhete Seguro**")
                        sel_b1 = mercados[:2]
                        odd_b1 = round(sel_b1[0][2] * sel_b1[1][2], 2)
                        st.success(f"**Odd Combinada: {odd_b1}**\n\n" + "\n".join([f"✅ {x[0]}" for x in sel_b1]))
                        
                    with b2:
                        st.write("**🎯 Bilhete de Estatísticas**")
                        estatisticas = [m for m in mercados if m[4] in ["Chutes_Totais", "Chutes_Time", "Faltas", "Cartoes", "Cantos_Totais", "Cantos_Time", "Impedimento"]]
                        if len(estatisticas) >= 2:
                            sel_b2 = random.sample(estatisticas, 2)
                            odd_b2 = round(sel_b2[0][2] * sel_b2[1][2], 2)
                            st.warning(f"**Odd Combinada: {odd_b2}**\n\n" + "\n".join([f"🎯 {x[0]}" for x in sel_b2]))
                        else:
                            st.warning("Dados insuficientes para estatísticas.")

                    with b3:
                        st.write("**🔥 Bilhete Ousado**")
                        jogador_prop = [m for m in mercados if m[4] == "Jogador"]
                        outros = random.sample(mercados[2:6], 2) if len(mercados) > 6 else mercados[:2]
                        sel_b3 = jogador_prop + [outros[0]] if jogador_prop else outros
                        
                        odd_b3 = 1.0
                        for x in sel_b3: odd_b3 *= (x[2] + 0.1)
                        odd_b3 = round(odd_b3, 2)
                        st.error(f"**Odd Combinada: {odd_b3}**\n\n" + "\n".join([f"⚡ {x[0]}" for x in sel_b3]))
                    
        else:
            st.error("Por favor, selecione um jogo na lista antes de iniciar a varredura.")

# ==========================================
# ABA 2: CALCULADORA DE ODDS (A NOVA FERRAMENTA)
# ==========================================
with aba_calc:
    st.header("🧮 Simulador de Retornos")
    st.write("Calcule seus ganhos reais antes de apostar.")
    
    tipo_aposta = st.radio(
        "Selecione o tipo de cálculo:",
        ["Aposta Simples", "Criar Aposta (Múltipla)"],
        horizontal=True
    )
    st.markdown("---")

    if tipo_aposta == "Aposta Simples":
        st.subheader("🎯 Modo: Aposta Simples")
        odd_simples = st.number_input("Digite a Odd da aposta:", min_value=1.01, value=1.50, step=0.01)
        valor_aposta = st.number_input("Valor da Aposta (R$):", min_value=1.0, value=10.0, step=1.0)
        
        if st.button("Calcular Retorno Simples", type="primary"):
            retorno = odd_simples * valor_aposta
            lucro = retorno - valor_aposta
            st.success(f"**Retorno Potencial:** R$ {retorno:.2f}")
            st.info(f"**Lucro Líquido:** R$ {lucro:.2f}")

    elif tipo_aposta == "Criar Aposta (Múltipla)":
        st.subheader("🛠️ Modo: Criar Aposta (Múltipla)")
        qtd_selecoes = st.number_input("Quantidade de seleções na aposta:", min_value=2, max_value=20, value=3, step=1)
        
        st.write("Insira as Odds de cada seleção:")
        odd_total = 1.0
        cols = st.columns(2)
        for i in range(int(qtd_selecoes)):
            with cols[i % 2]:
                odd = st.number_input(f"Odd {i+1}:", min_value=1.01, value=1.50, step=0.01, key=f"odd_{i}")
                odd_total *= odd
                
        st.markdown(f"### **Odd Total Calculada: {odd_total:.2f}**")
        valor_multipla = st.number_input("Valor da Aposta (R$):", min_value=1.0, value=10.0, step=1.0, key="valor_mult")
        
        if st.button("Calcular Retorno Múltipla", type="primary"):
            retorno_mult = odd_total * valor_multipla
            lucro_mult = retorno_mult - valor_multipla
            st.success(f"**Retorno Potencial:** R$ {retorno_mult:.2f}")
            st.info(f"**Lucro Líquido:** R$ {lucro_mult:.2f}")
