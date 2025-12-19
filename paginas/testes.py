import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

# --- 3. TESTE DE HIPÓTESES ---
st.subheader("2. Teste de Hipóteses Automatizado")

# Configuração
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
    # Filtra dados
    df_plot = df[df[grupo_key].astype(str).isin(grupos_escolhidos)].copy()
    df_plot = df_plot.sort_values(grupo_key)
    
    dados_grupos = [df_plot[df_plot[grupo_key].astype(str) == g][col_analise_original].dropna() for g in grupos_escolhidos]

    if len(dados_grupos) < 2:
        st.error("Dados insuficientes.")
    else:
        # Estatística
        if len(dados_grupos) == 2:
            tipo, stat, p_val = "Teste t (Student)", *stats.ttest_ind(dados_grupos[0], dados_grupos[1], equal_var=False)
        else:
            tipo, stat, p_val = "ANOVA", *stats.f_oneway(*dados_grupos)

        # Exibição Resultados
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
            
            # --- CRIAÇÃO DO GRÁFICO COMBINADO (HISTOGRAMA + BOXPLOT) ---
            # Cria figura com 2 subplots (o de cima é o Histograma, o de baixo é o Boxplot)
            # gridspec_kw={'height_ratios': (.15, .85)} define que o boxplot é menorzinho embaixo, ou meio a meio
            fig, (ax_box, ax_hist) = plt.subplots(
                2, 1, 
                sharex=True, 
                figsize=(10, 8),
                gridspec_kw={"height_ratios": (.15, .85)} # Boxplot pequeno em cima, Histograma grande embaixo? Ou o contrário?
                # Vamos fazer padrão: Boxplot em cima (15%), Histograma embaixo (85%) ou vice-versa.
                # O pedido foi "em cima ou embaixo". Vou colocar Boxplot no topo e Histograma embaixo.
            )
            
            # 1. Boxplot (Topo)
            sns.boxplot(x=col_analise_original, y=grupo_key, data=df_plot, orient='h', ax=ax_box, palette="Set2")
            ax_box.set(xlabel='') # Remove label x do topo para não duplicar
            ax_box.set_title("")
            
            # 2. Histograma / KDE (Baixo)
            sns.histplot(data=df_plot, x=col_analise_original, hue=grupo_key, kde=True, element="step", ax=ax_hist, palette="Set2")
            ax_hist.set_xlabel(var_analise)
            
            st.pyplot(fig)
