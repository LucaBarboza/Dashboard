import streamlit as st

# --- CONFIGURAÇÃO VISUAL ---
# Título Principal com formatação centralizada e CSS dinâmico (Claro/Escuro)
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        color: #2E86C1;
        margin-bottom: 0px;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: var(--text-color); /* Adapta ao tema (antes era #555) */
        margin-bottom: 30px;
        opacity: 0.8;
    }
    
    /* Estilo para os Cards de Navegação */
    .card {
        background-color: var(--secondary-background-color); /* Fundo dinâmico (antes #f0f2f6) */
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2E86C1;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Sombra suave */
    }
    /* Garante que o texto dentro dos cards também se adapte */
    .card h3, .card p {
        color: var(--text-color) !important;
    }

    /* Estilo para o Card de Destaque (Cobertura Nacional) */
    .metric-card {
        text-align: center;
        padding: 20px;
        background-color: var(--secondary-background-color); /* Fundo dinâmico */
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card h1, .metric-card p {
        color: var(--text-color) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<div class="main-title">🌤️ Observatório Climático Brasileiro</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Análise de Dados Meteorológicos, Estatística Avançada e Inteligência Artificial (2015-2021)</div>', unsafe_allow_html=True)

st.markdown("---")
st.image("arquivos/capa.png", use_container_width=True)
# --- INTRODUÇÃO ---

st.markdown("### 🎯 O Objetivo")
st.write("""
Este projeto é uma **plataforma analítica completa** desenvolvida para explorar a complexidade do clima brasileiro. 
Utilizando dados reais do **INMET**, transformamos milhões de linhas de dados brutos em conhecimento visual e preditivo.

A ferramenta foi desenhada para atender desde curiosos sobre o clima até cientistas de dados, 
oferecendo desde visualizações descritivas até modelos de Machine Learning.
""")

st.info("**Fonte dos Dados:** Instituto Nacional de Meteorologia (INMET). Período abrangido: 2015 a 2021.")

st.markdown("---")

# --- O QUE VOCÊ VAI ENCONTRAR (GUIA DE NAVEGAÇÃO) ---
st.subheader("🧭 Guia de Navegação")
st.markdown("Explore as funcionalidades através do menu lateral. Veja o que cada módulo oferece:")

# Linha 1 de Cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <h3>📊 Dashboard Interativo</h3>
        <p>Uma visão geral descritiva. Filtre por estados, analise médias, extremos e veja a distribuição dos dados (Boxplots e Histogramas) de forma rápida e intuitiva.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <h3>🌍 Mapa Temporal Animado</h3>
        <p>Assista à evolução do clima. Mapas coropléticos animados que mostram como a temperatura, chuva e umidade mudaram ao longo dos anos e estações.</p>
    </div>
    """, unsafe_allow_html=True)

# Linha 2 de Cards
col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="card">
        <h3>📉 Estatística & Correlações</h3>
        <p>O "porquê" dos dados. Matrizes de correlação (Pearson/Spearman) e testes de hipótese automatizados (ANOVA/Test-T) para validar diferenças climáticas.</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="card">
        <h3>🤖 IA & Modelagem</h3>
        <p>O nível avançado. Algoritmos de Machine Learning para prever o futuro (Séries Temporais), detectar anomalias e agrupar o Brasil em novos clusters climáticos.</p>
    </div>
    """, unsafe_allow_html=True)

# --- RODAPÉ TÉCNICO ---
st.markdown("---")
with st.expander("🛠️ Ficha Técnica do Projeto"):
    st.markdown("""
    Este dashboard foi construído utilizando as seguintes tecnologias:
    * **Linguagem:** Python 3.10+
    * **Framework Web:** Streamlit
    * **Processamento de Dados:** Pandas & NumPy
    * **Visualização:** Plotly Express & Graph Objects
    * **Machine Learning:** Scikit-Learn (Regressão, K-Means, Isolation Forest)
    * **Geoprocessamento:** GeoJSON & Folium logic
    * **Estatística:** SciPy Stats
    """)