import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(layout="wide") # Descomente se rodar isolado

st.header("🇧🇷 Painel Climático: Comparativo & Evolução")

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
@st.cache_data
def carregar_dados():
    # Tenta carregar de possíveis locais (raiz ou pasta dataframe)
    arquivos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for arq in arquivos:
        try:
            df = pd.read_csv(arq)
            break
        except FileNotFoundError:
            continue
            
    if df is None:
        st.error("Erro: Arquivo 'clima_brasil_semanal_refinado_2015.csv' não encontrado.")
        return pd.DataFrame()

    try:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Criar colunas de tempo
        df['Ano'] = df['semana_ref'].dt.year
        df['Mes'] = df['semana_ref'].dt.month
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m') 
        
        # Definir Estações (Hemisfério Sul)
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.apply(get_estacao)
        
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

df = carregar_dados()
geojson_brasil = carregar_geojson()

if df.empty:
    st.stop()

# --- SIDEBAR: VARIÁVEIS ---
st.sidebar.markdown("### ⚙️ Configurações")

variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação Solar": "radiacao_media"
}

var_label = st.sidebar.selectbox("Escolha a Variável:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Definição de Cores
if "temperatura" in var_col:
    escala = "RdYlBu_r"
elif "chuva" in var_col:
    escala = "Blues"
elif "umidade" in var_col:
    escala = "Teal"
else:
    escala = "Spectral_r"

# Calcular Min/Max Global
min_global = df[var_col].min()
max_global = df[var_col].max()


# ==============================================================================
# SEÇÃO 1: GRID COMPARATIVO (2016-2021)
# ==============================================================================
st.markdown("### 🗓️ Comparativo Anual (2016 - 2021)")

# Filtro de Estação
estacao_selecionada = st.radio(
    "Filtrar Período:",
    ["Média do Ano", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

# Filtrar dados baseado na seleção
df_grid = df.copy()
if estacao_selecionada != "Média do Ano":
    df_grid = df_grid[df_grid['Estacao'] == estacao_selecionada]

# Layout de Grid (2 linhas x 3 colunas)
anos_grid = [2016, 2017, 2018, 2019, 2020, 2021]

row1 = st.columns(3)
row2 = st.columns(3)
colunas_grid = row1 + row2

for i, ano in enumerate(anos_grid):
    with colunas_grid[i]:
        df_ano = df_grid[df_grid['Ano'] == ano]
        df_mapa_ano = df_ano.groupby('state')[var_col].mean().reset_index()
        
        if not df_mapa_ano.empty:
            fig = px.choropleth(
                df_mapa_ano,
                geojson=geojson_brasil,
                locations='state',
                featureidkey="properties.sigla",
                color=var_col,
                color_continuous_scale=escala,
                range_color=[min_global, max_global], 
                scope="south america",
                title=f"<b>{ano}</b>"
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                margin={"r":0,"t":30,"l":0,"b":0},
                coloraxis_showscale=False, # Esconde a barra individual
                height=200
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Sem dados ({ano})")

# --- BARRA DE CORES UNIFICADA (CORREÇÃO DO ERRO) ---
st.caption(f"Escala de Cores: {var_label}")

# Cria uma figura "falsa" apenas para exibir a barra de cores horizontalmente
# Corrigimos o height=0 para height=50 e ajustamos a visibilidade
dummy_fig = px.imshow(
    [[min_global, max_global]], 
    color_continuous_scale=escala
)
dummy_fig.update_traces(opacity=0) # Esconde os pixels, mostra só a barra
dummy_fig.update_xaxes(visible=False)
dummy_fig.update_yaxes(visible=False)
dummy_fig.update_layout(
    height=50, # Altura mínima válida
    margin={"r":10,"t":0,"l":10,"b":0},
    coloraxis_showscale=False # Desativa a padrão do layout para controlar no trace
)
# Força a barra de cores a aparecer horizontalmente
dummy_fig.update_traces(
    showscale=True,
    colorbar=dict(
        title=None,
        orientation='h',
        thickness=20,
        yanchor="middle",
        y=0.5,
        len=1.0 # Largura total
    )
)
st.plotly_chart(dummy_fig, use_container_width=True)


st.markdown("---")

# ==============================================================================
# SEÇÃO 2: MAPA INTERATIVO
# ==============================================================================
st.markdown("### 🎞️ Evolução Histórica Detalhada")

timeline = sorted(df['Mes_Ano'].unique())

col_play, col_slider = st.columns([1, 6])

if 'anim_index' not in st.session_state:
    st.session_state.anim_index = 0
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

with col_play:
    st.write("")
    st.write("")
    label_btn = "⏹️ Parar" if st.session_state.is_playing else "▶️ Reproduzir"
    if st.button(label_btn, use_container_width=True):
        st.session_state.is_playing = not st.session_state.is_playing

if st.session_state.is_playing:
    if st.session_state.anim_index < len(timeline) - 1:
        st.session_state.anim_index += 1
    else:
        st.session_state.anim_index = 0
    time.sleep(0.4)
    st.rerun()

with col_slider:
    mes_selecionado = st.select_slider(
        "",
        options=timeline,
        value=timeline[st.session_state.anim_index]
    )
    st.session_state.anim_index = timeline.index(mes_selecionado)

# Mapa Grande
df_mes = df[df['Mes_Ano'] == mes_selecionado]
df_mapa_mes = df_mes.groupby('state')[var_col].mean().reset_index()

if not df_mapa_mes.empty:
    estacao_atual = df_mes['Estacao'].iloc[0]
    fig_grande = px.choropleth(
        df_mapa_mes,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        color_continuous_scale=escala,
        range_color=[min_global, max_global],
        scope="south america",
        title=f"Brasil em {mes_selecionado} ({estacao_atual})",
        hover_data={var_col:':.2f'}
    )
    fig_grande.update_geos(fitbounds="locations", visible=False)
    fig_grande.update_layout(
        height=600,
        margin={"r":0,"t":40,"l":0,"b":0},
        coloraxis_colorbar=dict(title=var_label, orientation="h", y=-0.1)
    )
    st.plotly_chart(fig_grande, use_container_width=True)
else:
    st.warning("Sem dados para este período.")
