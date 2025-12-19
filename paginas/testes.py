import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

# --- 1. CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_stats():
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
        except:
            st.error("Erro: CSV não encontrado.")
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

# --- 2. CONFIGURAÇÃO VISUAL ---
config_padrao = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
}

# --- 3. TESTE DE HIPÓTESES ---
st.subheader("2. Teste de Hipóteses Automatizado")

with st.container(border=True):
    col_conf1, col_conf2, col_conf3 = st.columns(3)
    with col_conf1:
        var_analise = st.selectbox("1️⃣ Variável Numérica:", colunas_numericas)
        col_analise_original = [k for k, v in cols_validas.items() if v == var_analise][0]
    with col_conf2:
        labels_agrupamento = {'region': 'Região', 'state': 'Estado', 'ano': 'Ano', 'estacao': 'Estação'}
        opcoes = [op for op in labels_agrupamento.keys() if op in df.columns]
        grupo_key = st.selectbox("2️⃣ Agrupar por:", opcoes, format_func=lambda x: labels_agrupamento.get(x, x))
    with col_conf3:
        vals = sorted(df[grupo_key].unique().astype(str))
        grupos_escolhidos = st.multiselect("3️⃣ Grupos (Min 2):", vals, default=vals[:2] if len(vals) > 1 else vals)

if len(grupos_escolhidos) < 2:
    st.warning("Selecione pelo menos 2 grupos para comparar.")
else:
    df_plot = df[df[grupo_key].astype(str).isin(grupos_escolhidos)].copy()
    dados_grupos = [df_plot[df_plot[grupo_key].astype(str) == g][col_analise_original].dropna() for g in grupos_escolhidos]

    if len(dados_grupos) < 2 or any(len(g) < 2 for g in dados_grupos):
        st.error("Dados insuficientes nos grupos selecionados.")
    else:
        if len(dados_grupos) == 2:
            tipo, stat, p_val = "Teste t (Student)", *stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=False)
        else:
            tipo, stat, p_val = "ANOVA", *stats.f_oneway(*dados_grupos)

        col_res, col_graf = st.columns([1, 2])
        
        with col_res:
            st.markdown("### 📊 Resultados")
            st.info(f"**Teste:** {tipo}")
            st.metric("P-Valor", f"{p_val:.4e}")
            if p_val < 0.05:
                st.success("✅ **Diferença Significativa!**")
            else:
                st.error("❌ **Sem Diferença Significativa**")

        with col_graf:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.2, 0.8], vertical_spacing=0.05)
            cores = ['#52BE80', '#5499C7', '#EC7063', '#F4D03F', '#AF7AC5'] 

            for i, grupo in enumerate(grupos_escolhidos):
                cor = cores[i % len(cores)]
                fig.add_trace(go.Box(x=dados_grupos[i], name=grupo, marker_color=cor, orientation='h', showlegend=False), row=1, col=1)
                fig.add_trace(go.Histogram(x=dados_grupos[i], name=grupo, marker_color=cor, opacity=0.6, histnorm='probability density'), row=2, col=1)

            fig.update_layout(height=500, barmode='overlay', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              margin=dict(l=20, r=20, t=10, b=10), dragmode=False)
            st.plotly_chart(fig, use_container_width=True, config=config_padrao)
