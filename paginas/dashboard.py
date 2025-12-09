import streamlit as st
import pandas as pd
import plotly.express as px

col_sel1, col_sel2 = st.columns([1, 3])
with col_sel1:
    var_label = st.selectbox("Escolha a Variável:", list(cols_numericas.keys()))
    var_coluna = cols_numericas[var_label]

st.markdown("---")

# 1. Tabela de Resumo
st.subheader(f"Estatísticas: {var_label}")
# Tabela agrupada por País (opcional) ou geral
if len(sel_pais) > 1:
    st.markdown("**Por País:**")
    stats_pais = df_filtered.groupby('country')[var_coluna].agg(['mean', 'max', 'min', 'std']).reset_index()
    stats_pais.columns = ['País', 'Média', 'Máxima', 'Mínima', 'Desvio Padrão']
    st.dataframe(stats_pais.style.format({"Média": "{:.3f}", "Desvio Padrão": "{:.3f}"}), use_container_width=True)
else:
    stats = df_filtered[var_coluna].agg(['mean', 'max', 'min', 'std']).to_frame().T
    stats.columns = ['Média', 'Máxima', 'Mínima', 'Desvio Padrão']
    st.dataframe(stats.style.format({"Média": "{:.3f}", "Desvio Padrão": "{:.3f}"}), use_container_width=True)

# # 2. Gráficos
# c1, c2 = st.columns(2)

# with c1:
#     st.markdown("#### Distribuição (Histograma)")
#     fig_hist = px.histogram(df_filtered, x=var_coluna, color="country", nbins=30, 
#                             title=f"Histograma de {var_label}")
#     st.plotly_chart(fig_hist, use_container_width=True)
    
# with c2:
#     st.markdown("#### Comparação (Boxplot)")
#     fig_box = px.box(df_filtered, x="country", y=var_coluna, color="country", 
#                         title=f"Boxplot de {var_label}")
#     st.plotly_chart(fig_box, use_container_width=True)
    
# st.markdown("#### Evolução Temporal (Média Diária)")
# # Agrupa por dia para limpar o gráfico
# df_line = df_filtered.groupby(['Data_Dia', 'country'])[var_coluna].mean().reset_index()

# fig_line = px.line(df_line, x="Data_Dia", y=var_coluna, color="country", 
#                     title=f"Série Temporal de {var_label}")
# st.plotly_chart(fig_line, use_container_width=True)