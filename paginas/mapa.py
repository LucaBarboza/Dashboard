import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(layout="wide") # Opcional: aumenta o espaço lateral
config_padrao = {
    'scrollZoom': False,
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
        'toImage', 'toggleHover'
    ]
}

# --- TÍTULO ---
st.header("🌍 Mapa Animado: Evolução Climática")
st.markdown("Navegue pelas abas abaixo para alternar entre a visão por **Estações** ou **Mensal**.")

# --- 1. CARREGAMENTO DE DADOS E GEOJSON ---
@st.cache_data(ttl=3600)
def carregar_dados_mapa():
    try:
        # Tenta carregar do caminho padrão ou raiz
        try:
            df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        except:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
            
        # Tratamento de Datas
        if 'semana_ref' in df.columns:
            df['semana_ref'] = pd.to_datetime(df['semana_ref'])
            df['ano'] = df['semana_ref'].dt.year
            df['mes'] = df['semana_ref'].dt.month
            
            # Função para Estação
            def get_estacao(m):
                if m in [12, 1, 2]: return "Verão"
                elif m in [3, 4, 5]: return "Outono"
                elif m in [6, 7, 8]: return "Inverno"
                else: return "Primavera"
            df['estacao'] = df['mes'].apply(get_estacao)
            
            # Mapeamento para nome do mês (para a animação mensal ficar bonita)
            mapa_meses = {1:'01-Jan', 2:'02-Fev', 3:'03-Mar', 4:'04-Abr', 5:'05-Mai', 6:'06-Jun',
                          7:'07-Jul', 8:'08-Ago', 9:'09-Set', 10:'10-Out', 11:'11-Nov', 12:'12-Dez'}
            df['nome_mes'] = df['mes'].map(mapa_meses)
            
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

if geojson is None:
    st.stop()

# --- 2. CÁLCULO DE ESCALAS GLOBAIS (TRAVAMENTO) ---
# Aqui definimos o min e max de TODO o histórico para cada variável.
# Isso garante que a cor vermelha signifique a mesma coisa em todas as abas.
global_ranges = {
    "temperatura_media": [df['temperatura_media'].min(), df['temperatura_media'].max()],
    "chuva_media_semanal": [df['chuva_media_semanal'].min(), df['chuva_media_semanal'].max()],
    "umidade_media": [df['umidade_media'].min(), df['umidade_media'].max()],
    "vento_medio": [df['vento_medio'].min(), df['vento_medio'].max()],
    "radiacao_media": [df['radiacao_media'].min(), df['radiacao_media'].max()]
}

# --- 3. CONTROLES GERAIS (SIDEBAR) ---
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

# Definição da Paleta de Cores (Baseada na variável escolhida)
if "chuva" in var_col:
    escala = "Blues"
elif "temperatura" in var_col:
    escala = "RdYlBu_r" 
elif "umidade" in var_col:
    escala = "YlGnBu"
else:
    escala = "Viridis"

# --- 4. CRIAÇÃO DAS ABAS ---
tab1, tab2 = st.tabs(["🍂 Por Estação (Anos)", "📅 Por Mês (Detalhado)"])

# ==========================================
# ABA 1: VISÃO SAZONAL (O que você já tinha)
# ==========================================
with tab1:
    st.markdown(f"**Análise Sazonal:** Veja como {var_label} mudou ao longo dos **Anos** para uma estação específica.")
    
    col_filtro1, col_filtro2 = st.columns([1, 3])
    with col_filtro1:
        estacao_selecionada = st.radio(
            "Escolha a Estação:",
            ["Verão", "Outono", "Inverno", "Primavera"],
            horizontal=False
        )
    
    # Processamento
    df_filtrado = df[df['estacao'] == estacao_selecionada].copy()
    # Agrupa por ANO e ESTADO
    df_animacao = df_filtrado.groupby(['ano', 'state'])[var_col].mean().reset_index()
    df_animacao = df_animacao.sort_values(['ano', 'state']) # Ordenação para estabilidade

    # Gráfico Tab 1
    fig1 = px.choropleth_mapbox(
        df_animacao,
        geojson=geojson,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        animation_frame="ano", # Animação corre pelos ANOS
        color_continuous_scale=escala,
        range_color=global_ranges[var_col], # <--- TRAVAMENTO DE ESCALA AQUI
        mapbox_style="carto-positron",
        zoom=3.0,
        center={"lat": -15.0, "lon": -54.0},
        opacity=0.9,
        height=600
    )
    
    fig1.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        dragmode=False,
        coloraxis_colorbar=dict(title=var_label)
    )
    
    # Ajuste de velocidade
    try:
        fig1.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    except: pass

    st.plotly_chart(fig1, use_container_width=True, config=config_padrao)


# ==========================================
# ABA 2: VISÃO MENSAL (Novo)
# ==========================================
with tab2:
    st.markdown(f"**Análise Mensal:** Veja a variação de Jan a Dez dentro de um ano específico.")
    
    # Filtro de Ano específico para esta aba
    lista_anos = sorted(df['ano'].unique())
    ano_selecionado = st.select_slider("Selecione o Ano para detalhar:", options=lista_anos, value=lista_anos[-1])
    
    # Processamento
    df_mensal = df[df['ano'] == ano_selecionado].copy()
    # Agrupa por MÊS e ESTADO
    # Incluímos 'nome_mes' no groupby para usá-lo na animação, e 'mes' para ordenar corretamente
    df_anim_mensal = df_mensal.groupby(['mes', 'nome_mes', 'state'])[var_col].mean().reset_index()
    df_anim_mensal = df_anim_mensal.sort_values(['mes', 'state']) # Garante Jan -> Dez e Estados A-Z

    # Gráfico Tab 2
    fig2 = px.choropleth_mapbox(
        df_anim_mensal,
        geojson=geojson,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        animation_frame="nome_mes", # Animação corre pelos MESES (Jan, Fev...)
        color_continuous_scale=escala,
        range_color=global_ranges[var_col], # <--- MESMA ESCALA DA ABA 1
        mapbox_style="carto-positron",
        zoom=3.0,
        center={"lat": -15.0, "lon": -54.0},
        opacity=0.9,
        height=600
    )

    fig2.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        dragmode=False,
        coloraxis_colorbar=dict(title=var_label)
    )

    # Velocidade um pouco mais rápida para os meses
    try:
        fig2.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
    except: pass

    st.plotly_chart(fig2, use_container_width=True, config=config_padrao)

# --- TABELA DE DADOS (EXPANSÍVEL GERAL) ---
st.divider()
with st.expander("🔎 Ver Tabela de Dados Brutos"):
    st.dataframe(df.head(500), use_container_width=True)