import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURAÇÃO PADRÃO (Travamento de Zoom/Pan e Limpeza Visual) ---
config_padrao = {
    'scrollZoom': False, # Desabilita zoom com scroll do mouse
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
        'toImage' # Opcional: remove botão de baixar imagem se quiser limpar mais
    ]
}

# --- TÍTULO E EXPLICAÇÃO ---
st.header("🌍 Mapa Animado: Evolução Climática")
st.markdown("""
Abaixo, você pode assistir à evolução do clima brasileiro ano a ano.
1. Escolha a **Variável** (ex: Temperatura).
2. Escolha a **Estação do Ano** (ex: Verão).
3. Aperte o **Play ▶️** no canto inferior esquerdo do mapa.
""")

# --- 1. CARREGAMENTO DE DADOS E GEOJSON ---
@st.cache_data(ttl=3600)
def carregar_dados_mapa():
    try:
        # Tenta carregar do caminho padrão
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except:
        try:
            # Tenta carregar da raiz (caso mude a pasta)
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
        except:
            st.error("Erro Crítico: CSV de dados não encontrado.")
            st.stop()
            
    # Tratamento de Datas
    if 'semana_ref' in df.columns:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['ano'] = df['semana_ref'].dt.year
        df['mes'] = df['semana_ref'].dt.month
        
        # Função para criar a coluna de Estação
        def get_estacao(m):
            if m in [12, 1, 2]: return "Verão"
            elif m in [3, 4, 5]: return "Outono"
            elif m in [6, 7, 8]: return "Inverno"
            else: return "Primavera"
        df['estacao'] = df['mes'].apply(get_estacao)
        
    return df

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
    st.warning("Sem conexão para carregar o mapa do Brasil. Verifique sua internet.")
    st.stop()

# --- 2. CONTROLES LATERAIS ---
st.sidebar.header("Configurações do Mapa")

# Seletor de Variável
variaveis = {
    "Temperatura (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}
var_label = st.sidebar.selectbox("O que você quer visualizar?", list(variaveis.keys()))
var_col = variaveis[var_label]

# Seletor de Estação (Filtro Principal)
estacao_selecionada = st.sidebar.radio(
    "Filtrar por Estação:",
    ["Verão", "Outono", "Inverno", "Primavera"],
    index=0
)

# --- 3. PREPARAÇÃO DOS DADOS PARA ANIMAÇÃO ---
# Filtra pela estação escolhida
df_filtrado = df[df['estacao'] == estacao_selecionada].copy()

# Agrupa por ANO e ESTADO (Tiramos a média da estação naquele ano)
df_animacao = df_filtrado.groupby(['ano', 'state'])[var_col].mean().reset_index()

# Ordena por ano para a animação seguir a cronologia correta
df_animacao = df_animacao.sort_values('ano')

# Define limites de cor FIXOS (Para a cor não "piscar" quando mudar o ano)
min_val = df_animacao[var_col].min()
max_val = df_animacao[var_col].max()

# --- 4. CONSTRUÇÃO DO MAPA ANIMADO ---

# Definição da Paleta de Cores
if "chuva" in var_col:
    escala = "Blues"
elif "temperatura" in var_col:
    escala = "RdYlBu_r" # Invertido: Vermelho para quente
elif "umidade" in var_col:
    escala = "YlGnBu"
else:
    escala = "Viridis"

# Criação do Gráfico
fig = px.choropleth_mapbox(
    df_animacao,
    geojson=geojson,
    locations='state',
    featureidkey="properties.sigla",
    color=var_col,
    animation_frame="ano", 
    color_continuous_scale=escala,
    range_color=[min_val, max_val], # Trava a escala de cores
    mapbox_style="carto-positron",
    zoom=3.5,
    center={"lat": -15.7, "lon": -52},
    opacity=0.9,
    title=f"Evolução: {var_label} no {estacao_selecionada} (2015-2021)",
    height=700
)

# Ajustes de Layout (Margens, Velocidade e Botões)
fig.update_layout(
    dragmode=False, # <--- TRAVA O ARRASTO (PAN) DO MAPA
    margin={"r":0,"t":50,"l":0,"b":0},
    coloraxis_colorbar=dict(title=var_label),
    updatemenus=[
        dict(
            type='buttons',
            showactive=False,
            y=0.1, 
            x=0.1, 
            xanchor='right', 
            yanchor='top', 
            pad=dict(t=0, r=10),
            buttons=[
                # --- BOTÃO PLAY ---
                dict(
                    label='▶️ Play',
                    method='animate',
                    args=[None, dict(frame=dict(duration=800, redraw=True), 
                                     fromcurrent=True)]
                ),
                # --- BOTÃO PAUSE ---
                dict(
                    label='⏸️ Pause',
                    method='animate',
                    args=[[None], dict(frame=dict(duration=0, redraw=False), 
                                       mode="immediate", 
                                       transition=dict(duration=0))]
                )
            ]
        )
    ]
)

# Renderização com Configuração de Travamento
st.plotly_chart(fig, use_container_width=True, config=config_padrao)

# Tabela de Dados
df_pivot = df_animacao.pivot(index='state', columns='ano', values=var_col)

altura_tab_map = (len(df_pivot) + 1) * 35 + 3

with st.expander("Ver dados desta animação"):
    st.dataframe(df_pivot, height=altura_tab_map)
