import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import requests

# --- CONFIGURAÇÃO INICIAL ---
st.header("🇧🇷 Mapa Climático do Brasil (Sazonal)")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_brasil():
    try:
        # Lê o novo arquivo CSV
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")        
        # Converter data (semana_ref)
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Criar colunas auxiliares de tempo
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        df['Ano'] = df['semana_ref'].dt.year
        
        # Função para definir estação do ano (aprox. Hemisfério Sul)
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
            
        df['Estacao'] = df['semana_ref'].dt.month.apply(get_estacao)
        
        # Ordenar cronologicamente
        df = df.sort_values('semana_ref')
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'clima_brasil_semanal_refinado_2015.csv' não encontrado. Verifique a pasta.")
        return pd.DataFrame()

# --- CARREGAMENTO DA GEOMETRIA (MAPA DO BRASIL) ---
@st.cache_data
def carregar_geojson_brasil():
    # URL pública com o desenho dos estados brasileiros
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    response = requests.get(url)
    return response.json()

df = carregar_dados_brasil()
geojson_brasil = carregar_geojson_brasil()

if df.empty:
    st.stop()

# --- SIDEBAR: CONFIGURAÇÕES ---
st.sidebar.markdown("### ⚙️ Configurações do Mapa")

# Mapeamento: Nome Bonito -> Coluna do DataFrame
variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva Semanal (mm)": "chuva_media_semanal",
    "Umidade Relativa (%)": "umidade_media",
    "Vento Médio (m/s)": "vento_medio",
    "Radiação Solar": "radiacao_media",
    "Pressão Atmosférica": "pressao_media"
}

# Escolha da Variável
var_selecionada = st.sidebar.selectbox("Selecione a Variável:", options=list(variaveis.keys()))
coluna_dados = variaveis[var_selecionada]

# Definição Automática de Cores
if "temperatura" in coluna_dados:
    escala_cor = "RdYlBu_r" # Vermelho Quente / Azul Frio
elif "chuva" in coluna_dados or "umidade" in coluna_dados:
    escala_cor = "Blues"    # Tons de Azul
elif "radiacao" in coluna_dados:
    escala_cor = "Solar"    # Tons de Sol
else:
    escala_cor = "Viridis"  # Padrão para outros

# Filtro de Ano (para não ficar pesado demais se tiver muitos anos)
anos_disponiveis = sorted(df['Ano'].unique())
ano_selecionado = st.sidebar.select_slider("Filtrar por Ano (Opcional):", options=anos_disponiveis, value=anos_disponiveis[-1])

# Filtrar o DataFrame pelo ano selecionado (ou usar tudo se preferir)
df_ano = df[df['Ano'] == ano_selecionado]

# Calcular Min/Max global do ano para fixar a escala de cores
min_global = df_ano[coluna_dados].min()
max_global = df_ano[coluna_dados].max()

# --- 1. MAPA GERAL (MÉDIA DO ANO) ---
st.subheader(f"📅 Média Anual de {ano_selecionado} ({var_selecionada})")

# Agrupar por Estado
df_media_ano = df_ano.groupby('state')[coluna_dados].mean().reset_index()

fig_geral = px.choropleth(
    df_media_ano,
    geojson=geojson_brasil,
    locations='state',        # Coluna do DF com a sigla (ex: SP, BA)
    featureidkey="properties.sigla", # Onde está a sigla no GeoJSON
    color=coluna_dados,
    color_continuous_scale=escala_cor,
    range_color=[min_global, max_global],
    scope="south america",
    title=f"Média Anual por Estado ({ano_selecionado})"
)
# Ajustar o zoom para focar só no Brasil
fig_geral.update_geos(fitbounds="locations", visible=False)
fig_geral.update_layout(margin={"r":0,"t":30,"l":0,"b":0})

st.plotly_chart(fig_geral, use_container_width=True)

st.markdown("---")

# --- 2. ANIMAÇÃO NO TEMPO (Mês a Mês) ---
st.subheader(f"🎞️ Animação Mensal: {var_selecionada}")

# Criar lista de meses presentes no ano selecionado
meses_unicos = sorted(df_ano['Mes_Ano'].unique())

# --- CONTROLES DE ANIMAÇÃO ---
col_play, col_slider = st.columns([1, 4])

if 'animacao_br' not in st.session_state:
    st.session_state.animacao_br = False
if 'idx_mes_br' not in st.session_state:
    st.session_state.idx_mes_br = 0

# Botão Play
with col_play:
    st.write("")
    st.write("")
    btn_label = "⏹️ Parar" if st.session_state.animacao_br else "▶️ Reproduzir"
    if st.button(btn_label, key="btn_play_br"):
        st.session_state.animacao_br = not st.session_state.animacao_br

# Lógica do Loop
if st.session_state.animacao_br:
    if st.session_state.idx_mes_br < len(meses_unicos) - 1:
        st.session_state.idx_mes_br += 1
    else:
        st.session_state.idx_mes_br = 0 # Reinicia
    time.sleep(0.7)
    st.rerun()

# Slider Manual
with col_slider:
    mes_atual = st.select_slider(
        "Linha do Tempo",
        options=meses_unicos,
        value=meses_unicos[st.session_state.idx_mes_br],
        key="slider_br"
    )
    st.session_state.idx_mes_br = list(meses_unicos).index(mes_atual)

# --- PLOTAR O MAPA DO MÊS ---
# 1. Filtrar dados do mês
df_mes = df_ano[df_ano['Mes_Ano'] == mes_atual]

# 2. Agrupar média por estado naquele mês
df_mapa_mes = df_mes.groupby(['state', 'Estacao'])[coluna_dados].mean().reset_index()

if not df_mapa_mes.empty:
    estacao_atual = df_mapa_mes['Estacao'].iloc[0]
    
    fig_anim = px.choropleth(
        df_mapa_mes,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=coluna_dados,
        color_continuous_scale=escala_cor,
        range_color=[min_global, max_global], # Escala fixa para comparação justa
        title=f"Situação em {mes_atual} ({estacao_atual})",
        hover_name="state"
    )
    fig_anim.update_geos(fitbounds="locations", visible=False)
    fig_anim.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    
    st.plotly_chart(fig_anim, use_container_width=True)
else:
    st.warning(f"Sem dados para {mes_atual}")
