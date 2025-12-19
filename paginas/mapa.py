import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(layout="wide")
config_padrao = {
    'scrollZoom': False,
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
        'toImage', 'toggleHover'
    ]
}

st.header("🌍 Mapa Animado: Evolução Climática")

# --- 1. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados_mapa():
    try:
        try:
            df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        except:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
            
        if 'semana_ref' in df.columns:
            df['semana_ref'] = pd.to_datetime(df['semana_ref'])
            df['ano'] = df['semana_ref'].dt.year
            df['mes'] = df['semana_ref'].dt.month
            
            # --- CRIAÇÃO DA COLUNA DE PERÍODO (YYYY-MM) ---
            # Isso garante que 2015-02 venha depois de 2015-01 na animação
            df['periodo'] = df['semana_ref'].dt.strftime('%Y-%m') 
            
            def get_estacao(m):
                if m in [12, 1, 2]: return "Verão"
                elif m in [3, 4, 5]: return "Outono"
                elif m in [6, 7, 8]: return "Inverno"
                else: return "Primavera"
            df['estacao'] = df['mes'].apply(get_estacao)
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

@st.cache_data(ttl=3600)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Erro ao baixar mapa (GeoJSON): {e}")
    return None

df = carregar_dados_mapa()
geojson = carregar_geojson()

if geojson is None: st.stop()

# --- 2. ESCALAS GLOBAIS (TRAVAMENTO) ---
global_ranges = {
    "temperatura_media": [df['temperatura_media'].min(), df['temperatura_media'].max()],
    "chuva_media_semanal": [df['chuva_media_semanal'].min(), df['chuva_media_semanal'].max()],
    "umidade_media": [df['umidade_media'].min(), df['umidade_media'].max()],
    "vento_medio": [df['vento_medio'].min(), df['vento_medio'].max()],
    "radiacao_media": [df['radiacao_media'].min(), df['radiacao_media'].max()]
}

# --- 3. SIDEBAR ---
st.sidebar.header("Configurações")
variaveis = {
    "Temperatura (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}
var_label = st.sidebar.selectbox("O que você quer visualizar?", list(variaveis.keys()))
var_col = variaveis[var_label]

if "chuva" in var_col: escala = "Blues"
elif "temperatura" in var_col: escala = "RdYlBu_r" 
elif "umidade" in var_col: escala = "YlGnBu"
else: escala = "Viridis"

# --- 4. ABAS ---
tab1, tab2 = st.tabs(["🍂 Por Estação (Anos)", "⏳ Linha do Tempo (Meses)"])

# === ABA 1: SAZONAL (Mantida igual) ===
with tab1:
    st.markdown(f"**Análise Sazonal:** Evolução ano a ano filtrada por estação.")
    estacao_selecionada = st.radio("Escolha a Estação:", ["Verão", "Outono", "Inverno", "Primavera"], horizontal=True)
    
    df_filtrado = df[df['estacao'] == estacao_selecionada].copy()
    df_animacao = df_filtrado.groupby(['ano', 'state'])[var_col].mean().reset_index()
    df_animacao = df_animacao.sort_values(['ano', 'state']) 

    fig1 = px.choropleth_mapbox(
        df_animacao, geojson=geojson, locations='state', featureidkey="properties.sigla",
        color=var_col, animation_frame="ano", color_continuous_scale=escala,
        range_color=global_ranges[var_col], mapbox_style="carto-positron",
        zoom=3.0, center={"lat": -15.0, "lon": -54.0}, opacity=0.9, height=550
    )
    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, dragmode=False, coloraxis_colorbar=dict(title=var_label))
    try: fig1.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    except: pass
    st.plotly_chart(fig1, use_container_width=True, config=config_padrao)

# === ABA 2: LINHA DO TEMPO COMPLETA (Alterada) ===
with tab2:
    st.markdown(f"**Linha do Tempo Completa:** De Jan/2015 até Abr/2021 sequencialmente.")
    
    # Agrupa por PERÍODO (YYYY-MM) e ESTADO
    df_timeline = df.groupby(['periodo', 'state'])[var_col].mean().reset_index()
    
    # ORDENAÇÃO CRÍTICA: O Plotly segue a ordem do DataFrame para montar a animação.
    # Como 'periodo' é texto "2015-01", "2015-02", a ordem alfabética funciona como ordem cronológica.
    df_timeline = df_timeline.sort_values(['periodo', 'state'])

    fig2 = px.choropleth_mapbox(
        df_timeline,
        geojson=geojson,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        animation_frame="periodo", # <--- AQUI ESTÁ O SEGREDO (YYYY-MM)
        color_continuous_scale=escala,
        range_color=global_ranges[var_col], # Mantém a escala travada
        mapbox_style="carto-positron",
        zoom=3.0,
        center={"lat": -15.0, "lon": -54.0},
        opacity=0.9,
        height=550
    )

    fig2.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        dragmode=False,
        coloraxis_colorbar=dict(title=var_label)
    )

    # Aumentei a velocidade (frame duration = 100ms) porque são muitos meses (70+)
    # Se ficar muito rápido, aumente para 200 ou 300
    try:
        fig2.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 100
        fig2.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 50
    except: pass

    st.plotly_chart(fig2, use_container_width=True, config=config_padrao)