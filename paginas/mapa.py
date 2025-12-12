import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- TÍTULO ---
st.header("🇧🇷 Painel Climático: Comparativo & Evolução")

# --- 1. CARREGAMENTO DOS DADOS (CACHEADO E OTIMIZADO) ---
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_dados_otimizados():
    # Lista de tentativas de caminho
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for caminho in caminhos:
        try:
            # Lê apenas as colunas necessárias para economizar memória
            cols = [
                'semana_ref', 'state', 'temperatura_media', 
                'chuva_media_semanal', 'umidade_media', 
                'vento_medio', 'radiacao_media'
            ]
            df = pd.read_csv(caminho, usecols=cols)
            break
        except FileNotFoundError:
            continue
            
    if df is None:
        st.error("❌ Erro: Arquivo CSV não encontrado.")
        st.stop()

    try:
        # Conversão Otimizada
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['Ano'] = df['semana_ref'].dt.year.astype('int16') # Menos memória
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Otimização de Memória: Converter texto para categoria
        df['state'] = df['state'].astype('category')
        
        # Função simples de estação
        def get_estacao_rapido(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.map(get_estacao_rapido).astype('category')
        
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao tratar dados: {e}")
        st.stop()

# --- 2. CARREGAMENTO DO MAPA (CACHEADO) ---
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_geojson():
    # GeoJSON simplificado
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

# Carregar dados na memória do servidor
df = carregar_dados_otimizados()
geojson_brasil = carregar_geojson()

# --- SIDEBAR (Leve) ---
st.sidebar.markdown("### ⚙️ Configurações")

variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}

var_label = st.sidebar.selectbox("Variável:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Cores
escala = "RdYlBu_r" if "temperatura" in var_col else ("Blues" if "chuva" in var_col else "Spectral_r")

# Limites globais (calculados uma vez)
min_g = df[var_col].min()
max_g = df[var_col].max()


# ==============================================================================
# PARTE 1: GRID COMPARATIVO (SIMPLIFICADO)
# ==============================================================================
st.subheader("🗓️ Comparativo Anual")

# Seletor de Estação
estacao_filtro = st.radio(
    "Filtrar Período:",
    ["Média do Ano", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

# Filtragem eficiente
df_grid = df if estacao_filtro == "Média do Ano" else df[df['Estacao'] == estacao_filtro]

# Grid de Mapas
anos = [2016, 2017, 2018, 2019, 2020, 2021]
colunas = st.columns(3)

for i, ano in enumerate(anos):
    col_idx = i % 3
    with colunas[col_idx]:
        # Agrupamento rápido
        df_ano = df_grid[df_grid['Ano'] == ano]
        
        # Check rápido para não processar vazio
        if df_ano.empty:
            st.info(f"{ano}: -")
            continue
            
        df_mapa = df_ano.groupby('state', observed=True)[var_col].mean().reset_index()
        
        fig = px.choropleth(
            df_mapa,
            geojson=geojson_brasil,
            locations='state',
            featureidkey="properties.sigla",
            color=var_col,
            color_continuous_scale=escala,
            range_color=[min_g, max_g],
            scope="south america",
            title=f"<b>{ano}</b>"
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, height=200, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# Legenda única leve
st.caption(f"Legenda Geral: {var_label}")
dummy = px.imshow([[min_g, max_g]], color_continuous_scale=escala)
dummy.update_layout(height=40, margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
dummy.update_traces(opacity=0, showscale=True, colorbar=dict(title=None, orientation='h', thickness=10))
dummy.update_xaxes(visible=False); dummy.update_yaxes(visible=False)
st.plotly_chart(dummy, use_container_width=True)

st.markdown("---")

# ==============================================================================
# PARTE 2: ANIMAÇÃO OTIMIZADA (POR ANO)
# ==============================================================================
st.subheader("🎞️ Linha do Tempo Evolutiva")

# Filtro de Ano para a Animação (ESSENCIAL PARA PERFORMANCE)
# Animar 6 anos de uma vez trava o navegador. Animar 1 ano é leve.
ano_animacao = st.select_slider("Selecione o Ano para Animar:", options=sorted(df['Ano'].unique()))

# Filtrar dados APENAS do ano selecionado
df_anim = df[df['Ano'] == ano_animacao].copy()

# Preparar dados agregados
df_agrupado = df_anim.groupby(['state', 'Mes_Ano'], observed=True)[var_col].mean().reset_index()
df_agrupado = df_agrupado.sort_values('Mes_Ano')

if not df_agrupado.empty:
    fig_anim = px.choropleth(
        df_agrupado,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        animation_frame="Mes_Ano", # Animação nativa (leve pois são poucos frames)
        color_continuous_scale=escala,
        range_color=[min_g, max_g],
        scope="south america",
        title=f"Evolução em {ano_animacao}",
        hover_data={var_col:':.1f'}
    )

    fig_anim.update_geos(fitbounds="locations", visible=False)
    fig_anim.update_layout(
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(title=None, orientation="h", y=-0.1, thickness=15),
        sliders=[{"pad": {"t": 30}}]
    )
    # Velocidade ideal
    fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500

    st.plotly_chart(fig_anim, use_container_width=True)
else:
    st.warning(f"Sem dados detalhados para {ano_animacao}")
