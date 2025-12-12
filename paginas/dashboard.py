# import streamlit as st
# import pandas as pd
# import plotly.express as px

# # 1. Configuração da Página
# st.set_page_config(page_title="Análise Descritiva - Clima Brasil", layout="wide")

# # 2. Carregamento de Dados
# @st.cache_data
# def carregar_dados():
#     df = pd.read_csv("dataframe/clima_brasil_mensal_refinado_2015.csv")
#     df['mes'] = pd.to_datetime(df['periodo_ref'])
#     df['Data_Dia'] = df['mes'].dt.date
#     return df

# df = carregar_dados()

# # --- BARRA LATERAL (FILTROS) ---
# st.sidebar.header("Filtros")

# # Filtro de Estado
# estados = sorted(df['state'].unique().astype(str))
# estados_filtro = st.sidebar.multiselect("Selecione os Estados:", estados, default=estados)

# # Aplica o filtro no DataFrame
# if estados_filtro:
#     df_filtered = df[df['state'].isin(estados_filtro)]
#     titulo_resumo = "Resumo dos Estados Selecionados"
# else:
#     df_filtered = df
#     titulo_resumo = "Resumo GERAL (Todos os Estados)"

# # --- SELEÇÃO DE VARIÁVEL ---
# cols_numericas = {
#     'Chuva Média (mm)': 'chuva_media_acumulada', # media semanal da soma de chuva em todas as estações
#     'Temperatura Média (C)': 'temperatura_media',
#     'Umidade Média (%)': 'umidade_media', 
#     'Vento Médio (Km/h)': 'vento_medio_kmh', 
#     'Pressão Média (inHg)': 'pressao_media_inHg',
#     'Radiação Média (Kj/m²)': 'radiacao_media'
# }

# st.subheader("Configuração da Análise")

# # O usuário escolhe a variável
# var_label = st.selectbox(
#     "Escolha a variável para analisar:",
#     options=cols_numericas.keys() 
# )

# # 2. Pega a FECHADURA/VALOR (o nome técnico, ex: "chuva_media")
# var_coluna = cols_numericas[var_label]

# st.markdown("---")

# # --- ANÁLISE ESTATÍSTICA (Tabela) ---
# if not estados_filtro:
#     # CENÁRIO 1: NENHUM ESTADO SELECIONADO -> MOSTRAR APENAS NÚMEROS
#     st.subheader(f"🌍 Visão Geral: {var_label}")
    
#     # Criamos o DataFrame SEM a coluna estados, apenas com os valores
#     tabela_final = pd.DataFrame({
#         'count': [df[var_coluna].count()],
#         'mean': [df[var_coluna].mean()],
#         'std': [df[var_coluna].std()],
#         'min': [df[var_coluna].min()],
#         'max': [df[var_coluna].max()],
#         'median': [df[var_coluna].median()]
#     })

# else:
#     # CENÁRIO 2: ESTADOS SELECIONADOS -> MOSTRAR NOMES DOS ESTADOS
#     st.subheader(f"📍 Detalhamento por Estado: {var_label}")
    
#     df_filtered = df[df['state'].isin(estados_filtro)]
    
#     # Agrupamento por estado
#     tabela_final = df_filtered.groupby('state')[var_coluna].agg(
#         ['count', 'mean', 'std', 'min', 'max', 'median']
#     ).reset_index()
    
#     tabela_final = tabela_final.sort_values(by='mean', ascending=False)

# altura_dinamica = (len(tabela_final) * 35) + 38
# # EXIBIÇÃO DA TABELA
# st.dataframe(
#     tabela_final,
#     use_container_width=True,
#     height=altura_dinamica,
#     hide_index=True,
#     column_config={
#         "state": st.column_config.TextColumn("Estado", width="large"), # Adaptação de rótulo
#         "count": st.column_config.NumberColumn("Nº Registros", format="%d"),
#         "mean": st.column_config.NumberColumn("Média", format="%.2f"),
#         "std": st.column_config.NumberColumn("Desv. Padrão", format="%.2f"),
#         "min": st.column_config.NumberColumn("Mínimo", format="%.2f"),
#         "max": st.column_config.NumberColumn("Máximo", format="%.2f"),
#         "median": st.column_config.NumberColumn("Mediana", format="%.2f")
#     }
# )

# # --- GRÁFICOS ---
# st.markdown("---")
# st.subheader("📈 Visualização Gráfica")

# # Define configurações dinâmicas baseadas no filtro
# if not estados_filtro:
#     # MODO GERAL: Gráficos únicos (sem separar por cores de estados)
#     cor_grafico = None           
#     eixo_x_box = None            
#     colunas_agrupamento = ['Data_Dia'] 
#     sulfixo_titulo = " (Visão Global)"
# else:
#     # MODO DETALHADO: Separa por cores dos estados
#     cor_grafico = "state"
#     eixo_x_box = "state"
#     colunas_agrupamento = ['Data_Dia', 'state'] 
#     sulfixo_titulo = " (por Estado)"

# # st.markdown("**Comparação (Boxplot)**") # (Mantido do original)
# st.markdown("**Comparação (Boxplot)**")
# fig_box = px.box(
#     df_filtered, 
#     x=eixo_x_box, 
#     y=var_coluna, 
#     color=cor_grafico, 
#     title=f"Boxplot de {var_label}{sulfixo_titulo}"
# )

# fig_box.update_layout(
#     showlegend=False,
#     xaxis=dict(
#         fixedrange=True,
#         title="Estados"
#     ),
#     yaxis=dict(
#         fixedrange=True,
#         title=f"{var_label}"
#     )
# )

# if not estados_filtro:
#     fig_box.update_layout(xaxis_title="Global")

# st.plotly_chart(
#     fig_box, 
#     use_container_width=True, 
#     theme="streamlit",  
#     config={
#         'displaylogo': False,
#         'modeBarButtonsToRemove': [
#             'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
#             'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'
#         ]
#     }
# )

# # Gráfico de Linha (Série Temporal)
# st.markdown("**Evolução no Tempo (Média Diária)**")

# # Agrupamento dinâmico
# df_line = df_filtered.groupby(colunas_agrupamento)[var_coluna].mean().reset_index()

# fig_line = px.line(
#     df_line, 
#     x="Data_Dia", 
#     y=var_coluna, 
#     color=cor_grafico, 
#     markers=True,
#     title=f"Evolução de {var_label}{sulfixo_titulo}"
# )
# st.plotly_chart(fig_line, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Análise Descritiva - Clima Brasil", layout="wide")

# 2. Carregamento de Dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dataframe/clima_brasil_mensal_refinado_2015.csv")
    df['mes'] = pd.to_datetime(df['periodo_ref'])
    df['Data_Dia'] = df['mes'].dt.date
    return df

df = carregar_dados()

# --- TÍTULO E FILTROS GLOBAIS (TOPO DA PÁGINA) ---
st.title("Dashboard Climático")

# Container para os filtros principais
with st.container():
    st.subheader("Filtros Globais")
    col_nav, col_reg, col_est = st.columns(3)

    # 1. Nível de Análise
    with col_nav:
        nivel_analise = st.radio(
            "Nível de Análise:",
            ["Regional", "Estadual"],
            horizontal=True,
            help="Define o agrupamento dos gráficos abaixo."
        )

    # 2. Filtro de Região (Sempre visível)
    with col_reg:
        regioes_disponiveis = sorted(df['region'].unique().astype(str))
        regioes_sel = st.multiselect(
            "Selecione as Regiões:", 
            regioes_disponiveis, 
            default=regioes_disponiveis
        )

    # Lógica de Filtragem Inicial
    if regioes_sel:
        df_filtrado = df[df['region'].isin(regioes_sel)]
    else:
        df_filtrado = df[df['region'].isin([])] # Zera se nada selecionado

    # 3. Filtro de Estado (Apenas se Nível == Estadual)
    with col_est:
        if nivel_analise == "Estadual":
            estados_disponiveis = sorted(df_filtrado['state'].unique().astype(str))
            estados_sel = st.multiselect(
                "Filtrar Estados Específicos:", 
                estados_disponiveis, 
                default=estados_disponiveis
            )
            # Refina o DF se houver estados selecionados
            if estados_sel:
                df_filtrado = df_filtrado[df_filtrado['state'].isin(estados_sel)]
        else:
            st.info("Visualização agrupada por Região.")

st.markdown("---")

# --- SELEÇÃO DE VARIÁVEL ---
cols_numericas = {
    'Chuva Média (mm)': 'chuva_media_acumulada',
    'Temperatura Média (C)': 'temperatura_media',
    'Umidade Média (%)': 'umidade_media', 
    'Vento Médio (Km/h)': 'vento_medio_kmh', 
    'Pressão Média (inHg)': 'pressao_media_inHg',
    'Radiação Média (Kj/m²)': 'radiacao_media'
}

var_label = st.selectbox("Escolha a variável para analisar:", options=cols_numericas.keys())
var_coluna = cols_numericas[var_label]

st.markdown("---")

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado disponível. Selecione ao menos uma Região/Estado acima.")

# --- VISUALIZAÇÃO: MODO REGIONAL ---
elif nivel_analise == "Regional":
    st.subheader(f"🌍 Visão Regional: {var_label}")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("**Distribuição (Boxplot)**")
        fig_box = px.box(
            df_filtrado, 
            x="region", 
            y=var_coluna, 
            color="region", 
            points="outliers"
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
    with col_g2:
        st.markdown("**Evolução Temporal Comparativa**")
        # Agrupa por dia e região para a linha
        df_line = df_filtrado.groupby(['Data_Dia', 'region'])[var_coluna].mean().reset_index()
        
        fig_line = px.line(
            df_line, 
            x="Data_Dia", 
            y=var_coluna, 
            color="region",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with st.expander("Ver Estatísticas Regionais"):
        st.dataframe(df_filtrado.groupby('region')[var_coluna].describe(), use_container_width=True)

# --- VISUALIZAÇÃO: MODO ESTADUAL ---
elif nivel_analise == "Estadual":
    st.subheader(f"📍 Visão Estadual: {var_label}")
    
    # 1. Boxplot e Linha Comparativa (Lado a Lado)
    col_est1, col_est2 = st.columns(2)
    
    with col_est1:
        st.markdown("**Comparativo de Distribuição**")
        fig_box_est = px.box(
            df_filtrado, 
            x="state", 
            y=var_coluna, 
            color="region", # Mantém cor da região para contexto
            title=f"Distribuição ({len(df_filtrado['state'].unique())} estados selecionados)"
        )
        fig_box_est.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_box_est, use_container_width=True)
    
    with col_est2:
        st.markdown("**Evolução Temporal Comparativa**")
        # Agrupa por dia e estado (garante linhas limpas)
        df_line_est = df_filtrado.groupby(['Data_Dia', 'state'])[var_coluna].mean().reset_index()
        
        fig_line_est = px.line(
            df_line_est,
            x="Data_Dia",
            y=var_coluna,
            color="state", # Cada estado é uma linha
            markers=True,
            title=f"Evolução ({len(df_filtrado['state'].unique())} estados selecionados)"
        )
        st.plotly_chart(fig_line_est, use_container_width=True)
    
    st.markdown("---")
    
    # 2. Destaque Individual (Foco)
    st.markdown("**🔍 Detalhe Individual (Foco em 1 Estado)**")
    
    col_sel, col_graph = st.columns([1, 3])
    
    with col_sel:
        # Lista apenas os estados que passaram no filtro global
        lista_estados_filtrados = sorted(df_filtrado['state'].unique())
        estado_destaque = st.selectbox("Selecione para destacar:", lista_estados_filtrados)
    
    with col_graph:
        if estado_destaque:
            df_destaque = df_filtrado[df_filtrado['state'] == estado_destaque]
            # Agrupa para garantir unicidade temporal
            df_line_dest = df_destaque.groupby('Data_Dia')[var_coluna].mean().reset_index()
            
            fig_dest = px.line(
                df_line_dest, 
                x="Data_Dia", 
                y=var_coluna, 
                markers=True,
                title=f"Evolução Isolada: {estado_destaque}"
            )
            fig_dest.update_traces(line_color='#FF4B4B', line_width=3) # Destaque visual
            st.plotly_chart(fig_dest, use_container_width=True)