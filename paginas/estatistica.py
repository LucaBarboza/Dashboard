import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Análise Climática Brasil")

st.header("📊 Laboratório de Análise Estatística")
st.markdown("Exploração de correlações climáticas por estado e nível nacional (2015-2021).")

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
@st.cache_data
def carregar_dados_stats():
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
        except:
            st.error("Erro: Base de dados não encontrada.")
            st.stop()
    return df

df = carregar_dados_stats()

cols_map = {
    'radiacao_media': 'Radiação',
    'vento_medio': 'Vento',
    'vento_medio_kmh': 'Vento (km/h)',
    'pressao_media': 'Pressão',
    'chuva_media_semanal': 'Chuva',
    'temperatura_media': 'Temperatura',
    'umidade_media': 'Umidade'
}
cols_validas = {k: v for k, v in cols_map.items() if k in df.columns}
colunas_numericas = list(cols_validas.values())

st.markdown("---")

# --- 2. ANÁLISE DE CORRELAÇÃO ---
st.subheader("1. Matrizes de Correlação (Pearson vs Spearman)")

# Filtro de Estado
if 'state' in df.columns:
    estados_disponiveis = ["Brasil (Todos)"] + sorted(df['state'].unique().tolist())
    estado_selecionado = st.selectbox("Selecione o Estado para as Matrizes:", estados_disponiveis)

    if estado_selecionado == "Brasil (Todos)":
        df_corr = df.copy()
    else:
        df_corr = df[df['state'] == estado_selecionado].copy()
else:
    df_corr = df.copy()
    estado_selecionado = "Brasil"

df_corr_renomeado = df_corr.rename(columns=cols_validas)

# --- CONFIGURAÇÃO: FOCO NO DADO + TELA CHEIA ---
# Remove botões de edição, mas mantém o de tela cheia do Plotly
config_custom = {
    'displayModeBar': True,
    'displaylogo': False,
    'scrollZoom': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 
        'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 
        'hoverCompareCartesian', 'toggleSpikelines'
    ]
}

with st.expander("Ver Matrizes de Correlação", expanded=True):
    st.info(f"Exibindo correlações para: **{estado_selecionado}**")
    
    col_pearson, col_spearman = st.columns(2)
    
    def aplicar_estilo_matriz(fig):
        fig.update_layout(
            height=600, 
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=20),
            coloraxis_colorbar=dict(title="Grau"),
            dragmode=False
        )
        return fig

    with col_pearson:
        st.markdown("#### 🔵 Pearson (Relação Linear)")
        corr_p = df_corr_renomeado[colunas_numericas].corr(method='pearson')
        fig_p = px.imshow(
            corr_p,
            text_auto=".2f",
            aspect="equal", 
            color_continuous_scale="RdBu_r", 
            zmin=-1, zmax=1
        )
        st.plotly_chart(aplicar_estilo_matriz(fig_p), use_container_width=True, config=config_custom)

    with col_spearman:
        st.markdown("#### 🟢 Spearman (Relação de Posto)")
        corr_s = df_corr_renomeado[colunas_numericas].corr(method='spearman')
        fig_s = px.imshow(
            corr_s,
            text_auto=".2f",
            aspect="equal", 
            color_continuous_scale="RdYlGn", 
            zmin=-1, zmax=1
        )
        st.plotly_chart(aplicar_estilo_matriz(fig_s), use_container_width=True, config=config_custom)

st.markdown("---")
