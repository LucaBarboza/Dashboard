import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Análise Climática",
    page_icon="⛅",
    layout="wide"
)

# ... (código anterior do app.py)

paginas = {
    "": [
        st.Page('paginas/home.py', title='Home', default=True),
    ],
    "Análise de dados": [
        st.Page('paginas/dashboard.py', title='Dashboard Interativo', icon = "📊", default=False),
        st.Page('paginas/mapa.py', title='Mapa Temporal Climático', icon = "🗺️",default=False),
        st.Page('paginas/estatistica.py', title='Matrizes de Correlação', icon="📈"),
        st.Page('paginas/modelagem.py', title='Modelagem e Previsão', icon="🤖"),
        st.Page('paginas/testes.py', title='Teste de hipótese', icon="☑️")
    ]
}

# Execução da navegação
pag = st.navigation(paginas)
pag.run()
