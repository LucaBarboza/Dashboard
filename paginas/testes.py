import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

@st.cache_data
def carregar_dados():
    try:
        return pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except:
        return pd.read_csv("clima_brasil_semanal_refinado_2015.csv")

df = carregar_dados()

# Mapeamentos necessários para a página
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

# --- CONFIGURAÇÃO PADRÃO (Mesma das matrizes) ---
config_padrao = {
    'displayModeBar': True,
    'displaylogo': False,
    'scrollZoom': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 
        'zoomOut2d', 'autoScale2d', 'resetScale2d'
    ]
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
        grupos_escolhidos = st.multiselect("3️⃣ Grupos (Min 2):", vals, default=vals[:2])

if len(grupos_escolhidos) < 2:
    st.warning("Selecione pelo menos 2 grupos para realizar o teste.")
else:
    df_plot = df[df[grupo_key].astype(str).isin(grupos_escolhidos)].copy()
    dados_grupos = [df_plot[df_plot[grupo_key].astype(str) == g][col_analise_original].dropna() for g in grupos_escolhidos]

    if len(dados_grupos) < 2 or any(len(g) < 3 for g in dados_grupos):
        st.error("Dados insuficientes nos grupos selecionados para análise estatística.")
    else:
        # Estatística
        if len(dados_grupos) == 2:
            tipo, stat, p_val = "Teste t (Student)", *stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=False)
        else:
            tipo, stat, p_val = "ANOVA", *stats.f_oneway(*dados_grupos)

        col_res, col_graf = st.columns([1, 2])
        
        with col_res:
            st.markdown(f"### 📊 Resultados")
            st.info(f"**Teste:** {tipo}")
            st.metric("P-Valor", f"{p_val:.4e}")
            if p_val < 0.05:
                st.success("✅ **Diferença Significativa!**")
                st.caption("As médias dos grupos são estatisticamente diferentes (Rejeita H0).")
            else:
                st.error("❌ **Sem Diferença Significativa**")
                st.caption("Não há evidências de diferença real entre os grupos (Aceita H0).")

        with col_graf:
            # --- GRÁFICO COMBINADO COM PLOTLY (Boxplot + Histograma) ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, row_heights=[0.2, 0.8])

            cores = ['#2E8B57', '#4682B4', '#CD5C5C', '#F4A460', '#9370DB']

            for i, grupo in enumerate(grupos_escolhidos):
                cor = cores[i % len(cores)]
                fig.add_trace(go.Box(x=dados_grupos[i], name=grupo, marker_color=cor, 
                                     showlegend=False, orientation='h'), row=1, col=1)
                fig.add_trace(go.Histogram(x=dados_grupos[i], name=grupo, marker_color=cor, 
                                           opacity=0.6, histnorm='probability density'), row=2, col=1)

            fig.update_layout(
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                barmode='overlay',
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(title_text=var_analise, row=2, col=1)
            
            st.plotly_chart(fig,
