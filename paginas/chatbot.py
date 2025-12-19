import streamlit as st
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.header("🤖 Assistente Técnico do Projeto")
st.markdown("""
Este assistente é o **especialista na metodologia** deste trabalho. 
Você pode perguntar sobre as escolhas estatísticas, as bibliotecas utilizadas ou como os algoritmos de Machine Learning foram configurados.
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
    model = genai.GenerativeModel('gemini-2.5-flash') 
except Exception as e:
    st.error(f"Erro de Configuração: {e}")
    st.stop()

# --- 2. O "CÉREBRO" DO BOT (Documentação Técnica Estática) ---
# Este contexto é "blindado". Ele só sabe o que está escrito aqui, evitando alucinações.
CONTEXTO_DO_PROJETO = """
VOCÊ É O ASSISTENTE TÉCNICO DE UM DASHBOARD DE ANÁLISE CLIMÁTICA (BRASIL 2015-2021).
Sua função é explicar a metodologia científica e técnica usada no trabalho.

AQUI ESTÁ A DOCUMENTAÇÃO TÉCNICA:

1. DADOS:
- Fonte: INMET (Instituto Nacional de Meteorologia) via Kaggle.
- Período: 2015 a 2021.
- Granularidade: Semanal.
- Tratamento: Limpeza de dados nulos e engenharia de recursos (criação de colunas Ano/Mês/Estação).

2. ARQUITETURA DE SOFTWARE:
- Linguagem: Python.
- Interface: Streamlit.
- Visualização: Plotly Express (para interatividade).
- Cache: Usamos `@st.cache_data` para otimizar o carregamento.

3. PÁGINA: MAPA TEMPORAL (GEOESPACIAL):
- Tecnologia: Mapa Coroplético animado (`animation_frame`).
- Decisão de Design: Fixamos o `range_color` (escala de cores) com o mínimo e máximo global dos dados. 
  - Por que? Para garantir que a cor "Vermelho Escuro" represente a mesma temperatura em 2015 e 2021, permitindo comparação visual justa.

4. PÁGINA: ESTATÍSTICA (CORRELAÇÃO):
- Exibimos matrizes de Pearson (Linear) e Spearman (Não-Linear/Postos) lado a lado para identificar relações complexas entre variáveis (ex: Chuva x Temperatura).

5. PÁGINA: TESTE DE HIPÓTESES (RIGOR CIENTÍFICO):
- O sistema possui um algoritmo de decisão automática:
  1. Roda Shapiro-Wilk (Teste de Normalidade).
  2. Roda Levene (Teste de Homogeneidade de Variância).
  3. DECISÃO:
     - Se Normal + Homogêneo -> Aplica ANOVA One-Way (ou Teste T).
     - Se Normal + Heterogêneo -> Aplica Teste T de Welch.
     - Se Não-Normal -> Aplica Kruskal-Wallis (ou Mann-Whitney U).
- Independência: Alertamos o usuário que dados semanais possuem autocorrelação, sugerindo o uso de "Médias Anuais" para validação estatística robusta.

6. PÁGINA: MODELAGEM (MACHINE LEARNING):
- Clusterização: Usamos K-Means para agrupar estados por similaridade climática, ignorando fronteiras políticas.
- Detecção de Anomalias: Usamos Isolation Forest para encontrar semanas com comportamento climático extremo (outliers).
- Previsão (Séries Temporais):
  - Modelo: Regressão Linear Múltipla.
  - Técnica: Criamos "Dummy Variables" para os meses (One-Hot Encoding).
  - Motivo: Isso permite que um modelo linear aprenda a curva sazonal (ondas de calor e frio) ao longo do ano.
  - Validação: Backtesting (treino no passado, teste no ano mais recente).

DIRETRIZES DE RESPOSTA:
- Responda apenas sobre a metodologia, ferramentas e conceitos acima.
- Se perguntarem sobre um dado específico (ex: "Qual a temperatura dia 15?"), diga: "Eu sou focado na metodologia do projeto. Para explorar os dados brutos, por favor utilize a aba 'Dashboard Interativo' ou 'Mapa'."
- Seja formal e acadêmico.
"""

# --- 3. GERENCIAMENTO DO CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Inicia o chat enviando o manual (invisível ao usuário)
    st.session_state.chat = model.start_chat(history=[
        {"role": "user", "parts": CONTEXTO_DO_PROJETO},
        {"role": "model", "parts": "Entendido. Atuarei como o especialista técnico do projeto."}
    ])

# Exibe histórico visual
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input do usuário
if prompt := st.chat_input("Dúvidas sobre a metodologia? (Ex: Como funciona o teste de hipótese?)"):
    # Mostra mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Gera resposta
    with st.chat_message("assistant"):
        with st.spinner("Consultando documentação técnica..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
