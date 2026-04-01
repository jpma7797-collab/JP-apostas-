import streamlit as st

# Configuração da página
st.set_page_config(page_title="Cérebro JP Apostas", layout="centered")

st.title("🧠 Cérebro JP Apostas")
st.markdown("---")

# Menu de escolha - O SEGREDO ESTÁ AQUI
tipo_aposta = st.radio(
    "Selecione o tipo de análise que deseja fazer agora:",
    ["Aposta Simples", "Criar Aposta"],
    horizontal=True
)

st.markdown("---")

# ==========================================
# LÓGICA DA APOSTA SIMPLES
# ==========================================
if tipo_aposta == "Aposta Simples":
    st.subheader("🎯 Modo: Aposta Simples")
    
    odd_simples = st.number_input("Digite a Odd da aposta:", min_value=1.01, value=1.50, step=0.01)
    valor_aposta = st.number_input("Valor da Aposta (R$):", min_value=1.0, value=10.0, step=1.0)
    
    if st.button("Calcular Retorno Simples", type="primary"):
        retorno = odd_simples * valor_aposta
        lucro = retorno - valor_aposta
        st.success(f"**Retorno Potencial:** R$ {retorno:.2f}")
        st.info(f"**Lucro Líquido:** R$ {lucro:.2f}")

# ==========================================
# LÓGICA DO CRIAR APOSTA
# ==========================================
elif tipo_aposta == "Criar Aposta":
    st.subheader("🛠️ Modo: Criar Aposta (Múltipla)")
    
    qtd_selecoes = st.number_input("Quantidade de seleções na aposta:", min_value=2, max_value=20, value=3, step=1)
    
    st.write("Insira as Odds de cada seleção:")
    odd_total = 1.0
    
    # Cria as caixinhas dinâmicas dependendo de quantas seleções você escolheu
    cols = st.columns(2)
    for i in range(int(qtd_selecoes)):
        with cols[i % 2]:
            odd = st.number_input(f"Odd da Seleção {i+1}:", min_value=1.01, value=1.50, step=0.01, key=f"odd_{i}")
            odd_total *= odd
            
    st.markdown("---")
    st.markdown(f"### **Odd Total Calculada: {odd_total:.2f}**")
    
    valor_multipla = st.number_input("Valor da Aposta (R$):", min_value=1.0, value=10.0, step=1.0, key="valor_mult")
    
    if st.button("Calcular Retorno Múltipla", type="primary"):
        retorno_mult = odd_total * valor_multipla
        lucro_mult = retorno_mult - valor_multipla
        st.success(f"**Retorno Potencial:** R$ {retorno_mult:.2f}")
        st.info(f"**Lucro Líquido:** R$ {lucro_mult:.2f}")
