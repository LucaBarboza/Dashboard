import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from scipy import stats

st.set_page_config(layout="wide")

st.header("📊 Laboratório de Análise Estatística")
st.markdown("Aqui você pode explorar correlações e testar hipóteses comparando diferentes grupos automaticamente.")

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
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
            
    if 'semana_ref' in df.columns:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['ano'] = df['semana_ref'].dt.year
        df['mes'] = df['semana_ref'].dt.month
        
        def get_estacao(m):
            if m in [12, 1, 2]: return "Verão"
            elif m in [3, 4, 5]: return "Outono"
            elif m in [6, 7, 8]: return "Inverno"
            else: return "Primavera"
        df['estacao'] = df['mes'].apply(get_estacao)
        
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

Para um visual profissional e sofisticado, as paletas divergentes suaves são as melhores. Elas mantêm a neutralidade no centro (correlação zero) e destacam as extremidades sem usar tons neon ou agressivos.

Vou sugerir duas paletas famosas no design de dados:

Pearson: Paleta Picnic (Tons de azul e vermelho lavados, mais sóbrios).

Spearman: Paleta Tealrose (Tons de verde-azulado e rosa seco, muito elegantes e modernos).

Além disso, ajustei o height e o aspect para garantir que a matriz fique com uma proporção harmônica.

Python

import plotly.express as px

# --- 2. ANÁLISE DE CORRELAÇÃO ---
st.subheader("1. Matrizes de Correlação (Pearson vs Spearman)")

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

with st.expander("Ver Matrizes de Correlação Interativas", expanded=True):
    st.info(f"Exibindo correlações para: **{estado_selecionado}**")
    
    col_pearson, col_spearman = st.columns(2)
    
    # Função personalizada para layout limpo e proporcional
    def configurar_layout_mapa(fig):
        fig.update_layout(
            height=550,  # Altura aumentada para evitar achatamento
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=20),
        )
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)
        return fig

    with col_pearson:
        st.markdown("#### 🔵 Pearson (Linear)")
        corr_p = df_corr_renomeado[colunas_numericas].corr(method='pearson')
        # Paleta 'Picnic': Tons suaves de azul, branco e vermelho
        fig_p = px.imshow(
            corr_p,
            text_auto=".2f",
            aspect="equal", 
            color_continuous_scale="Picnic", 
            zmin=-1, zmax=1
        )
        st.plotly_chart(configurar_layout_mapa(fig_p), use_container_width=True)

    with col_spearman:
        st.markdown("#### 🟢 Spearman (Rank)")
        corr_s = df_corr_renomeado[colunas_numericas].corr(method='spearman')
        # Paleta 'Tealrose': Tons suaves de verde água e rosa antigo
        fig_s = px.imshow(
            corr_s,
            text_auto=".2f",
            aspect="equal", 
            color_continuous_scale="Tealrose", 
            zmin=-1, zmax=1
        )
        st.plotly_chart(configurar_layout_mapa(fig_s), use_container_width=True)

# --- 3. TESTE DE HIPÓTESES ---
# (O restante do seu código permanece igual abaixo)
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
    st.warning("Selecione pelo menos 2 grupos.")
else:
    df_plot = df[df[grupo_key].astype(str).isin(grupos_escolhidos)].copy()
    df_plot = df_plot.sort_values(grupo_key)
    dados_grupos = [df_plot[df_plot[grupo_key].astype(str) == g][col_analise_original].dropna() for g in grupos_escolhidos]

    if len(dados_grupos) < 2:
        st.error("Dados insuficientes.")
    else:
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
                st.caption("As médias dos grupos são estatisticamente diferentes.")
            else:
                st.error("❌ **Sem Diferença Significativa**")
                st.caption("Não há evidências de diferença real entre os grupos.")

        with col_graf:
            st.markdown(f"#### Distribuição: {var_analise} por {labels_agrupamento.get(grupo_key)}")
            fig, (ax_box, ax_hist) = plt.subplots(2, 1, sharex=True, figsize=(10, 8), gridspec_kw={"height_ratios": (.15, .85)})
            sns.boxplot(x=col_analise_original, y=grupo_key, data=df_plot, orient='h', ax=ax_box, palette="Set2")
            ax_box.set(xlabel='')
            sns.histplot(data=df_plot, x=col_analise_original, hue=grupo_key, kde=True, element="step", ax=ax_hist, palette="Set2")
            ax_hist.set_xlabel(var_analise)
            st.pyplot(fig)
