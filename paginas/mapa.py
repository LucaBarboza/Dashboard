import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CONFIGURAÇÃO INICIAL ---
st.header("🗺️ Mapa Climático Espaço-Temporal")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_mapa():
    try:
        df = pd.read_csv("dataframe/dados_AS.csv")
        
        # Filtrar Colômbia (conforme solicitado)
        df = df[df['country'] != 'Colombia']
        
        # Converter data
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        
        # Criar coluna de período (Ano-Mês-Dia ou apenas Mês para agrupar)
        # Vamos usar Dia para precisão, ou Mês se quiser menos "frames"
        df['Data_Formatada'] = df['last_updated'].dt.strftime('%Y-%m-%d')
        
        # Ordenar por data
        df = df.sort_values('last_updated')
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'dataframe/dados_AS.csv' não encontrado.")
        return pd.DataFrame()

df = carregar_dados_mapa()

if df.empty:
    st.stop()

# --- SIDEBAR: CONFIGURAÇÕES DE VISUALIZAÇÃO ---
st.sidebar.markdown("### Configurações do Mapa")

# Dicionário de Variáveis (Nome Bonito -> Nome da Coluna)
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

# Dicionário de Cores para cada variável (Estética)
cores_mapa = {
    "temperature_celsius": "RdYlBu_r", # Vermelho para quente
    "precip_mm": "Blues",              # Azul para chuva
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

# --- 1. GRÁFICO GERAL (MÉDIA POR LOCALIZAÇÃO) ---
st.subheader(f"📍 Visão Geral Média: {var_selecionada}")

# Agrupar por Localização para tirar a média de todo o período
df_medio = df.groupby(['location_name', 'country', 'latitude', 'longitude'])[coluna_dados].mean().reset_index()

fig_geral = px.scatter_mapbox(
    df_medio,
    lat="latitude",
    lon="longitude",
    color=coluna_dados,
    size=coluna_dados, # O tamanho da bolinha também varia com o valor
    hover_name="location_name",
    hover_data={"country": True, "latitude": False, "longitude": False},
    color_continuous_scale=escala_cor,
    size_max=15,
    zoom=2.5,
    mapbox_style="carto-positron", # Estilo de mapa clean e gratuito
    title=f"Média de {var_selecionada} por Cidade (Todo o Período)"
)
fig_geral.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig_geral, use_container_width=True)

st.markdown("---")

# --- 2. ANIMAÇÃO TEMPORAL (CONTROLES MANUAIS) ---
st.subheader(f"⏳ Evolução no Tempo: {var_selecionada}")

# Criar lista de datas únicas para o slider
datas_unicas = df['Data_Formatada'].unique()

# --- CONTROLES DE ANIMAÇÃO ---
col_play, col_slider = st.columns([1, 4])

# Inicializar estado da animação
if 'animacao_ativa' not in st.session_state:
    st.session_state.animacao_ativa = False
if 'indice_tempo' not in st.session_state:
    st.session_state.indice_tempo = 0

with col_play:
    # Botão Play/Pause
    label_botao = "⏸️ Parar" if st.session_state.animacao_ativa else "▶️ Iniciar Animação"
    if st.button(label_botao):
        st.session_state.animacao_ativa = not st.session_state.animacao_ativa

# Lógica de Loop da Animação
if st.session_state.animacao_ativa:
    # Incrementa o índice
    if st.session_state.indice_tempo < len(datas_unicas) - 1:
        st.session_state.indice_tempo += 1
    else:
        st.session_state.indice_tempo = 0 # Reinicia o loop
    # Pequena pausa para visualização
    time.sleep(0.3) 
    # Força o recarregamento da página para atualizar o slider e o mapa
    st.rerun()

with col_slider:
    # Slider que permite mexer manualmente (e atualiza com o Play)
    data_escolhida = st.select_slider(
        "Linha do Tempo",
        options=datas_unicas,
        value=datas_unicas[st.session_state.indice_tempo],
        key="slider_tempo" # Chave para conectar com session_state se necessário
    )
    # Sincronizar slider manual com o índice do play
    idx_atual = list(datas_unicas).index(data_escolhida)
    st.session_state.indice_tempo = idx_atual

# --- FILTRAR E PLOTAR O MAPA DO DIA ---
df_dia = df[df['Data_Formatada'] == data_escolhida]

if not df_dia.empty:
    # Definir limites de cor fixos (min e max globais) para a cor não "piscar" na animação
    v_min = df[coluna_dados].min()
    v_max = df[coluna_dados].max()

    fig_animado = px.scatter_mapbox(
        df_dia,
        lat="latitude",
        lon="longitude",
        color=coluna_dados,
        size=coluna_dados,
        hover_name="location_name",
        hover_data={"country": True, "time": df_dia['last_updated'].dt.strftime('%H:%M')},
        color_continuous_scale=escala_cor,
        range_color=[v_min, v_max], # Fixar escala de cor
        size_max=20,
        zoom=2.5,
        mapbox_style="carto-positron",
        title=f"Situação em: {data_escolhida}"
    )
    fig_animado.update_layout(transition={'duration': 50}) # Suavizar transição
    fig_animado.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    
    st.plotly_chart(fig_animado, use_container_width=True)
else:
    st.warning("Sem dados para esta data.")

# Informação extra sobre os dados
with st.expander("Ver dados brutos desta data"):
    st.dataframe(df_dia[['country', 'location_name', 'last_updated', coluna_dados]])
