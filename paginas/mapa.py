import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

# --- TÍTULO ---
st.header("🇧🇷 Painel Climático: Comparativo & Evolução")

# --- 1. CARREGAMENTO DOS DADOS (ROBUSTO) ---
@st.cache_data
def carregar_dados():
    # Tenta ler de diferentes caminhos para garantir que encontre o arquivo
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for caminho in caminhos:
        try:
            df = pd.read_csv(caminho)
            break
        except FileNotFoundError:
            continue
            
    if df is None:
        st.error("❌ Erro Crítico: Arquivo CSV não encontrado. Verifique se ele está na pasta 'dataframe'.")
        st.stop()

    try:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['Ano'] = df['semana_ref'].dt.year
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m') 
        
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.apply(get_estacao)
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao tratar dados: {e}")
        st.stop()

# --- 2. CARREGAMENTO DO MAPA (GEOJSON CONFIÁVEL) ---
@st.cache_data
def carregar_geojson():
    # Link direto para o GeoJSON dos estados brasileiros (IBGE Simplificado)
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        response = requests.get(url)
        response.raise_for_status() # Garante que não deu 404
        return response.json()
    except Exception as e:
        st.error(f"Erro ao baixar mapa: {e}")
        st.stop()

df = carregar_dados()
geojson_brasil = carregar_geojson()

# --- SIDEBAR: CONFIGURAÇÕES ---
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

# Calcular limites globais para consistência visual
min_g = df[var_col].min()
max_g = df[var_col].max()


# ==============================================================================
# PARTE 1: GRID COMPARATIVO (ESTÁTICO)
# ==============================================================================
st.subheader("🗓️ Comparativo Anual")

estacao_filtro = st.radio(
    "Filtrar Período:",
    ["Média do Ano", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

df_grid = df.copy()
if estacao_filtro != "Média do Ano":
    df_grid = df_grid[df_grid['Estacao'] == estacao_filtro]

# Grid 2x3 (Anos 2016 a 2021)
anos = [2016, 2017, 2018, 2019, 2020, 2021]
colunas = st.columns(3)

for i, ano in enumerate(anos):
    col_idx = i % 3
    with colunas[col_idx]:
        df_ano = df_grid[df_grid['Ano'] == ano]
        df_mapa = df_ano.groupby('state')[var_col].mean().reset_index()
        
        if not df_mapa.empty:
            fig = px.choropleth(
                df_mapa,
                geojson=geojson_brasil,
                locations='state',
                featureidkey="properties.sigla",
                color=var_col,
                color_continuous_scale=escala,
                range_color=[min_g, max_g], # Trava a escala de cor
                scope="south america",
                title=f"<b>{ano}</b>"
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                margin={"r":0,"t":30,"l":0,"b":0},
                height=200,
                coloraxis_showscale=False # Esconde a barra lateral individual
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"{ano}: Sem dados")

# Legenda Geral (Barra de Cores)
st.caption(f"Legenda Geral: {var_label}")
dummy = px.imshow([[min_g, max_g]], color_continuous_scale=escala)
dummy.update_layout(height=40, margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
dummy.update_traces(opacity=0, showscale=True, colorbar=dict(title=None, orientation='h', thickness=15, y=0.5))
dummy.update_xaxes(visible=False); dummy.update_yaxes(visible=False)
st.plotly_chart(dummy, use_container_width=True)

st.markdown("---")

# ==============================================================================
# PARTE 2: MAPA ANIMADO (PLAYER NATIVO DO PLOTLY)
# ==============================================================================
st.subheader("🎞️ Linha do Tempo Evolutiva")
st.info("Aperte o **Play** abaixo para ver a evolução mês a mês sem travamentos.")

# 1. Preparar dados agregados para animação
# Agrupamos por Estado e Mês de uma vez só
df_animacao = df.groupby(['state', 'Mes_Ano'])[var_col].mean().reset_index()
df_animacao = df_animacao.sort_values('Mes_Ano')

# 2. Criar gráfico com animation_frame (Renderização no navegador = Rápido!)
if not df_animacao.empty:
    fig_anim = px.choropleth(
        df_animacao,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        animation_frame="Mes_Ano", # <--- A MÁGICA ESTÁ AQUI
        color_continuous_scale=escala,
        range_color=[min_g, max_g],
        scope="south america",
        title=f"Evolução Temporal: {var_label}",
        hover_data={var_col:':.2f'}
    )

    # 3. Ajustes Finais de Estética e Performance
    fig_anim.update_geos(fitbounds="locations", visible=False)
    fig_anim.update_layout(
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title=None, 
            orientation="h", 
            y=-0.15 # Barra de cores embaixo
        ),
        sliders=[{"pad": {"t": 30}}] # Espaço para o slider não encostar no mapa
    )

    # Ajustar velocidade da animação (frame duration em milissegundos)
    fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 300

    st.plotly_chart(fig_anim, use_container_width=True)
else:
    st.error("Não há dados suficientes para gerar a animação.")
