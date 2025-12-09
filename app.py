import streamlit as st
import pandas as pd
import plotly.express as px

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

@st.cache_data
def carregar_dados_reais():
    # Lê o arquivo CSV enviado
    df = pd.read_csv("dataframe/dados_AS.csv")
    
    # Conversão de data
    df['last_updated'] = pd.to_datetime(df['last_updated'])
    
    # Criando colunas de tempo
    df['Mes_Ano'] = df['last_updated'].dt.strftime('%Y-%m')
    df['Data_Simples'] = df['last_updated'].dt.date
    
    return df

# Carrega os dados
df = carregar_dados_reais()

# Deixando os nomes mais bonitos no seletor
cols_numericas = {
    'Vento (km/h)': 'wind_kph',
    'Pressão (in)': 'pressure_in', 
    'Precipitação (mm)': 'precip_mm', 
    'Umidade (%)': 'humidity', 
    'Cobertura de Nuvens (%)': 'cloud',
    'Índice UV': 'uv_index',
    'Sensação Térmica (C)': 'feels_like_celsius'
}

# Execução da navegação
pag = st.navigation(paginas)
pag.run()
