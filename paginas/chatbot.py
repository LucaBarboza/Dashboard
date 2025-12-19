import streamlit as st
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.header("🤖 Assistente Virtual do Projeto")
st.markdown("""
Tem dúvidas sobre a metodologia, os códigos ou os conceitos estatísticos usados? 
Pergunte ao **Gemini**, que foi treinado com a documentação técnica deste dashboard.
""")

# --- 1. CONFIGURAÇÃO DA API ---
# Tenta pegar do secrets (nuvem) ou pede na sidebar (local)
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

# Se estiver rodando localmente sem secrets, use a input. Se tiver secrets, usa direto.
if not api_key:
    if "GEMINI_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_KEY"]
    else:
        st.warning("⚠️ Insira a chave da API do Google Gemini na barra lateral para começar.")
        st.stop()

try:
    genai.configure(api_key=api_key)
    # Usando o modelo Flash (Rápido e Inteligente)
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"Erro de Configuração: {e}")
    st.stop()

# --- 2. O "CÉREBRO" DO BOT (O Prompt de Sistema) ---
# Aqui garantimos que ele sabe tudo o que foi feito.
CONTEXTO_DO_PROJETO = """
VOCÊ É O ASSISTENTE ESPECIALISTA DESTE DASHBOARD CLIMÁTICO (BRASIL 2015-2021).
Sua missão é explicar para a banca avaliadora ou usuários como este projeto foi construído.

AQUI ESTÁ A DOCUMENTAÇÃO TÉCNICA DO PROJETO:

1. DADOS:
- Fonte: INMET (Instituto Nacional de Meteorologia).
- Período: 2015 a 2021.
- Granularidade original: Semanal.
- Variáveis: Temperatura, Chuva, Umidade, Vento, Pressão, Radiação.
- Tratamento: Limpeza de NaNs e criação de colunas temporais (Ano, Mês, Estação).

2. PÁGINA: DASHBOARD INTERATIVO
- Objetivo: Análise descritiva.
- O que faz: Mostra médias, desvio padrão e extremos.
- Gráficos: Usa Boxplots (distribuição) e Gráficos de Linha (séries temporais).
- Detalhe técnico: Permite filtrar por Região e Estado simultaneamente.

3. PÁGINA: MAPA TEMPORAL ANIMADO
- Objetivo: Visualizar a evolução geoespacial.
- Tecnologia: Plotly Express com `animation_frame`.
- O "Pulo do Gato": Fixamos a escala de cores (`range_color`) com o min/max global de todo o período. Se não fizéssemos isso, as cores "piscariam" (mudariam de significado) a cada ano, impedindo a comparação justa.

4. PÁGINA: ESTATÍSTICA (CORRELAÇÃO)
- Objetivo: Entender relações entre variáveis.
- Métodos: 
  a) Pearson: Para relações lineares (Reta).
  b) Spearman: Para relações monotônicas (Rank).
- Visual: Heatmaps comparativos lado a lado.

5. PÁGINA: TESTE DE HIPÓTESES (A MAIS COMPLEXA)
- Objetivo: Validar se diferenças (ex: Norte vs Sul) são reais ou acaso.
- Metodologia Rigorosa (Fluxograma de Decisão):
  1. Testamos Normalidade (Shapiro-Wilk).
  2. Testamos Homogeneidade de Variância (Levene).
  3. DECISÃO AUTOMÁTICA:
     - Se Normal + Homogêneo -> ANOVA (3+ grupos) ou Teste T (2 grupos).
     - Se Normal + Heterogêneo -> Teste T de Welch.
     - Se Não Normal -> Kruskal-Wallis (3+ grupos) ou Mann-Whitney U (2 grupos).
- Independência: Alertamos que dados semanais brutos violam independência (séries temporais). Oferecemos um modo "Médias Anuais" para corrigir isso agregando os dados.

6. PÁGINA: MODELAGEM (MACHINE LEARNING)
- Aba Regressão: Linear Regression do Scikit-Learn para medir impacto de variáveis.
- Aba Clustering: K-Means para agrupar estados por similaridade climática (ignorando geografia política).
- Aba Anomalias: Isolation Forest para detectar eventos extremos (outliers).
- Aba Previsão: Regressão Linear com "Dummy Variables" para os meses.
  - Por que Dummies? Para capturar a Sazonalidade (ondas de calor/frio) dentro de um modelo linear simples.
  - Validação: Usamos Backtesting (treina no passado antigo, testa no ano recente) para calcular o erro (MAE).

RESPOSTAS:
- Seja didático, mas técnico.
- Se perguntarem "O que é ANOVA One-Way?", explique: "É um teste para comparar médias de 3 ou mais grupos baseados em 1 fator apenas. Diferente da Two-Way que usaria 2 fatores."
- Se perguntarem sobre o código, explique que foi feito em Python + Streamlit.
"""

# --- 3. GERENCIAMENTO DO CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Injeta o contexto na primeira mensagem (invisível ao usuário, mas o modelo vê)
    st.session_state.chat = model.start_chat(history=[
        {"role": "user", "parts": CONTEXTO_DO_PROJETO},
        {"role": "model", "parts": "Entendido. Estou pronto para explicar cada detalhe técnico e estatístico deste dashboard."}
    ])

# Exibe histórico visual
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input do usuário
if prompt := st.chat_input("Pergunte sobre os testes, o mapa ou os modelos..."):
    # Mostra mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Gera resposta
    with st.chat_message("assistant"):
        with st.spinner("Consultando documentação..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
