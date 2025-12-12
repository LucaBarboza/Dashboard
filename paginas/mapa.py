import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

# --- TÍTULO ---
st.header("🇧🇷 Painel Climático: Evolução Histórica")

# --- 1. CARREGAMENTO DOS DADOS (OTIMIZADO PARA NUVEM) ---
@st.cache_data(ttl=3600)  # Guarda na memória por 1 hora
def carregar_dados():
    # Tenta achar o arquivo no GitHub/Streamlit Cloud
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for caminho in caminhos:
        try:
            # Lê apenas as colunas que realmente usamos (economiza memória)
            cols_usadas = [
                'semana_ref', 'state', 'temperatura_media', 
                'chuva_media_semanal', 'umidade_media', 
                'vento_medio', 'radiacao_media'
            ]
            df = pd.read_csv(caminho, usecols=cols_usadas)
            break
        except FileNotFoundError:
            continue
            
    if df is None:
        st.error("❌ Erro: Arquivo CSV não encontrado.")
        st.stop()

    try:
        # --- OTIMIZAÇÃO DE MEMÓRIA (AUTOMÁTICA) ---
        # Converte Data
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Converte Texto -> Categoria (Isso reduz o uso de RAM em até 90%)
        df['state'] = df['state'].astype('category')
        
        # Converte Números para Float32 (Metade do tamanho do padrão)
        cols_num = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio', 'radiacao_media']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], downcast='float')

        # Criar colunas de tempo
        df['Ano'] = df['semana_ref'].dt.year
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Função de Estação Otimizada
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.map(get_estacao).astype('category')
        
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao tratar dados: {e}")
        st.stop()

# --- 2. CARREGAMENTO DO MAPA ---
@st.cache_data(ttl=3600)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

# Carrega tudo (Isso roda rápido por causa do cache)
df = carregar_dados()
geojson_brasil = carregar_geojson()

# --- SIDEBAR ---
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
if "temperatura" in var_col:
    escala = "RdYlBu_r"
elif "chuva" in var_col:
    escala = "Blues"
elif "umidade" in var_col:
    escala = "Teal"
else:
    escala = "Spectral_r"

# Limites globais
min_g = df[var_col].min()
max_g = df[var_col].max()


# ==============================================================================
# PARTE 1: GRID COMPARATIVO
# ==============================================================================
st.subheader("🗓️ Comparativo Anual")

estacao_filtro = st.radio(
    "Filtrar Período:",
    ["Média do Ano", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

df_grid = df if estacao_filtro == "Média do Ano" else df[df['Estacao'] == estacao_filtro]

anos = [2016, 2017, 2018, 2019, 2020, 2021]
colunas = st.columns(3)

for i, ano in enumerate(anos):
    col_idx = i % 3
    with colunas[col_idx]:
        df_ano = df_grid[df_grid['Ano'] == ano]
        
        # Check rápido para evitar erro se o ano estiver vazio
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
        fig.update_layout(
            margin={"r":0,"t":30,"l":0,"b":0},
            height=200,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)

# Legenda Simples e Leve
st.caption(f"Legenda: {var_label}")
dummy = px.imshow([[min_g, max_g]], color_continuous_scale=escala)
dummy.update_layout(height=40, margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
dummy.update_traces(opacity=0, showscale=True, colorbar=dict(title=None, orientation='h', thickness=10))
dummy.update_xaxes(visible=False); dummy.update_yaxes(visible=False)
st.plotly_chart(dummy, use_container_width=True)

st.markdown("---")

# ==============================================================================
# PARTE 2: ANIMAÇÃO (LEVE E NATIVA)
# ==============================================================================
st.subheader("🎞️ Linha do Tempo Evolutiva")
st.info("💡 Selecione um ano para ver a animação mensal com fluidez.")

# Filtro de Ano (Essencial para não travar o navegador com dados demais)
anos_disp = sorted(df['Ano'].unique())
ano_anim = st.select_slider("Ano:", options=anos_disp, value=anos_disp[-1])

# Filtrar dados apenas do ano escolhido (Deixa MUITO leve)
df_animacao = df[df['Ano'] == ano_anim].copy()

# Agrupar por Mês (Reduz de 52 semanas para 12 quadros)
df_agrupado = df_animacao.groupby(['state', 'Mes_Ano'], observed=True)[var_col].mean().reset_index()
df_agrupado = df_agrupado.sort_values('Mes_Ano')

if not df_agrupado.empty:
    fig_anim = px.choropleth(
        df_agrupado,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        # O PLAYER NATIVO (Roda no navegador, zero lag)
        animation_frame="Mes_Ano", 
        color_continuous_scale=escala,
        range_color=[min_g, max_g],
        scope="south america",
        title=f"Evolução em {ano_anim}",
        hover_data={var_col:':.1f'}
    )

    fig_anim.update_geos(fitbounds="locations", visible=False)
    fig_anim.update_layout(
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(title=None, orientation="h", y=-0.1, thickness=15),
        sliders=[{"pad": {"t": 30}}]
    )
    
    # Velocidade ideal (500ms)
    fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500

    st.plotly_chart(fig_anim, use_container_width=True)
else:
    st.warning(f"Sem dados detalhados para {ano_anim}")
