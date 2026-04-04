import streamlit as st
import datetime
import requests
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JP Apostas Pro", layout="wide", initial_sidebar_state="collapsed")

# --- SUA CHAVE DA API ---
CHAVE_API = "4ff6fcf934058cffb79383415bbb913e"

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
        data = res.json()
        if data.get('errors'):
            return {"erro": data.get('errors')}
        return data.get('response', [])
    except Exception as e:
        return {"erro": str(e)}

# --- CAÇADOR DE ODDS REAIS ---
def buscar_odds_reais(f_id):
    odds_data = api_call("odds", {"fixture": f_id})
    mercados_reais = {}
    
    # Proteção caso a API mande erro no meio da busca de odds
    if isinstance(odds_data, dict) and "erro" in odds_data:
        return mercados_reais

    if odds_data and isinstance(odds_data, list) and len(odds_data) > 0 and odds_data[0].get("bookmakers"):
        bets = odds_data[0]["bookmakers"][0].get("bets", [])
        for b in bets:
            nome = b["name"]
            valores = b["values"]
            
            if nome == "Match Winner":
                for v in valores:
                    if v["value"] == "Home": mercados_reais["vitoria_casa"] = float(v["odd"])
                    if v["value"] == "Away": mercados_reais["vitoria_fora"] = float(v["odd"])
            elif nome == "Goals Over/Under":
                for v in valores:
                    if v["value"] == "Over 1.5": mercados_reais["over_15"] = float(v["odd"])
                    if v["value"] == "Over 2.5": mercados_reais["over_25"] = float(v["odd"])
                    if v["value"] == "Under 2.5": mercados_reais["under_25"] = float(v["odd"])
            elif nome == "Both Teams Score":
                for v in valores:
                    if v["value"] == "Yes": mercados_reais["ambas_sim"] = float(v["odd"])
            elif nome == "Double Chance":
                for v in valores:
                    if v["value"] == "Home/Draw": mercados_reais["dc_casa"] = float(v["odd"])
                    if v["value"] == "Draw/Away": mercados_reais["dc_fora"] = float(v["odd"])
    return mercados_reais

# --- CÉREBRO JP: ANÁLISE DINÂMICA DE MERCADOS ---
def motor_de_analise_avancada(f_id, casa_nome, fora_nome):
    data = api_call("predictions", {"fixture": f_id})
    lineups = api_call("fixtures/lineups", {"fixture": f_id})
    odds_reais = buscar_odds_reais(f_id)
    
    # Validação de segurança para não quebrar a página
    if not data or (isinstance(data, dict) and "erro" in data) or not isinstance(data, list) or len(data) == 0:
        return None
    
    p = data[0]
    comp = p['comparison']
    perc = p['predictions']['percent']
    
    win_c = float(perc['home'].replace('%',''))
    win_f = float(perc['away'].replace('%',''))
    
    att_c = float(comp['att']['home'].replace('%',''))
    att_f = float(comp['att']['away'].replace('%',''))
    def_c = float(comp['def']['home'].replace('%',''))
    def_f = float(comp['def']['away'].replace('%',''))
    
    poisson_c = float(comp['poisson_distribution']['home'].replace('%',''))
    poisson_f = float(comp['poisson_distribution']['away'].replace('%',''))
    poisson_total = poisson_c + poisson_f
    
    form_c = float(comp['form']['home'].replace('%',''))
    form_f = float(comp['form']['away'].replace('%',''))
    h2h_c = float(comp['h2h']['home'].replace('%',''))
    h2h_f = float(comp['h2h']['away'].replace('%',''))

    pool = []
    
    # --- 1. MERCADOS DE RESULTADO ---
    if win_c >= 55 and form_c > form_f:
        odd = odds_reais.get("vitoria_casa", 1.65)
        pool.append([f"Vitória: {casa_nome}", f"Mandante com momento superior ({win_c}%).", odd, "resultado"])
        if win_c >= 65 and att_c > 60:
            pool.append([f"Vence o 1º Tempo: {casa_nome}", f"Ataque forte costuma resolver cedo.", odd + 0.60, "resultado_ht"])
    elif win_f >= 55 and form_f > form_c:
        odd = odds_reais.get("vitoria_fora", 1.75)
        pool.append([f"Vitória: {fora_nome}", f"Visitante em grande fase ({win_f}%).", odd, "resultado"])
        if win_f >= 65 and att_f > 60:
            pool.append([f"Vence o 1º Tempo: {fora_nome}", f"Visitante letal nos minutos iniciais.", odd + 0.60, "resultado_ht"])
    
    if 40 <= win_c < 55:
        odd = odds_reais.get("dc_casa", 1.35)
        pool.append([f"Dupla Chance: {casa_nome} ou Empate", f"Jogo equilibrado, proteção para o mandante.", odd, "resultado_seguro"])
    elif 40 <= win_f < 55:
        odd = odds_reais.get("dc_fora", 1.45)
        pool.append([f"Dupla Chance: {fora_nome} ou Empate", f"Proteção essencial para o visitante.", odd, "resultado_seguro"])

    # --- 2. MERCADOS DE GOLS ---
    if poisson_total >= 65 and att_c > 45 and att_f > 45:
        odd_over = odds_reais.get("over_25", 1.85)
        odd_ambas = odds_reais.get("ambas_sim", 1.75)
        pool.append(["Mais de 2.5 Gols", "Times com alto índice de finalização.", odd_over, "gols_over"])
        pool.append(["Ambas Marcam: Sim", "Padrão tático de jogo aberto dos dois lados.", odd_ambas, "ambas"])
    elif poisson_total >= 50:
        odd = odds_reais.get("over_15", 1.30)
        pool.append(["Mais de 1.5 Gols", "Tendência segura de rede balançando.", odd, "gols_over"])
    
    if def_c > 65 and def_f > 65 and poisson_total < 40:
        odd = odds_reais.get("under_25", 1.65)
        pool.append(["Menos de 2.5 Gols", "Defesas sólidas, jogo muito truncado.", odd, "gols_under"])

    # --- 3. CHUTES E FINALIZAÇÕES ---
    if att_c >= 60:
        pool.append([f"Chutes ao Gol ({casa_nome}): Mais de 4.5", "Mandante pressiona muito em casa.", 1.70, "chutes_casa"])
    if att_f >= 55:
        pool.append([f"Chutes ao Gol ({fora_nome}): Mais de 3.5", "Visitante usa muito o contra-ataque.", 1.80, "chutes_fora"])
    if lineups and not (isinstance(lineups, dict) and "erro" in lineups) and win_c > 50:
        pool.append([f"Atacante {casa_nome} (+1.5 Chutes a Gol)", "Homem de referência será muito acionado.", 2.10, "jogador_chutes"])

    # --- 4. ESCANTEIOS ---
    pressao_total = att_c + att_f + form_c + form_f
    if pressao_total > 220:
        pool.append(["Mais de 8.5 Escanteios na Partida", "Jogo de muita intensidade pelas pontas.", 1.65, "escanteios"])
    elif pressao_total > 180:
        pool.append(["Mais de 7.5 Escanteios", "Volume de jogo favorável a bloqueios na linha de fundo.", 1.40, "escanteios"])

    # --- 5. CARTÕES E FALTAS ---
    agressividade = (100 - def_c) + (100 - def_f)
    if agressividade > 110 or (h2h_c > 45 and h2h_f > 45):
        pool.append(["Mais de 4.5 Cartões no Jogo", "Histórico do confronto e estilo das defesas pedem jogo faltoso.", 1.70, "cartoes"])
        pool.append(["Mais de 24.5 Faltas", "Muitas paradas táticas e erros de marcação esperados.", 1.80, "faltas"])
    
    # --- 6. IMPEDIMENTOS ---
    if def_c > 60 and att_f > 50:
        pool.append([f"Impedimentos ({fora_nome}): Mais de 1.5", "Mandante joga com linhas altas, visitante tenta bolas longas.", 1.65, "impedimentos"])

    is_oficial = False
    if lineups and isinstance(lineups, list) and len(lineups) > 0:
        is_oficial = True

    return {"status": "✅ Oficial" if is_oficial else "⏳ Provável", "mercados": pool}

# --- GERADOR INTELIGENTE DE BILHETES ---
def construir_bilhetes(mercados_pool):
    if not mercados_pool:
        st.warning("Dados insuficientes para gerar bilhetes para esta partida.")
        return

    bilhetes_conservadores = []
    bilhetes_ousados = []
    
    for _ in range(30):
        if len(bilhetes_conservadores) >= 2 and len(bilhetes_ousados) >= 2:
            break
            
        random.shuffle(mercados_pool)
        qtd_itens = random.randint(2, 4)
        
        bilhete_atual = []
        categorias_usadas = set()
        odd_total = 1.0
        
        for m in mercados_pool:
            categoria = m[3]
            if categoria not in categorias_usadas:
                bilhete_atual.append(m)
                categorias_usadas.add(categoria)
                odd_total *= m[2]
            if len(bilhete_atual) == qtd_itens:
                break
                
        if len(bilhete_atual) >= 2:
            if odd_total <= 4.0 and len(bilhetes_conservadores) < 2:
                bilhetes_conservadores.append({"itens": bilhete_atual, "odd": odd_total})
            elif odd_total > 4.0 and len(bilhetes_ousados) < 2:
                bilhetes_ousados.append({"itens": bilhete_atual, "odd": odd_total})

    return bilhetes_conservadores, bilhetes_ousados

def renderizar_bilhetes(lista_bilhetes, tipo, titulo):
    if not lista_bilhetes: return
    
    cols = st.columns(len(lista_bilhetes))
    for i, col in enumerate(cols):
        b = lista_bilhetes[i]
        classe_odd = "ousado" if tipo == "ousado" else ""
        icone = "🔥" if tipo == "ousado" else "🛡️"
        
        html_card = f'<div class="bet-card"><div class="bet-title">{icone} {titulo} {i+1}</div><div class="odd-box {classe_odd}">Odd: {b["odd"]:.2f}</div>'
        for x in b["itens"]:
            html_card += f'<div class="bet-item"><div class="bet-market">🎯 {x[0]} <span style="color:#00e676; font-size:0.9rem;">({x[2]:.2f})</span></div><div class="bet-reason">{x[1]}</div></div>'
        html_card += '</div>'
        col.markdown(html_card, unsafe_allow_html=True)

# --- INTERFACE PRINCIPAL ---
tab_ia, tab_calc = st.tabs(["🧠 Cérebro JP IA", "🧮 Calculadora de Lucro"])

with tab_ia:
    st.markdown("<h1>JP Apostas Pro <span style='color: #00e676;'>🎯</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; margin-bottom: 30px;'>Inteligência Artificial para análises dinâmicas baseadas nos atributos de cada jogo.</p>", unsafe_allow_html=True)
    
    data_sel = st.date_input("Data dos Jogos:", value=datetime.date.today()).strftime("%Y-%m-%d")
    
    with st.spinner("Buscando jogos no servidor..."):
        jogos_dia = api_call("fixtures", {"date": data_sel, "timezone": "America/Sao_Paulo"})
    
    # 1. VERIFICA SE DEU ERRO DE API (LIMITE)
    if isinstance(jogos_dia, dict) and "erro" in jogos_dia:
        st.error("⚠️ **Erro na comunicação com a API-Sports**")
        st.json(jogos_dia["erro"])
        st.info("💡 **Dica:** O limite diário pode ter esgotado. Tente forçar a atualização.")
        if st.button("🔄 Tentar Novamente / Limpar Cache", type="primary"):
            st.cache_data.clear()
            st.rerun()

    # 2. SE TROUXE OS JOGOS NORMALMENTE
    elif jogos_dia and isinstance(jogos_dia, list):
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
        tipo_analise = st.radio("Estratégia da IA:", ["Entradas Simples", "Criar Aposta (Bilhetes)"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 PROCESSAR ANÁLISE DINÂMICA", type="primary", use_container_width=True) and jogo_obj:
            with st.spinner("Lendo histórico, cruzando dados defensivos/ofensivos e buscando odds reais nas casas de apostas..."):
                intel = motor_de_analise_avancada(jogo_obj['fixture']['id'], jogo_obj['teams']['home']['name'], jogo_obj['teams']['away']['name'])
            
            if intel and len(intel['mercados']) >= 2:
                if tipo_analise == "Entradas Simples":
                    st.markdown("### 🏆 Recomendações Individuais (Baseado na leitura do jogo)")
                    cols = st.columns(min(3, len(intel['mercados'])))
                    mercados_simples = sorted(intel['mercados'], key=lambda x: x[2])[:3]
                    for i, m in enumerate(mercados_simples):
                        card_simples = f'<div class="bet-card"><div class="bet-title">Entrada {i+1}</div><div class="odd-box">Odd: {m[2]:.2f}</div><div class="bet-item"><div class="bet-market">🎯 {m[0]}</div><div class="bet-reason">{m[1]}</div></div></div>'
                        cols[i].markdown(card_simples, unsafe_allow_html=True)
                
                else:
                    b_cons, b_ous = construir_bilhetes(intel['mercados'])
                    
                    if b_cons:
                        st.markdown("### 🛡️ BILHETES CONSERVADORES (Odd Total até 4.0)")
                        renderizar_bilhetes(b_cons, "seguro", "Bilhete Seguro")
                        st.markdown("<br>", unsafe_allow_html=True)

                    if b_ous:
                        st.markdown("### 🔥 BILHETES OUSADOS (Odd Total acima de 4.0)")
                        renderizar_bilhetes(b_ous, "ousado", "Bilhete Ousado")
            else:
                st.warning("Jogo com pouquíssimas estatísticas. Não há margem segura para gerar bilhetes personalizados.")

    # 3. SE VEIO VAZIO (O ERRO QUE VOCÊ ESTAVA TENDO!)
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("⚠️ **A tela parou de carregar porque o sistema travou sem resultados na memória.**")
        st.write("Isso acontece quando o aplicativo salva um 'cache vazio' após uma oscilação na internet ou se a API realmente não cobrir nenhum jogo nesta data.")
        
        if st.button("🔄 Forçar Atualização (Limpar Cache)", type="primary"):
            st.cache_data.clear()
            st.rerun()

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
