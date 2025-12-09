import streamlit as st
cols_numericas = ['Velocidade do Vento (Km/h)', 'Pressão (pol)', 'Precipitação (mm)', 
                      'Umidade (%)', 'Cobertura de Nuvens (%)', 'Temperatura (C)']
    
    var_selecionada = st.selectbox("Selecione a Variável para Análise:", cols_numericas, index=0)
    
    st.subheader(f"Estatísticas de: {var_selecionada}")
    
    # 1. Tabela com Média, Máxima e Mínima
    stats = df_filtered[var_selecionada].agg(['mean', 'max', 'min', 'std']).to_frame().T
    stats.columns = ['Média', 'Máxima', 'Mínima', 'Desvio Padrão']
    
    # Formatação bonita
    st.dataframe(stats.style.format("{:.2f}"), use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Histograma")
        fig_hist = px.histogram(df_filtered, x=var_selecionada, color="País", nbins=30, 
                                title=f"Distribuição de {var_selecionada}")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col2:
        st.markdown("### Boxplot")
        fig_box = px.box(df_filtered, x="País", y=var_selecionada, color="País", 
                         title=f"Boxplot de {var_selecionada} por País")
        st.plotly_chart(fig_box, use_container_width=True)
        
    st.markdown("### Série Temporal")
    # Agrupando por data para o gráfico de linha não ficar bagunçado
    df_line = df_filtered.groupby(['Data', 'País'])[var_selecionada].mean().reset_index()
    
    fig_line = px.line(df_line, x="Data", y=var_selecionada, color="País", 
                       title=f"Evolução Média de {var_selecionada} no Tempo")
    st.plotly_chart(fig_line, use_container_width=True)