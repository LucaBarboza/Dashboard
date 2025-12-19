import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- 1. CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title="Monitor Climático Brasil",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração para limpar a interface do Plotly (tirar botões de zoom chatos)
config_padrao = {
    'scrollZoom': False, 
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
        'toImage', 'toggleHover'
    ]
}

# --- 2. FUNÇÕES DE CARREGAMENTO (CACHED) ---

@st.cache_data(ttl=3600)
def carregar_dados_mapa():
    """Carrega, limpa e prepara os dados climáticos."""
    try:
        # Tenta ler de subpasta ou raiz
        try:
            df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        except FileNotFoundError:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
            
        # Converter coluna de data
        if 'semana_ref' in df.columns:
            df['semana_ref'] = pd.to_datetime(df['semana_ref'])
            df['ano'] = df['semana_ref'].dt.year
            df['mes'] = df['semana_ref'].dt.month
            
            # CRUCIAL: Coluna de ordenação para a Timeline (YYYY-MM)
            # Isso garante que a animação flua corretamente: 2015-01 -> 2015-02...
            df['ano_mes'] = df['semana_ref'].dt.strftime('%Y-%m')
            
            # Define Estações
            def get_estacao(m):
                if m in [12, 1, 2]: return "Verão"
                elif m in [3, 4, 5]: return "Outono"
                elif m in [6, 7, 8]: return "Inverno"
                else: return "Primavera"
            df['estacao'] = df['mes'].apply(get_estacao)
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados CSV: {e}")
        st.stop()

@st.cache_data(ttl=3600)
def carregar_geojson():
    """Baixa o mapa do Brasil (limites estaduais)."""
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Erro ao baixar mapa GeoJSON: {e}")
    return None

# Carrega os dados
df = carregar_dados_mapa()
geojson = carregar_geojson()

if geojson is None:
    st.stop()

# --- 3. CÁLCULO DE ESCALAS GLOBAIS (TRAVAMENTO) ---
# Calcula o min e max ABSOLUTOS de todo o histórico.
# Isso garante que as cores sejam comparáveis entre as abas.
global_ranges = {
    "temperatura_media": [df['temperatura_media'].min(), df['temperatura_media'].max()],
    "chuva_media_semanal": [df['chuva_media_semanal'].min(), df['chuva_media_semanal'].max()],
    "umidade_media": [df['umidade_media'].min(), df['umidade_media'].max()],
    "vento_medio": [df['vento_medio'].min(), df['vento_medio'].max()],
    "radiacao_media": [df['radiacao_media'].min(), df['radiacao_media'].max()]
}

# --- 4. BARRA LATERAL (CONTROLES) ---
st.sidebar.header("⚙️ Configurações")

variaveis = {
    "Temperatura (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}

var_label = st.sidebar.selectbox("Variável Visualizada:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Definição Inteligente da Paleta de Cores
if "chuva" in var_col:
    escala = "Blues"
elif "temperatura" in var_col:
    escala = "RdYlBu_r" # Invertido: Azul (Frio) -> Vermelho (Quente)
elif "umidade" in var_col:
    escala = "YlGnBu"
else:
    escala = "Viridis"

# --- 5. INTERFACE PRINCIPAL (ABAS) ---
st.title("🌍 Evolução Climática do Brasil")

# Criação das duas abas
tab1, tab2 = st.tabs(["🍂 Comparação por Estações (Ano a Ano)", "⏳ Linha do Tempo das Estações"])

# ==========================================
# ABA 1: VISÃO SAZONAL
# ==========================================
with tab1:
    st.markdown("Compare como uma **Estação Específica** mudou ao longo dos anos.")
    
    col_sel, _ = st.columns([1, 3])
    with col_sel:
        estacao_selecionada = st.radio(
            "Selecione a Estação:",
            ["Verão", "Outono", "Inverno", "Primavera"],
            horizontal=True
        )
    
    # Filtra e Agrupa
    df_sazonal = df[df['estacao'] == estacao_selecionada].copy()
    df_anim_sazonal = df_sazonal.groupby(['ano', 'state'])[var_col].mean().reset_index()
    df_anim_sazonal = df_anim_sazonal.sort_values(['ano', 'state'])

    # Mapa 1
    fig1 = px.choropleth_mapbox(
        df_anim_sazonal,
        geojson=geojson,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        animation_frame="ano",
        color_continuous_scale=escala,
        range_color=global_ranges[var_col], # <--- Escala Travada
        mapbox_style="carto-positron",
        zoom=3.0,
        center={"lat": -15.0, "lon": -54.0},
        opacity=0.9,
        height=600,
        title=f"Evolução: {var_label} no {estacao_selecionada}"
    )
    
    # Layout Limpo
    fig1.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, dragmode=False)
    # Velocidade Lenta (1 seg) para comparação anual
    try:
        fig1.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    except: pass
    
    st.plotly_chart(fig1, use_container_width=True, config=config_padrao)


# ==========================================
# ABA 2: LINHA DO TEMPO COMPLETA (OTIMIZADA)
# ==========================================
# ==========================================
# ABA 2: VISÃO SAZONAL (VERÃO 14 -> OUTONO 21)
# ==========================================
with tab2:
    st.markdown(f"**Evolução por Estações:** Agrupamento trimestral (Verão, Outono, Inverno, Primavera).")

    # 1. Função auxiliar para definir estação e ajustar o ano
    # (O Verão de 2015, por exemplo, é composto por Dez/14, Jan/15 e Fev/15)
    def get_estacao_info(row):
        mes = row['mes']
        ano = row['ano']
        
        if mes in [12, 1, 2]:
            # Se for Dezembro, pertence ao Verão do ano SEGUINTE
            ano_ref = ano + 1 if mes == 12 else ano
            return "Verão", 1, ano_ref
        elif mes in [3, 4, 5]:
            return "Outono", 2, ano
        elif mes in [6, 7, 8]:
            return "Inverno", 3, ano
        else: # 9, 10, 11
            return "Primavera", 4, ano

    # 2. Aplicando a lógica no DataFrame
    df_sazonal = df.copy()
    
    # Aplica a função e expande o resultado em colunas novas
    # Resulta em: Nome da Estação, Ordem (1-4) para sort, e Ano da Estação
    season_data = df_sazonal.apply(get_estacao_info, axis=1, result_type='expand')
    df_sazonal[['estacao', 'ordem_estacao', 'ano_estacao']] = season_data

    # 3. Agrupamento (Média por Estação/Ano/Estado)
    df_anim_sazonal = df_sazonal.groupby(['ano_estacao', 'estacao', 'ordem_estacao', 'state'])[var_col].mean().reset_index()

    # 4. Ordenação CRONOLÓGICA (Ano -> Ordem da Estação -> Estado)
    df_anim_sazonal = df_anim_sazonal.sort_values(['ano_estacao', 'ordem_estacao', 'state'])

    # 5. Criar Label para a Animação (Ex: "Verão/2015")
    df_anim_sazonal['periodo_label'] = df_anim_sazonal['estacao'] + "/" + df_anim_sazonal['ano_estacao'].astype(str)

    # Gráfico Tab 2
    fig2 = px.choropleth_mapbox(
        df_anim_sazonal,
        geojson=geojson,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        
        # Animação pelas estações
        animation_frame="periodo_label", 
        
        color_continuous_scale=escala,
        range_color=global_ranges[var_col],
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

    # Velocidade: Como temos menos frames (4 por ano), podemos deixar mais lento para apreciar (800ms)
    try:
        fig2.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
    except: pass

    st.plotly_chart(fig2, use_container_width=True, config=config_padrao)

# --- 6. RODAPÉ (DADOS) ---
st.divider()
with st.expander("🔎 Ver Tabela de Dados (Amostra)"):
    st.dataframe(df.head(100), use_container_width=True)