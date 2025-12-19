import streamlit as st

# --- CONFIGURAÇÃO INICIAL (Deve ser a primeira linha) ---
st.set_page_config(
    page_title="Observatório Climático",
    page_icon="⛅",
    layout="wide"
)

# --- DEFINIÇÃO DA NAVEGAÇÃO ---
paginas = {
    # 1. Página Inicial (Sem categoria)
    "": [
        st.Page('paginas/home.py', title='Home', default=True),
    ],
    
    # 2. O Core do Projeto (Análises)
    "Análise de Dados": [
        st.Page('paginas/dashboard.py', title='Dashboard Interativo', icon="📊"),
        st.Page('paginas/mapa.py', title='Mapa Temporal Climático', icon="🌍"),
        st.Page('paginas/estatistica.py', title='Matrizes de Correlação', icon="📉"),
        st.Page('paginas/testes.py', title='Teste de Hipóteses', icon="🧪"),
        st.Page('paginas/modelagem.py', title='Modelagem e IA', icon="🧠"),
    ],
    
    # 3. O Diferencial (Chatbot)
    "Assistente Virtual": [
        st.Page('paginas/chatbot.py', title='Chatbot Especialista', icon="💬"),
    ]
}

# --- EXECUÇÃO ---
pag = st.navigation(paginas)
pag.run()
