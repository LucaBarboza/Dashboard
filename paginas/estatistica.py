import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

st.set_page_config(layout="wide") # Garante layout amplo para os gráficos lado a lado

st.header("📊 Laboratório de Análise Estatística")
st.markdown("Aqui você pode explorar correlações e testar hipóteses comparando diferentes grupos automaticamente.")

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
@st.cache_data
def carregar_dados_stats():
    # Tenta carregar o CSV
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
        except:
            st.error("Erro: CSV não encontrado.")
            st.stop()
            
    # Tratamento de Datas
    if 'semana_ref' in df.columns:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['ano'] = df['semana_ref'].dt.year
        df['mes'] = df['semana_ref'].dt.month
        
        # Função simples para estação (se não existir no CSV)
        def get_estacao(m):
            if m in [12, 1, 2]: return "Verão"
            elif m in [3, 4, 5]: return "Outono"
            elif m in [6, 7, 8]: return "Inverno"
            else: return "Primavera"
        df['estacao'] = df['mes'].apply(get_estacao)
        
    return df

df = carregar_dados_stats()

# Mapeamento de nomes amigáveis para as colunas
cols_map = {
    'radiacao_media': 'Radiação',
    'vento_medio': 'Vento',
    'vento_medio_kmh': 'Vento (km/h)', # Caso o nome varie
    'pressao_media': 'Pressão',
    'chuva_media_semanal': 'Chuva',
    'temperatura_media': 'Temperatura',
    'umidade_media': 'Umidade'
}
# Filtra apenas colunas que existem no DataFrame
cols_validas = {k: v for k, v in cols_map.items() if k in df.columns}
df_renomeado = df.rename(columns=cols_validas)
colunas_numericas = list(cols_validas.values())

st.markdown("---")

# --- 2. ANÁLISE DE CORRELAÇÃO (LADO A LADO) ---
st.subheader("1. Matrizes de Correlação")
st.info("Compare como as variáveis se relacionam linearmente (Pearson) vs. monotonicamente (Spearman).")

col_pearson, col_spearman = st.columns(2)

with col_pearson:
    st.markdown("#### 🔵 Pearson (Linear)")
    st.caption("Detecta relações proporcionais diretas (reta).")
    
    # Cálculo
    corr_p = df_renomeado[colunas_numericas].corr(method='pearson')
    
    # Plot
    fig_p, ax_p = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_p, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1, ax=ax_p)
    st.pyplot(fig_p)

with col_spearman:
    st.markdown("#### 🟢 Spearman (Rank)")
    st.caption("Detecta relações de crescimento conjunto, mesmo que não seja uma reta perfeita.")
    
    # Cálculo
    corr_s = df_renomeado[colunas_numericas].corr(method='spearman')
    
    # Plot
    fig_s, ax_s = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_s, annot=True, cmap='viridis', fmt=".2f", vmin=-1, vmax=1, ax=ax_s)
    st.pyplot(fig_s)

st.markdown("---")

# --- 3. TESTE DE HIPÓTESES AUTOMATIZADO ---
st.subheader("2. Teste de Hipóteses Automatizado")
st.markdown("Defina o cenário abaixo e o sistema escolherá o teste estatístico adequado (Teste T ou ANOVA).")

# --- CONFIGURAÇÃO DO TESTE ---
with st.container(border=True):
    col_conf1, col_conf2, col_conf3 = st.columns(3)
    
    with col_conf1:
        st.markdown("**1️⃣ O que você quer analisar?** (Variável Numérica)")
        var_analise = st.selectbox("Selecione a Métrica:", colunas_numericas)
        col_analise_original = [k for k, v in cols_validas.items() if v == var_analise][0]

    with col_conf2:
        st.markdown("**2️⃣ Como quer agrupar?** (Categorias)")
        opcoes_agrupamento = ['region', 'state', 'ano', 'estacao']
        # Adiciona 'mes' se existir e converte nomes
        labels_agrupamento = {'region': 'Região', 'state': 'Estado', 'ano': 'Ano', 'estacao': 'Estação', 'mes': 'Mês'}
        
        grupo_selecionado_key = st.selectbox(
            "Agrupar por:", 
            options=[op for op in opcoes_agrupamento if op in df.columns],
            format_func=lambda x: labels_agrupamento.get(x, x)
        )

    with col_conf3:
        st.markdown("**3️⃣ Quais grupos comparar?**")
        # Pega valores únicos da coluna de agrupamento selecionada
        valores_unicos = sorted(df[grupo_selecionado_key].unique().astype(str))
        
        grupos_escolhidos = st.multiselect(
            "Selecione os grupos (mínimo 2):",
            options=valores_unicos,
            default=valores_unicos[:2] # Já seleciona os 2 primeiros por padrão
        )

# --- EXECUÇÃO DO TESTE ---
if len(grupos_escolhidos) < 2:
    st.warning("⚠️ Selecione pelo menos 2 grupos para realizar uma comparação.")
else:
    # Preparar os dados filtrados
    dados_grupos = []
    nomes_grupos = []
    
    # Coletar as amostras para cada grupo escolhido
    for g in grupos_escolhidos:
        # Nota: Convertemos para string para garantir match com o filtro (anos as vezes sao int)
        amostra = df[df[grupo_selecionado_key].astype(str) == g][col_analise_original].dropna()
        if len(amostra) > 0:
            dados_grupos.append(amostra)
            nomes_grupos.append(g)
    
    # Verifica se temos dados suficientes
    if len(dados_grupos) < 2:
        st.error("Dados insuficientes nos grupos selecionados (muitos valores nulos ou vazios).")
    else:
        st.markdown(f"### 🧪 Resultado do Teste: {var_analise} por {labels_agrupamento.get(grupo_selecionado_key)}")
        
        # --- LÓGICA DE DECISÃO DO TESTE ---
        if len(dados_grupos) == 2:
            # --- TESTE T (2 Grupos) ---
            tipo_teste = "Teste t de Student (Independente)"
            stat, p_val = stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=False) # Welch's t-test é mais seguro
            
            explicacao = f"Comparando a média de **{nomes_grupos[0]}** contra **{nomes_grupos[1]}**."
            
        else:
            # --- ANOVA (3+ Grupos) ---
            tipo_teste = "ANOVA (One-Way)"
            stat, p_val = stats.f_oneway(*dados_grupos)
            
            explicacao = f"Comparando se existe diferença entre as médias de: **{', '.join(nomes_grupos)}**."

        # --- EXIBIÇÃO DOS RESULTADOS ---
        col_res1, col_res2 = st.columns([1, 2])
        
        with col_res1:
            st.metric("P-Valor (Significância)", f"{p_val:.4e}")
            st.metric("Estatística do Teste", f"{stat:.2f}")
            
        with col_res2:
            st.info(f"**Teste Utilizado:** {tipo_teste}")
            st.write(explicacao)
            
            st.markdown("---")
            if p_val < 0.05:
                st.success(f"✅ **Resultado Significativo!** (p < 0.05)")
                st.write(f"Há evidências estatísticas de que a média de **{var_analise}** muda dependendo do grupo selecionado.")
            else:
                st.error(f"❌ **Resultado Não Significativo** (p >= 0.05)")
                st.write(f"Não há evidências suficientes para dizer que as médias são diferentes. As variações observadas podem ser puro acaso.")

        # --- GRÁFICO DE CAIXA (BOXPLOT) PARA VISUALIZAR ---
        st.markdown("#### 👁️ Visualização da Distribuição")
        
        # Cria dataframe apenas com os grupos selecionados para plotar
        df_plot = df[df[grupo_selecionado_key].astype(str).isin(grupos_escolhidos)].copy()
        df_plot = df_plot.sort_values(grupo_selecionado_key)
        
        fig_box, ax_box = plt.subplots(figsize=(10, 4))
        sns.boxplot(x=grupo_selecionado_key, y=col_analise_original, data=df_plot, palette="Set2", ax=ax_box)
        ax_box.set_title(f"Distribuição de {var_analise} nos grupos selecionados")
        ax_box.set_xlabel(labels_agrupamento.get(grupo_selecionado_key))
        ax_box.set_ylabel(var_analise)
        st.pyplot(fig_box)
