import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

st.header("📊 Análise Estatística e Correlações")

# 1. Carregar Dados
@st.cache_data
def carregar_dados_stats():
    df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    # Ajuste de datas
    if 'semana_ref' in df.columns:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['ano'] = df['semana_ref'].dt.year
        df['mes'] = df['semana_ref'].dt.month
    return df

df = carregar_dados_stats()

# --- A. MATRIZ DE CORRELAÇÃO ---
st.subheader("1. Correlação de Pearson (Heatmap)")
st.info("Valores próximos de 1 ou -1 indicam forte relação. Próximos de 0 indicam pouca relação linear.")

# Mapeamento para nomes mais amigáveis
cols_map = {
    'radiacao_media': 'Radiação',
    'vento_medio': 'Vento',
    'pressao_media': 'Pressão',
    'chuva_media_semanal': 'Chuva',
    'temperatura_media': 'Temperatura',
    'umidade_media': 'Umidade'
}

# Filtrar apenas colunas numéricas existentes
cols_disponiveis = [c for c in cols_map.keys() if c in df.columns]
df_corr = df[cols_disponiveis].rename(columns=cols_map)

# Calcular Correlação
corr_matrix = df_corr.corr()

# Plotar Heatmap com Seaborn e Matplotlib
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, ax=ax)
st.pyplot(fig)

# --- B. TESTE DE HIPÓTESE (ANOVA) ---
st.markdown("---")
st.subheader("2. Teste de Hipótese (ANOVA)")
st.markdown("""
O teste ANOVA verifica se as médias de temperatura variam significativamente entre os grupos.
* **Hipótese Nula (H0):** As médias são iguais (não há diferença entre os grupos).
* **Hipótese Alternativa (H1):** Pelo menos uma média é diferente.
* **Critério:** Se P-valor < 0.05, rejeitamos H0 (há diferença significativa).
""")

col1, col2 = st.columns(2)

# Teste 1: Diferença entre MESES
with col1:
    st.markdown("#### 📅 Variação Mensal")
    grupos_mes = [df[df['mes'] == m]['temperatura_media'].dropna() for m in range(1, 13)]
    f_stat, p_val = stats.f_oneway(*grupos_mes)
    
    st.metric("Estatística F", f"{f_stat:.2f}")
    st.metric("P-valor", f"{p_val:.2e}")
    
    if p_val < 0.05:
        st.success("✅ Diferença Significativa entre os Meses detected.")
    else:
        st.warning("❌ Sem diferença estatística significativa.")

# Teste 2: Diferença entre ANOS
with col2:
    st.markdown("#### 📆 Variação Anual")
    anos = sorted(df['ano'].unique())
    grupos_ano = [df[df['ano'] == y]['temperatura_media'].dropna() for y in anos]
    f_stat_ano, p_val_ano = stats.f_oneway(*grupos_ano)
    
    st.metric("Estatística F", f"{f_stat_ano:.2f}")
    st.metric("P-valor", f"{p_val_ano:.2e}")
    
    if p_val_ano < 0.05:
        st.success("✅ Diferença Significativa entre os Anos detectada.")
    else:
        st.warning("❌ Sem diferença estatística significativa.")
