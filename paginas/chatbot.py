import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.header("🤖 Assistente Especialista (Técnico & Analítico)")
st.markdown("""
Este assistente tem acesso total ao projeto. Ele pode responder sobre:
1.  **Metodologia:** Como o dashboard foi construído, quais testes usamos e por quê.
2.  **Dados Reais:** Quais foram as médias, os recordes de temperatura e tendências observadas no Brasil.
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
    # Usando o modelo estável mais rápido disponível
    model = genai.GenerativeModel('gemini-2.5-flash') 
except Exception as e:
    st.error(f"Erro de Configuração: {e}")
    st.stop()

# --- 2. GERAÇÃO DE MEMÓRIA (DADOS + DOCUMENTAÇÃO) ---
@st.cache_data
def criar_contexto_completo():
    # A. Carrega os Dados
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except:
        df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")

    # --- CORREÇÃO: TRATAMENTO DE DADOS (CRIAÇÃO DA COLUNA ANO) ---
    if 'semana_ref' in df.columns:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['ano'] = df['semana_ref'].dt.year
        df['mes'] = df['semana_ref'].dt.month
    # -------------------------------------------------------------

    # Criação do "Cheat Sheet" de Dados (Resumo Numérico Leve)
    # Agora a coluna 'ano' existe, então o groupby vai funcionar
    resumo_dados = f"""
    [ESTATÍSTICAS GERAIS DOS DADOS REAIS 2015-2021]
    - Total de Registros Analisados: {len(df)} linhas (semanais).
    - Temperatura: Mínima {df['temperatura_media'].min():.1f}°C | Máxima {df['temperatura_media'].max():.1f}°C | Média Global {df['temperatura_media'].mean():.1f}°C.
    - Chuva Semanal: Máximo registrado {df['chuva_media_semanal'].max():.1f}mm | Média Global {df['chuva_media_semanal'].mean():.1f}mm.
    
    [EXTREMOS POR ESTADO (MÉDIA HISTÓRICA)]
    - Estado mais Quente: {df.groupby('state')['temperatura_media'].mean().idxmax()}
    - Estado mais Frio: {df.groupby('state')['temperatura_media'].mean().idxmin()}
    - Estado mais Chuvoso: {df.groupby('state')['chuva_media_semanal'].mean().idxmax()}
    
    [EVOLUÇÃO ANUAL (TENDÊNCIA)]
    Médias de Temperatura por Ano:
    {df.groupby('ano')['temperatura_media'].mean().to_string()}
    """

    # B. A Documentação Técnica
    doc_tecnica = """
    AQUI ESTÁ A DOCUMENTAÇÃO TÉCNICA DO PROJETO:

    1. DADOS:
    - Fonte: INMET (Instituto Nacional de Meteorologia) via Kaggle.
    - Período: 2015 a 2021.
    - Granularidade original: Por hora.
    - Variáveis: Temperatura, Chuva, Umidade, Vento, Pressão, Radiação.
    - Tratamento: Limpeza de NaNs e criação de colunas temporais (Ano, Mês, Estação). Foram agrupados em grupos de tempo (semana, mes e ano).

    2. PÁGINA: DASHBOARD INTERATIVO
    - Objetivo: Análise descritiva.
    - O que faz: Mostra médias, desvio padrão e extremos.
    - Gráficos: Usa Boxplots e Gráficos de Linha.
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
    """

    # C. Consolidação do Prompt de Sistema
    prompt_final = f"""
    VOCÊ É O ASSISTENTE ESPECIALISTA DESTE DASHBOARD CLIMÁTICO.
    Sua missão é explicar para a banca avaliadora ou usuários tanto os DADOS REAIS quanto a METODOLOGIA TÉCNICA.
    
    {doc_tecnica}
    
    {resumo_dados}
    
    DIRETRIZES DE RESPOSTA:
    - Se perguntarem sobre NÚMEROS (ex: "Qual o estado mais quente?"), consulte a seção [ESTATÍSTICAS GERAIS].
    - Se perguntarem sobre PROCESSO (ex: "Como funciona o mapa?"), consulte a seção [DOCUMENTAÇÃO TÉCNICA].
    - Seja didático, profissional e técnico.
    - Se perguntarem "O que é ANOVA One-Way?", explique: "É um teste para comparar médias de 3 ou mais grupos baseados em 1 fator apenas."
    """
    
    return prompt_final

# Carrega o contexto (com cache para não recalcular toda hora)
prompt_sistema = criar_contexto_completo()

# --- 3. GERENCIAMENTO DO CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Inicia o chat com o contexto injetado
    st.session_state.chat = model.start_chat(history=[
        {"role": "user", "parts": prompt_sistema},
        {"role": "model", "parts": "Entendido. Tenho acesso aos dados estatísticos e à documentação técnica. Estou pronto."}
    ])

# Exibe histórico visual
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: Qual o estado mais quente ou como funciona a previsão?"):
    # Mostra mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Gera resposta
    with st.chat_message("assistant"):
        with st.spinner("Analisando base de conhecimento..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
