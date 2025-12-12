import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
# Se já estiver configurado no app.py, esta linha é ignorada, mas garante funcionamento isolado
# st.set_page_config(layout="wide") 

st.header("comparação Sazonal: Evolução Anual")
st.info("Selecione a estação do ano abaixo para comparar as mudanças climáticas ao longo dos anos.")

# --- 1. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados_completos():
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    df = None
    for c in caminhos:
        try:
            df = pd.read_csv(c)
            break
        except: continue
        
    if df is None:
        st.error("Erro: CSV não encontrado.")
        st.stop()
        
    # Tratamento de datas e criação de colunas temporais
    df['semana_ref'] = pd.to_datetime(df['semana_ref'])
    df['ano'] = df['semana_ref'].dt.year
    df['mes'] = df['semana_ref'].dt.month
    
    # Função para definir estação do ano (Simplificada para Climatologia Geral)
    def get_estacao(mes):
        if mes in [12, 1, 2]: return "Verão"
        elif mes in [3, 4, 5]: return "Outono"
        elif mes in [6, 7, 8]: return "Inverno"
        else: return "Primavera"
        
    df['estacao'] = df['mes'].apply(get_estacao)
    
    return df

@st.cache_data(ttl=3600)
def carregar_geojson():
    # GeoJSON oficial dos estados brasileiros
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        return requests.get(url).json()
    except Exception as e:
        st.error(f"Erro ao carregar mapa: {e}")
        return None

df = carregar_dados_completos()
geojson = carregar_geojson()

# --- 2. BARRA LATERAL (CONTROLES) ---
st.sidebar.header("⚙️ Configurações")

# Seleção de Variável
variaveis = {
    "Temperatura (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}
var_label = st.sidebar.selectbox("Variável Climática:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Filtro de Anos (Opcional, para não poluir se tiver muitos anos)
anos_disponiveis = sorted(df['ano'].unique())
# Seleciona por padrão os últimos 6 anos se houver muitos
padrao_anos = anos_disponiveis[-6:] if len(anos_disponiveis) > 6 else anos_disponiveis
anos_selecionados = st.sidebar.multiselect("Anos para exibir:", anos_disponiveis, default=padrao_anos)

# --- 3. INTERFACE PRINCIPAL ---

# Botões de Estação (Pills ou Radio horizontal)
col_nav, _ = st.columns([2, 1])
with col_nav:
    estacao_selecionada = st.radio(
        "Selecione a Estação:",
        ["Verão", "Outono", "Inverno", "Primavera"],
        horizontal=True,
        index=0 # Começa no Verão
    )

# --- 4. PROCESSAMENTO DOS DADOS ---
# Filtrar pelo input do usuário
df_filtrado = df[
    (df['estacao'] == estacao_selecionada) & 
    (df['ano'].isin(anos_selecionados))
]

# Agrupar: Calcula a média da variável para cada Estado em cada Ano
df_mapa = df_filtrado.groupby(['ano', 'state'])[var_col].mean().reset_index()

# Garantir ordenação para os mapas aparecerem na ordem certa
df_mapa = df_mapa.sort_values('ano')

# --- 5. VISUALIZAÇÃO (PLOTLY FACET MAPS) ---
if df_mapa.empty:
    st.warning("Sem dados para essa combinação de filtros.")
else:
    # Definir escala de cor baseada na variável
    if "chuva" in var_col:
        escala_cor = "Blues"
    elif "temperatura" in var_col:
        escala_cor = "RdYlBu_r" # Vermelho (quente) a Azul (frio) invertido
    elif "umidade" in var_col:
        escala_cor = "YlGnBu"
    else:
        escala_cor = "Viridis"

    # Criar o Grid de Mapas (Facet Plot)
    fig = px.choropleth_mapbox(
        df_mapa,
        geojson=geojson,
        locations='state',        # Coluna com a sigla do estado
        featureidkey="properties.sigla", # Onde está a sigla no GeoJSON
        color=var_col,
        facet_col="ano",          # CRUCIAL: Cria um mapa por ano
        facet_col_wrap=3,         # Quebra linha a cada 3 mapas (para mostrar 6 fica 3x2)
        color_continuous_scale=escala_cor,
        mapbox_style="carto-positron",
        zoom=3,
        center={"lat": -15.7, "lon": -52},
        opacity=0.9,
        title=f"Média de {var_label} no {estacao_selecionada} (Por Ano)",
        height=700 # Altura fixa para garantir visibilidade
    )

    # Ajustes finos de layout
    fig.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(title=var_label)
    )

    # Exibir no Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Tabela Resumo (Opcional, abaixo dos mapas)
    with st.expander("Ver dados detalhados em tabela"):
        st.dataframe(
            df_mapa.pivot(index='state', columns='ano', values=var_col).style.format("{:.1f}"),
            use_container_width=True
        )
