import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- TÍTULO ---
st.header("🇧🇷 Painel Climático: Comparativo & Evolução")

# --- 1. CARREGAMENTO DOS DADOS (CACHEADO E OTIMIZADO) ---
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_dados():
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for caminho in caminhos:
        try:
            # Lê apenas colunas necessárias para economizar memória RAM
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
        # Conversão de Tipos (O segredo da performance)
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['Ano'] = df['semana_ref'].dt.year
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Strings para Categorias (Reduz uso de memória)
        df['state'] = df['state'].astype('category')
        
        # Números para float32 (Reduz uso de memória pela metade)
        cols_num = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio', 'radiacao_media']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Função de Estação
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
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

df = carregar_dados()
geojson_brasil = carregar_geojson()

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Configurações")

variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação Solar": "radiacao_media"
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

# Grid Fixo 2016-2021 (Ignora 2014/2015 que podem estar incompletos no visual)
anos = [2016, 2017, 2018, 2019, 2020, 2021]
colunas = st.columns(3)

for i, ano in enumerate(anos):
    col_idx = i % 3
    with colunas[col_idx]:
        df_ano = df_grid[df_grid['Ano'] == ano]
        
        if df_ano.empty:
            st.info(f"{ano}: -")
            continue
            
        # Agrupamento com observed=True para performance
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

# Legenda Simples
dummy = px.imshow([[min_g, max_g]], color_continuous_scale=escala)
dummy.update_layout(height=40, margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
dummy.update_traces(opacity=0, showscale=True, colorbar=dict(title=None, orientation='h', thickness=10))
dummy.update_xaxes(visible=False); dummy.update_yaxes(visible=False)
st.plotly_chart(dummy, use_container_width=True)

st.markdown("---")

# ==============================================================================
# PARTE 2: ANIMAÇÃO POR ANO (CORRIGIDA)
# ==============================================================================
st.subheader("🎞️ Linha do Tempo Evolutiva")
st.info("Selecione um ano abaixo para ver a animação mensal.")

# Slider de Ano
anos_disp = sorted(df['Ano'].unique())
# Define 2016 como padrão se disponível, pois 2014/2015 podem ter poucos dados
default_year = 2016 if 2016 in anos_disp else anos_disp[-1]
ano_anim = st.select_slider("Ano:", options=anos_disp, value=default_year)

# Filtrar dados
df_anim = df[df['Ano'] == ano_anim].copy()
df_agrupado = df_anim.groupby(['state', 'Mes_Ano'], observed=True)[var_col].mean().reset_index()
df_agrupado = df_agrupado.sort_values('Mes_Ano')

if not df_agrupado.empty:
    fig_anim = px.choropleth(
        df_agrupado,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
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

    # --- CORREÇÃO DO ERRO INDEXERROR ---
    # Só tenta ajustar a velocidade se houver animação (mais de 1 quadro)
    if len(df_agrupado['Mes_Ano'].unique()) > 1:
        try:
            fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
        except:
            pass # Se falhar, usa o padrão

    st.plotly_chart(fig_anim, use_container_width=True)
else:
    st.warning(f"Sem dados detalhados para {ano_anim}")
