import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CONFIGURAÇÃO INICIAL ---
st.header("🗺️ Mapa Climático por País (Sazonal)")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_mapa():
    try:
        df = pd.read_csv("dataframe/dados_AS.csv")
        
        # 1. Filtrar Colômbia
        df = df[df['country'] != 'Colombia']
        
        # 2. Converter data
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        
        # 3. Criar coluna de data formatada (para o slider)
        # Vamos usar MÊS/ANO para a animação ficar mais fluida e agrupar melhor
        df['Data_Formatada'] = df['last_updated'].dt.strftime('%Y-%m-%d')
        
        # Ordenar
        df = df.sort_values('last_updated')
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'dataframe/dados_AS.csv' não encontrado.")
        return pd.DataFrame()

df = carregar_dados_mapa()

if df.empty:
    st.stop()

# --- SIDEBAR: CONFIGURAÇÕES ---
st.sidebar.markdown("### Configurações do Mapa")

# Dicionário de Variáveis
variaveis = {
    "Temperatura (°C)": "temperature_celsius",
    "Precipitação (mm)": "precip_mm",
    "Umidade (%)": "humidity",
    "Vento (km/h)": "wind_kph",
    "Pressão (in)": "pressure_in",
    "Nuvens (%)": "cloud",
    "Sensação Térmica (°C)": "feels_like_celsius",
    "Índice UV": "uv_index"
}

# Dicionário de Cores
cores_mapa = {
    "temperature_celsius": "RdYlBu_r", # Vermelho = Quente
    "precip_mm": "Blues",              # Azul escuro = Muita chuva
    "humidity": "Teal",
    "wind_kph": "Viridis",
    "cloud": "Greys",
    "uv_index": "Magma",
    "feels_like_celsius": "RdYlBu_r"
}

var_selecionada = st.sidebar.selectbox(
    "Selecione a Variável:", 
    options=list(variaveis.keys())
)
coluna_dados = variaveis[var_selecionada]
escala_cor = cores_mapa.get(coluna_dados, "Viridis")

# Calcular Min/Max global para fixar a escala de cores (evita piscar na animação)
min_global = df[coluna_dados].min()
max_global = df[coluna_dados].max()

# --- 1. MAPA GERAL (MÉDIA DO PERÍODO TODO) ---
st.subheader(f"🌎 Média Geral por País: {var_selecionada}")

# Agrupar por PAÍS (Média de todas as datas e cidades daquele país)
df_pais_geral = df.groupby('country')[coluna_dados].mean().reset_index()

fig_geral = px.choropleth(
    df_pais_geral,
    locations="country",        # Nome do país na coluna 'country'
    locationmode="country names", # Plotly entende nomes em inglês (Brazil, Argentina...)
    color=coluna_dados,
    scope="south america",      # Foca na América do Sul
    color_continuous_scale=escala_cor,
    range_color=[min_global, max_global],
    title=f"Média Geral ({var_selecionada})",
    labels={coluna_dados: var_selecionada}
)
fig_geral.update_geos(fitbounds="locations", visible=False) # Ajusta zoom automático
fig_geral.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

st.plotly_chart(fig_geral, use_container_width=True)

st.markdown("---")

# --- 2. ANIMAÇÃO NO TEMPO ---
st.subheader(f"📅 Evolução Temporal: {var_selecionada}")

datas_unicas = df['Data_Formatada'].unique()

# Controles de Animação
col_play, col_slider = st.columns([1, 4])

# Estado da sessão para animação
if 'animacao_ativa' not in st.session_state:
    st.session_state.animacao_ativa = False
if 'indice_tempo' not in st.session_state:
    st.session_state.indice_tempo = 0

with col_play:
    label_botao = "⏸️ Parar" if st.session_state.animacao_ativa else "▶️ Play"
    if st.button(label_botao):
        st.session_state.animacao_ativa = not st.session_state.animacao_ativa

# Lógica do Loop
if st.session_state.animacao_ativa:
    if st.session_state.indice_tempo < len(datas_unicas) - 1:
        st.session_state.indice_tempo += 1
    else:
        st.session_state.indice_tempo = 0 # Loop infinito
    time.sleep(0.5) # Velocidade da animação
    st.rerun()

with col_slider:
    data_escolhida = st.select_slider(
        "Linha do Tempo",
        options=datas_unicas,
        value=datas_unicas[st.session_state.indice_tempo],
        key="slider_tempo_mapa"
    )
    # Sincroniza slider manual
    st.session_state.indice_tempo = list(datas_unicas).index(data_escolhida)

# --- PROCESSAMENTO DOS DADOS DO DIA ---
# 1. Filtra a data
df_dia = df[df['Data_Formatada'] == data_escolhida]

# 2. Agrupa por PAÍS (Média das cidades daquele país naquele dia)
df_dia_pais = df_dia.groupby('country')[coluna_dados].mean().reset_index()

if not df_dia_pais.empty:
    fig_animado = px.choropleth(
        df_dia_pais,
        locations="country",
        locationmode="country names",
        color=coluna_dados,
        scope="south america",
        color_continuous_scale=escala_cor,
        range_color=[min_global, max_global], # Escala fixa é crucial para animação
        title=f"Situação em: {data_escolhida}",
        labels={coluna_dados: var_selecionada}
    )
    
    # Ajustes visuais finos
    fig_animado.update_geos(
        fitbounds="locations", 
        visible=False, 
        showcountries=True, 
        countrycolor="white" # Linha branca entre países fica bonito
    )
    fig_animado.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    
    st.plotly_chart(fig_animado, use_container_width=True)
else:
    st.warning(f"Sem dados disponíveis para {data_escolhida}")

# Tabela auxiliar (opcional)
with st.expander("Ver dados detalhados desta data (Médias por País)"):
    st.dataframe(df_dia_pais)
