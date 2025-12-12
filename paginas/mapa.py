import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests

# --- CONFIGURAÇÃO INICIAL ---
st.header("🇧🇷 Evolução Climática Histórica (2015-2021)")

# --- 1. CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_brasil():
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Criar coluna Ano-Mês para agrupar (Ex: "2015-01")
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Definir Estação (Aprox.)
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

# --- 2. CARREGAMENTO DO MAPA (GEOJSON) ---
@st.cache_data
def carregar_geojson_brasil():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

df = carregar_dados_brasil()
geojson_brasil = carregar_geojson_brasil()

if df.empty:
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Variável")
variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}
var_label = st.sidebar.selectbox("Escolha o indicador:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Cores
if "temperatura" in var_col:
    escala = "RdYlBu_r"
elif "chuva" in var_col or "umidade" in var_col:
    escala = "Blues"
else:
    escala = "Spectral_r"

# Calcular limites globais para a cor não "piscar"
min_g = df[var_col].min()
max_g = df[var_col].max()

# --- PREPARAÇÃO DA LINHA DO TEMPO ---
# Lista ordenada de todos os meses disponíveis (Jan/2015 a Abr/2021)
timeline = sorted(df['Mes_Ano'].unique())

# --- CONTROLES DE ANIMAÇÃO ---
st.markdown("### 🎮 Controle do Tempo")

# Container para os controles ficarem lado a lado
col1, col2 = st.columns([1, 6])

# Estado da Animação
if 'anim_index' not in st.session_state:
    st.session_state.anim_index = 0
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

with col1:
    st.write("") # Espaço para alinhar
    st.write("")
    # Botão Play/Pause
    btn_label = "⏸️ Parar" if st.session_state.is_playing else "▶️ Iniciar"
    if st.button(btn_label, use_container_width=True):
        st.session_state.is_playing = not st.session_state.is_playing

# Lógica de Loop
if st.session_state.is_playing:
    if st.session_state.anim_index < len(timeline) - 1:
        st.session_state.anim_index += 1
    else:
        st.session_state.anim_index = 0 # Loop
    time.sleep(0.3) # Velocidade da animação
    st.rerun()

with col2:
    # Slider que controla tudo
    mes_selecionado = st.select_slider(
        "",
        options=timeline,
        value=timeline[st.session_state.anim_index],
        key="main_slider"
    )
    # Sincronizar slider manual com o índice da animação
    st.session_state.anim_index = timeline.index(mes_selecionado)

# --- PROCESSAMENTO DOS DADOS DO MÊS ---
df_mes = df[df['Mes_Ano'] == mes_selecionado]
# Agrupar por Estado (Média do mês)
df_mapa = df_mes.groupby('state')[var_col].mean().reset_index()

# Definir Estação do ano atual para exibir no título
estacao_atual = df_mes['Estacao'].iloc[0] if not df_mes.empty else ""

# --- LAYOUT DOS GRÁFICOS ---
col_mapa, col_grafico = st.columns([3, 2])

with col_mapa:
    # 1. MAPA
    fig_map = px.choropleth(
        df_mapa,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        color_continuous_scale=escala,
        range_color=[min_g, max_g], # Escala fixa
        title=f"Brasil em {mes_selecionado} ({estacao_atual})",
        labels={var_col: var_label}
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        coloraxis_colorbar=dict(title=None, orientation="h", y=-0.1) # Barra de cores embaixo
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_grafico:
    # 2. GRÁFICO DE TENDÊNCIA (MINI)
    # Mostra a média nacional ao longo do tempo e destaca o ponto atual
    st.write(f"**Tendência Nacional: {var_label}**")
    
    # Média Brasil por mês
    df_tendencia = df.groupby('Mes_Ano')[var_col].mean().reset_index()
    
    fig_line = px.line(df_tendencia, x='Mes_Ano', y=var_col)
    
    # Adicionar um ponto vermelho no mês atual da animação
    fig_line.add_scatter(
        x=[mes_selecionado], 
        y=[df_tendencia[df_tendencia['Mes_Ano'] == mes_selecionado][var_col].values[0]],
        mode='markers', 
        marker=dict(color='red', size=12),
        name='Atual'
    )
    
    fig_line.update_layout(
        xaxis_title=None, 
        yaxis_title=None, 
        showlegend=False,
        height=350,
        margin={"r":10,"t":10,"l":10,"b":10}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 3. TOP ESTADOS (Ranking)
    st.write(f"**Estados com maior {var_label} em {mes_selecionado}**")
    top_5 = df_mapa.nlargest(5, var_col)[['state', var_col]]
    st.dataframe(
        top_5, 
        hide_index=True, 
        column_config={
            "state": "Estado",
            var_col: st.column_config.NumberColumn(var_label, format="%.1f")
        },
        use_container_width=True
    )
