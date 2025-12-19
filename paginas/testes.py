import streamlit as st
import pandas as pd
import numpy as np
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
st.header("🧪 Teste de Hipóteses (Com Validação de Suposições)")
st.markdown("""
Aqui garantimos o rigor científico. O sistema verifica **Normalidade**, **Homogeneidade** e permite tratar a **Independência**.
""")

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        var_analise = st.selectbox("1️⃣ Variável:", colunas_numericas)
        col_orig = [k for k, v in cols_validas.items() if v == var_analise][0]
    with c2:
        labels = {'region': 'Região', 'state': 'Estado', 'estacao': 'Estação'} # Tiramos 'ano' daqui pois ele será usado na agregação
        opts = [op for op in labels.keys() if op in df.columns]
        grupo_key = st.selectbox("2️⃣ Comparar:", opts, format_func=lambda x: labels.get(x, x))
    with c3:
        vals = sorted(df[grupo_key].unique().astype(str))
        grupos = st.multiselect("3️⃣ Grupos:", vals, default=vals[:2] if len(vals)>=2 else vals)

st.markdown("---")

# --- NOVO: CONTROLE DE INDEPENDÊNCIA ---
st.subheader("⚙️ Configuração da Amostra (Independência)")
modo_agregacao = st.radio(
    "Como você deseja tratar os dados temporais?",
    ["Médias Anuais (Recomendado - Independente)", "Dados Semanais (Brutos - Autocorrelacionado)"],
    help="Dados semanais são viciados (o clima de hoje depende de ontem). Usar médias anuais corrige isso."
)

if modo_agregacao == "Médias Anuais (Recomendado - Independente)":
    st.info("✅ **Modo Seguro:** O sistema vai calcular a média de cada ano para cada grupo. Isso reduz o tamanho da amostra (N), mas garante que os dados sejam independentes, tornando o P-valor válido.")
else:
    st.warning("⚠️ **Modo Bruto:** Usando todas as semanas. Atenção: Isso viola a suposição de independência! Os testes tendem a apontar diferenças significativas (P-valor minúsculo) que podem ser exageradas.")

# --- 3. PROCESSAMENTO DOS DADOS ---
if len(grupos) < 2:
    st.info("Selecione os grupos acima.")
else:
    df_base = df[df[grupo_key].astype(str).isin(grupos)].copy()
    
    dados_grupos = []
    nomes_grupos = []
    
    for g in grupos:
        df_g = df_base[df_base[grupo_key].astype(str) == g]
        
        if modo_agregacao == "Médias Anuais (Recomendado - Independente)":
            # AGREGAÇÃO: Transforma 300 semanas em 7 anos
            d = df_g.groupby('ano')[col_orig].mean().dropna()
        else:
            # BRUTO: Usa as 300 semanas
            d = df_g[col_orig].dropna()
            
        if len(d) > 1: # Precisa de pelo menos 2 pontos
            dados_grupos.append(d)
            nomes_grupos.append(g)

    if len(dados_grupos) < 2:
        st.error("Dados insuficientes após o agrupamento. Tente usar 'Dados Semanais' se houver poucos anos.")
    else:
        # --- 4. AUDITORIA DAS SUPOSIÇÕES ---
        st.subheader("🔍 Auditoria Automática")
        
        c_audit1, c_audit2 = st.columns(2)
        
        # A. Normalidade (Shapiro)
        violou_normalidade = False
        with c_audit1:
            st.markdown("**1. Normalidade (Curva de Sino)**")
            for i, d in enumerate(dados_grupos):
                if len(d) < 3:
                    st.warning(f"⚠️ {nomes_grupos[i]}: Amostra muito pequena ({len(d)}) para testar normalidade.")
                else:
                    stat_s, p_s = stats.shapiro(d)
                    if p_s < 0.05:
                        violou_normalidade = True
                        st.error(f"❌ {nomes_grupos[i]}: Não Normal (p={p_s:.3f})")
                    else:
                        st.success(f"✅ {nomes_grupos[i]}: Normal (p={p_s:.3f})")

        # B. Homogeneidade (Levene)
        violou_variancia = False
        stat_l, p_l = stats.levene(*dados_grupos)
        with c_audit2:
            st.markdown("**2. Homogeneidade de Variância**")
            if p_l < 0.05:
                violou_variancia = True
                st.error(f"❌ Variâncias Diferentes (p={p_l:.3f})")
            else:
                st.success(f"✅ Variâncias Iguais (p={p_l:.3f})")

        # --- 5. DECISÃO E RESULTADO ---
        st.divider()
        st.subheader("📊 Resultado Final")

        # Lógica de Decisão
        nome_teste = ""
        motivo = ""
        
        if len(dados_grupos) == 2:
            if violou_normalidade:
                nome_teste = "Mann-Whitney U"
                motivo = "Dados não são normais -> Usamos teste Não-Paramétrico."
                stat, p_val = stats.mannwhitneyu(dados_grupos[0], dados_grupos[1])
            elif violou_variancia:
                nome_teste = "Teste t de Welch"
                motivo = "Dados normais com variâncias diferentes -> Usamos Teste t corrigido."
                stat, p_val = stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=False)
            else:
                nome_teste = "Teste t de Student"
                motivo = "Suposições atendidas -> Usamos Teste t padrão."
                stat, p_val = stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=True)
        else:
            if violou_normalidade:
                nome_teste = "Kruskal-Wallis"
                motivo = "Dados não são normais -> Usamos ANOVA Não-Paramétrica."
                stat, p_val = stats.kruskal(*dados_grupos)
            else:
                nome_teste = "ANOVA One-Way"
                motivo = "Suposições atendidas -> Usamos ANOVA padrão."
                stat, p_val = stats.f_oneway(*dados_grupos)

        # Exibição
        c_res1, c_res2 = st.columns([1, 2])
        with c_res1:
            st.metric("P-Valor", f"{p_val:.4e}")
            if p_val < 0.05:
                st.success("✅ **Diferença Significativa**")
            else:
                st.error("❌ **Sem Diferença**")
        
        with c_res2:
            st.markdown(f"**Teste Selecionado:** `{nome_teste}`")
            st.info(f"**Por que?** {motivo}")
            st.caption(f"Amostras usadas: {len(dados_grupos[0])} pontos por grupo.")

        # --- 6. VISUALIZAÇÃO ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.3, 0.7], vertical_spacing=0.05)
        cores = ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099']
        
        for i, (d, nome) in enumerate(zip(dados_grupos, nomes_grupos)):
            cor = cores[i % len(cores)]
            fig.add_trace(go.Box(x=d, name=nome, marker_color=cor, showlegend=False), row=1, col=1)
            # No modo "Médias Anuais", o histograma fica ruim (poucos dados), então usamos Rug Plot ou só Box
            if len(d) > 10:
                fig.add_trace(go.Histogram(x=d, name=nome, marker_color=cor, opacity=0.6, histnorm='probability density'), row=2, col=1)
            else:
                # Se tiver poucos dados, usamos um Scatter simples para ver os pontos
                fig.add_trace(go.Scatter(x=d, y=[0]*len(d), mode='markers', name=nome, marker=dict(color=cor, size=10)), row=2, col=1)

        fig.update_layout(title=f"Distribuição ({'Médias Anuais' if 'Anuais' in modo_agregacao else 'Dados Semanais'})", height=500)
        st.plotly_chart(fig, use_container_width=True)
