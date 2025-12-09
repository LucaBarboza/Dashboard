import streamlit as st

st.set_page_config(
    page_title="Análise Climática",
    page_icon="⛅",
    layout="wide"
)

# Configuração da navegação entre páginas
paginas = {
    # Use aspas vazias aqui para "esconder" o título da seção
    "": [
        st.Page('paginas/home.py', title='Home', default=True),
    ],
    "Análise de dados": [
        st.Page('paginas/dashboard.py', title='Dashboard Interativo', default=False),
        st.Page('paginas/mapa.py', title='Mapa Temporal Climático', default=False)
    ]
}

# Execução da navegação
pag = st.navigation(paginas)
pag.run()
