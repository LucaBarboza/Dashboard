import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

# --- 1. CARREGAMENTO E TRATAMENTO ---
@st.cache_data
def carregar_dados_stats():
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except:
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
    'pressao_media': 'Pressão',
    'chuva_media_semanal': 'Chuva',
    'temperatura_media': 'Temperatura',
    'umidade_media': 'Umidade'
}
cols_validas = {k: v for k, v in cols_map.items() if k in df.columns}
colunas_numericas = list(cols_validas.values())

# --- 2. INTERFACE ---
st.header("🧪 Teste de Hipóteses (Auditoria Automática)")
st.markdown("""
O sistema verifica as premissas estatísticas (Suposições) antes de escolher o teste:
1.  **Normalidade:** Os dados seguem uma curva de sino?
2.  **Homogeneidade:** A variação dos dados é similar entre os grupos?
""")

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        var_analise = st.selectbox("1️⃣ Variável:", colunas_numericas)
        col_orig = [k for k, v in cols_validas.items() if v == var_analise][0]
    with c2:
        labels = {'region': 'Região', 'state': 'Estado', 'ano': 'Ano', 'estacao': 'Estação'}
        opts = [op for op in labels.keys() if op in df.columns]
        grupo_key = st.selectbox("2️⃣ Agrupar por:", opts, format_func=lambda x: labels.get(x, x))
    with c3:
        vals = sorted(df[grupo_key].unique().astype(str))
        grupos = st.multiselect("3️⃣ Grupos:", vals, default=vals[:2] if len(vals)>=2 else vals)

# --- 3. AUDITORIA ESTATÍSTICA ---
if len(grupos) < 2:
    st.info("Selecione pelo menos 2 grupos.")
else:
    df_plot = df[df[grupo_key].astype(str).isin(grupos)].copy()
    dados_grupos = []
    nomes_grupos = []
    
    # Coleta dados
    for g in grupos:
        d = df_plot[df_plot[grupo_key].astype(str) == g][col_orig].dropna()
        if len(d) > 3: 
            dados_grupos.append(d)
            nomes_grupos.append(g)
            
    if len(dados_grupos) < 2:
        st.error("Dados insuficientes.")
    else:
        st.subheader("🔍 Auditoria das Suposições")
        col_audit1, col_audit2 = st.columns(2)
        
        # --- A. TESTE DE NORMALIDADE (Shapiro-Wilk) ---
        # H0: É Normal | H1: Não é Normal
        violou_normalidade = False
        grupos_fora_normal = []
        
        with col_audit1:
            st.markdown("**1. Teste de Normalidade (Shapiro-Wilk)**")
            for i, d in enumerate(dados_grupos):
                # Shapiro tem limite de 5000 amostras, fazemos sample se necessário
                amostra = d if len(d) < 5000 else d.sample(5000, random_state=42)
                stat_s, p_s = stats.shapiro(amostra)
                
                if p_s < 0.05:
                    violou_normalidade = True
                    grupos_fora_normal.append(nomes_grupos[i])
                    st.error(f"❌ {nomes_grupos[i]}: Não é Normal (p={p_s:.1e})")
                else:
                    st.success(f"✅ {nomes_grupos[i]}: Normal (p={p_s:.2f})")
        
        # --- B. TESTE DE HOMOGENEIDADE DE VARIÂNCIA (Levene) ---
        # H0: Variâncias Iguais | H1: Variâncias Diferentes
        violou_variancia = False
        stat_l, p_l = stats.levene(*dados_grupos)
        
        with col_audit2:
            st.markdown("**2. Homogeneidade de Variância (Levene)**")
            if p_l < 0.05:
                violou_variancia = True
                st.error(f"❌ Variâncias Diferentes (Heterocedasticidade) (p={p_l:.1e})")
                st.caption("Os grupos têm dispersões muito diferentes.")
            else:
                st.success(f"✅ Variâncias Iguais (Homocedasticidade) (p={p_l:.2f})")

        st.divider()

        # --- C. DECISÃO AUTOMÁTICA DO TESTE ---
        st.subheader("📊 Resultado do Teste Definido")
        
        # LÓGICA DE DECISÃO
        nome_teste = ""
        motivo = ""
        
        if len(dados_grupos) == 2:
            # --- COMPARAÇÃO DE 2 GRUPOS ---
            if violou_normalidade:
                # Se não é normal -> Mann-Whitney (Não-Paramétrico)
                nome_teste = "Mann-Whitney U"
                motivo = f"⚠️ O teste Não-Paramétrico foi escolhido porque o grupo **{grupos_fora_normal[0]}** violou a suposição de normalidade."
                stat, p_val = stats.mannwhitneyu(dados_grupos[0], dados_grupos[1])
            
            else:
                # É Normal
                if violou_variancia:
                    # Normal mas com variância diferente -> Welch's T-Test
                    nome_teste = "Teste t de Welch"
                    motivo = "✅ Dados Normais, mas com variâncias diferentes. Usamos o ajuste de Welch."
                    stat, p_val = stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=False)
                else:
                    # Caso Perfeito
                    nome_teste = "Teste t de Student (Padrão)"
                    motivo = "✅ Todas as suposições (Normalidade e Variância) foram atendidas."
                    stat, p_val = stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=True)

        else:
            # --- COMPARAÇÃO DE 3+ GRUPOS ---
            if violou_normalidade:
                # Não-Paramétrico -> Kruskal-Wallis
                nome_teste = "Kruskal-Wallis"
                motivo = f"⚠️ O teste Não-Paramétrico foi escolhido porque os dados violaram a suposição de normalidade."
                stat, p_val = stats.kruskal(*dados_grupos)
            else:
                # Paramétrico -> ANOVA
                nome_teste = "ANOVA One-Way"
                if violou_variancia:
                    motivo = "⚠️ Dados Normais, mas variâncias diferentes. Resultado da ANOVA deve ser interpretado com cautela."
                else:
                    motivo = "✅ Todas as suposições atendidas."
                stat, p_val = stats.f_oneway(*dados_grupos)

        # EXIBIÇÃO FINAL
        c_res1, c_res2 = st.columns([1, 2])
        with c_res1:
            st.metric("P-Valor Final", f"{p_val:.4e}")
            if p_val < 0.05:
                st.success("✅ **Diferença Significativa**")
            else:
                st.warning("❌ **Sem Diferença**")
        
        with c_res2:
            st.markdown(f"### Teste Usado: **{nome_teste}**")
            st.info(motivo)

        # --- D. VISUALIZAÇÃO ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.3, 0.7], vertical_spacing=0.05)
        cores = ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099']
        
        for i, (d, nome) in enumerate(zip(dados_grupos, nomes_grupos)):
            cor = cores[i % len(cores)]
            # Boxplot
            fig.add_trace(go.Box(x=d, name=nome, marker_color=cor, showlegend=False), row=1, col=1)
            # Histograma
            fig.add_trace(go.Histogram(x=d, name=nome, marker_color=cor, opacity=0.6, histnorm='probability density'), row=2, col=1)

        fig.update_layout(title=f"Distribuição Visual: {var_analise}", barmode='overlay', height=500)
        st.plotly_chart(fig, use_container_width=True)
