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

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros Globais")

# 1. Filtro de Região
regioes_disponiveis = sorted(df['region'].unique().astype(str))
regioes_sel = st.sidebar.multiselect(
    "Selecione as Regiões:", 
    regioes_disponiveis, 
    default=regioes_disponiveis
)

# Filtra o DF principal pelas regiões
if regioes_sel:
    df_regiao = df[df['region'].isin(regioes_sel)]
else:
    df_regiao = df[df['region'].isin([])] # DF vazio se nada selecionado

# 2. Filtro de Estado (Multiselect para Boxplot e Tabela)
estados_disponiveis = sorted(df_regiao['state'].unique().astype(str))
estados_sel = st.sidebar.multiselect(
    "Filtrar Estados (Boxplot/Tabela):", 
    estados_disponiveis, 
    default=estados_disponiveis
)

# Filtra para visualizações específicas de estado
if estados_sel:
    df_estado = df_regiao[df_regiao['state'].isin(estados_sel)]
else:
    df_estado = df_regiao # Se limpar estados, mantém os dados da região

# --- SELEÇÃO DE VARIÁVEL ---
cols_numericas = {
    'Chuva Média (mm)': 'chuva_media_acumulada',
    'Temperatura Média (C)': 'temperatura_media',
    'Umidade Média (%)': 'umidade_media', 
    'Vento Médio (Km/h)': 'vento_medio_kmh', 
    'Pressão Média (inHg)': 'pressao_media_inHg',
    'Radiação Média (Kj/m²)': 'radiacao_media'
}

st.subheader("Configuração da Análise")
var_label = st.selectbox("Escolha a variável para analisar:", options=cols_numericas.keys())
var_coluna = cols_numericas[var_label]

st.markdown("---")

# --- ANÁLISE DE DISTRIBUIÇÃO (BOXPLOTS) ---
st.subheader(f"📊 Distribuição: {var_label}")

# Usando abas para organizar as visões
tab_reg, tab_est = st.tabs(["Por Região", "Por Estado"])

with tab_reg:
    if not df_regiao.empty:
        fig_box_reg = px.box(
            df_regiao, 
            x="region", 
            y=var_coluna, 
            color="region", 
            title="Distribuição dos Dados por Região",
            points="outliers" # mostra apenas outliers para não poluir
        )
        st.plotly_chart(fig_box_reg, use_container_width=True)
    else:
        st.warning("Selecione ao menos uma região.")

with tab_est:
    if not df_estado.empty:
        fig_box_est = px.box(
            df_estado, 
            x="state", 
            y=var_coluna, 
            color="state", 
            title="Distribuição dos Dados por Estado (Filtrados)"
        )
        st.plotly_chart(fig_box_est, use_container_width=True)
    else:
        st.warning("Nenhum estado selecionado.")

st.markdown("---")

# --- ANÁLISE TEMPORAL (LINHAS) ---
st.subheader("📈 Evolução Temporal")

col1, col2 = st.columns(2)

# GRÁFICO 1: Evolução por REGIÃO (Agrupado)
with col1:
    st.markdown("**Média por Região**")
    if not df_regiao.empty:
        # Agrupa por dia e região
        df_line_reg = df_regiao.groupby(['Data_Dia', 'region'])[var_coluna].mean().reset_index()
        
        fig_line_reg = px.line(
            df_line_reg, 
            x="Data_Dia", 
            y=var_coluna, 
            color="region",
            markers=True,
            title=f"Evolução das Regiões Selecionadas"
        )
        st.plotly_chart(fig_line_reg, use_container_width=True)
    else:
        st.info("Aguardando seleção de regiões...")

# GRÁFICO 2: Evolução por ESTADO ÚNICO (Destaque)
with col2:
    st.markdown("**Destaque de Estado**")
    
    # Selectbox específico para escolher UM estado
    # As opções vêm das regiões que já foram filtradas na sidebar
    estado_destaque = st.selectbox(
        "Selecione um estado para visualizar individualmente:",
        options=estados_disponiveis,
        index=0 if len(estados_disponiveis) > 0 else None
    )
    
    if estado_destaque:
        df_destaque = df[df['state'] == estado_destaque]
        # Agrupa caso haja mais de uma entrada (segurança), mas no mensal costuma ser único
        df_line_dest = df_destaque.groupby('Data_Dia')[var_coluna].mean().reset_index()
        
        fig_dest = px.line(
            df_line_dest, 
            x="Data_Dia", 
            y=var_coluna, 
            markers=True,
            title=f"Evolução em: {estado_destaque}"
        )
        # Ajuste de cor para destacar
        fig_dest.update_traces(line_color='#FF4B4B') 
        st.plotly_chart(fig_dest, use_container_width=True)
    else:
        st.info("Nenhum estado disponível para destaque.")

# --- TABELA DE DADOS (Opcional, abaixo dos gráficos) ---
with st.expander("Ver Tabela Detalhada (Dados Filtrados por Estado)"):
    if not df_estado.empty:
        # Tabela resumo por estado
        tabela_final = df_estado.groupby('state')[var_coluna].agg(
            ['count', 'mean', 'std', 'min', 'max']
        ).reset_index().sort_values(by='mean', ascending=False)
        
        st.dataframe(
            tabela_final,
            use_container_width=True,
            hide_index=True,
            column_config={
                "state": "Estado",
                "mean": st.column_config.NumberColumn("Média", format="%.2f"),
                "std": st.column_config.NumberColumn("Desv. Pad.", format="%.2f")
            }
        )