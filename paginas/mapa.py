import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
# (Se não estiver no app.py, descomente a linha abaixo)
# st.set_page_config(layout="wide")

st.header("🇧🇷 Painel Climático: Comparativo & Evolução")

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
@st.cache_data
def carregar_dados():
    try:
        # Carrega o dataset do Brasil
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Criar colunas de tempo
        df['Ano'] = df['semana_ref'].dt.year
        df['Mes'] = df['semana_ref'].dt.month
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m') # Para o slider
        
        # Definir Estações (Hemisfério Sul)
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.apply(get_estacao)
        
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_geojson():
    # Mapa dos estados brasileiros
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

# Calcular Min/Max Global (para manter as cores consistentes em todos os mapas)
# Isso é crucial para poder comparar 2016 com 2021 visualmente
min_global = df[var_col].min()
max_global = df[var_col].max()


# ==============================================================================
# SEÇÃO 1: GRID COMPARATIVO (2016-2021)
# ==============================================================================
st.markdown("### 🗓️ Comparativo Anual (2016 - 2021)")

# Filtro de Estação (Botões em cima)
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

# Criar containers para as linhas
row1 = st.columns(3)
row2 = st.columns(3)
colunas_grid = row1 + row2 # Lista com as 6 colunas

for i, ano in enumerate(anos_grid):
    with colunas_grid[i]:
        # Filtrar o ano específico
        df_ano = df_grid[df_grid['Ano'] == ano]
        
        # Agrupar média por estado
        df_mapa_ano = df_ano.groupby('state')[var_col].mean().reset_index()
        
        if not df_mapa_ano.empty:
            fig = px.choropleth(
                df_mapa_ano,
                geojson=geojson_brasil,
                locations='state',
                featureidkey="properties.sigla",
                color=var_col,
                color_continuous_scale=escala,
                range_color=[min_global, max_global], # Escala fixa!
                scope="south america",
                title=f"<b>{ano}</b>" # Título em negrito
            )
            
            # Limpar visual do mapa pequeno
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                margin={"r":0,"t":30,"l":0,"b":0},
                coloraxis_showscale=False, # Esconde a barra de cores individual (poluição visual)
                height=250 # Altura fixa pequena
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Sem dados para {ano}")

# Barra de cores (legenda) única para o grid
st.caption(f"Escala de Cores para todos os mapas acima ({var_label})")
# (Truque para mostrar só a barra de cores)
dummy_fig = px.imshow([[min_global, max_global]], color_continuous_scale=escala)
dummy_fig.update_layout(height=0, coloraxis_showscale=True, margin={"r":0,"t":0,"l":0,"b":0})
# st.plotly_chart(dummy_fig, use_container_width=True) # Opcional


st.markdown("---")


# ==============================================================================
# SEÇÃO 2: MAPA INTERATIVO (EVOLUÇÃO TEMPORAL)
# ==============================================================================
st.markdown("### 🎞️ Evolução Histórica Detalhada")

# Preparar linha do tempo completa
timeline = sorted(df['Mes_Ano'].unique())

# Controles de Animação
col_play, col_slider = st.columns([1, 6])

if 'anim_index' not in st.session_state:
    st.session_state.anim_index = 0
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

with col_play:
    st.write("") # Espaçamento
    st.write("")
    label_btn = "⏹️ Parar" if st.session_state.is_playing else "▶️ Reproduzir"
    if st.button(label_btn, use_container_width=True):
        st.session_state.is_playing = not st.session_state.is_playing

# Lógica de Loop
if st.session_state.is_playing:
    if st.session_state.anim_index < len(timeline) - 1:
        st.session_state.anim_index += 1
    else:
        st.session_state.anim_index = 0 # Reinicia
    time.sleep(0.4) # Velocidade
    st.rerun()

with col_slider:
    mes_selecionado = st.select_slider(
        "",
        options=timeline,
        value=timeline[st.session_state.anim_index]
    )
    # Sincroniza slider manual
    st.session_state.anim_index = timeline.index(mes_selecionado)

# --- PLOTAGEM DO MAPA GRANDE ---
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
        height=600, # Mapa maior
        margin={"r":0,"t":40,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title=var_label,
            thickness=20,
            len=0.5,
            yanchor="bottom", y=0,
            xanchor="right", x=0.95
        )
    )
    
    st.plotly_chart(fig_grande, use_container_width=True)
else:
    st.warning("Sem dados para este período.")
