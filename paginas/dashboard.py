import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Análise Descritiva - Clima Brasil", layout="wide")

# --- CONFIGURAÇÃO PADRÃO DOS GRÁFICOS ---
config_padrao = {
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'
    ]
}

# 2. Carregamento de Dados
@st.cache_data
def carregar_dados():
    # Certifique-se que o caminho do arquivo está correto no seu projeto
    df = pd.read_csv("dataframe/clima_brasil_mensal_refinado_2015.csv")
    df['mes'] = pd.to_datetime(df['periodo_ref'])
    df['Data_Dia'] = df['mes'].dt.date
    # Cria a coluna Ano para o filtro
    df['Ano'] = df['mes'].dt.year
    return df

df = carregar_dados()

# --- CONFIGURAÇÃO AUTOMÁTICA DE CORES ---
paletas_estados_matte = {
    'NE': ["#D4E157", "#FFEE58", "#FDD835", "#FFCA28", "#FFA726", "#FF7043", "#8D6E63", "#FFCC80", "#E6EE9C"],
    'N':  ["#4DB6AC", "#81C784", "#AED581", "#43A047", "#26A69A", "#558B2F", "#00897B"],
    'SE': ["#4FC3F7", "#64B5F6", "#7986CB", "#9575CD"],
    'CO': ["#FF8A65", "#F06292", "#BA68C8", "#E57373"],
    'S':  ["#CE93D8", "#BA68C8", "#9575CD"]
}

paletas_regioes_pastel = {
    'NE': "#FFF59D", 'N':  "#C8E6C9", 'SE': "#BBDEFB", 'CO': "#F8BBD0", 'S':  "#E1BEE7"
}

# ---------------------------------------------------------
# 2. LÓGICA DE APLICAÇÃO
# ---------------------------------------------------------

unique_regions = df['region'].unique()

# --- Configura Cores das REGIÕES ---
cores_regioes = {}
for reg in unique_regions:
    cores_regioes[reg] = paletas_regioes_pastel.get(reg, "#EEEEEE")

# --- Configura Cores dos ESTADOS ---
cores_estados = {}
for regiao in unique_regions:
    lista_cores = paletas_estados_matte.get(regiao, [])
    estados_da_regiao = sorted(df[df['region'] == regiao]['state'].unique())
    for estado, cor in zip(estados_da_regiao, lista_cores):
        cores_estados[estado] = cor

# --- TÍTULO ---
st.title("Dashboard Climático")

# --- SELEÇÃO DE VARIÁVEIS ---
cols_numericas = {
    'Chuva Média (mm)': 'chuva_media_acumulada',
    'Temperatura Média (C)': 'temperatura_media',
    'Umidade Média (%)': 'umidade_media', 
    'Vento Médio (Km/h)': 'vento_medio_kmh', 
    'Pressão Média (inHg)': 'pressao_media_inHg',
    'Radiação Média (Kj/m²)': 'radiacao_media'
}

var_label = st.selectbox("Escolha a Variável:", options=cols_numericas.keys())
var_coluna = cols_numericas[var_label]

# --- FILTROS LATERAIS (Região e Tempo) ---
col_filtros_1, col_filtros_2 = st.columns([2, 1])

with col_filtros_1:
    regioes_disponiveis = sorted(df['region'].unique().astype(str))
    regioes_sel = st.multiselect(
        "Filtre as Regiões:", 
        regioes_disponiveis, 
        default=regioes_disponiveis
    )

with col_filtros_2:
    st.write("")
    st.write("")
    usar_filtro_ano = st.checkbox("Filtrar por Ano?")
    
    # Valores padrão (Todo o dataset)
    df_filtrado_tempo = df
    
    if usar_filtro_ano:
        min_ano = int(df['Ano'].min())
        max_ano = int(df['Ano'].max())
        
        if min_ano == max_ano:
            st.info(f"Ano único disponível: {min_ano}")
            ano_inicio, ano_fim = min_ano, max_ano
        else:
            ano_inicio, ano_fim = st.slider(
                "Faixa de Anos:",
                min_value=min_ano,
                max_value=max_ano,
                value=(min_ano, max_ano)
            )
        
        # Aplica filtro de tempo
        df_filtrado_tempo = df[(df['Ano'] >= ano_inicio) & (df['Ano'] <= ano_fim)]

# --- LÓGICA DE DADOS ---

# 1. Lista de Estados ESTÁVEL (Baseada apenas nas Regiões selecionadas, ignora o Tempo)
if regioes_sel:
    df_base_regiao = df[df['region'].isin(regioes_sel)]
else:
    df_base_regiao = df[df['region'].isin([])]

# 2. Dados para GRÁFICOS (Baseado em Região + Tempo)
if regioes_sel:
    df_regiao = df_filtrado_tempo[df_filtrado_tempo['region'].isin(regioes_sel)]
else:
    df_regiao = df_filtrado_tempo[df_filtrado_tempo['region'].isin([])]

st.markdown("---")

# --- VISUALIZAÇÃO (ABAS) ---
if df_regiao.empty:
    st.warning("⚠️ Sem dados para os filtros selecionados (Verifique a Região ou o Ano).")
else:
    tab_reg, tab_est = st.tabs(["🌍 Visão por Região", "📍 Visão por Estado"])

    # === ABA 1: ANÁLISE POR REGIÃO ===
    with tab_reg:
        st.subheader(f"Análise Regional: {var_label}")
        
        # Prepara ordem alfabética das regiões presentes
        ordem_regioes = sorted(df_regiao['region'].unique())
        
        with st.expander("### 📊 Estatísticas Detalhadas por Região", expanded=False):
            tabela_reg = df_regiao.groupby('region')[var_coluna].agg(
                ['count', 'mean', 'std', 'min', 'max', 'median']
            ).reset_index().sort_values(by='region', ascending=True)

            st.dataframe(
                tabela_reg,
                use_container_width=True,
                hide_index=True,
                column_config={"region": "Região", "mean": st.column_config.NumberColumn("Média", format="%.2f")}
            )

        # === Boxplot (Região) ===
        st.markdown("**Distribuição (Boxplot)**")
        fig_box_reg = px.box(
            df_regiao, 
            x="region", 
            y=var_coluna, 
            color="region", 
            points="outliers",
            color_discrete_map=cores_regioes,
            category_orders={"region": ordem_regioes}
        )
        fig_box_reg.update_layout(
            showlegend=False, 
            xaxis=dict(fixedrange=True, title="Regiões"), 
            yaxis=dict(fixedrange=True, title=var_label)
        )
        st.plotly_chart(fig_box_reg, use_container_width=True, config=config_padrao)
            
        # === Linhas (Região) ===
        st.markdown("**Evolução Temporal (Média das Regiões)**")
        df_line_reg = df_regiao.groupby(['Data_Dia', 'region'])[var_coluna].mean().reset_index()
        
        fig_line_reg = px.line(
            df_line_reg, 
            x="Data_Dia", 
            y=var_coluna, 
            color="region",
            markers=True,
            color_discrete_map=cores_regioes,
            category_orders={"region": ordem_regioes}
        )
        # CONFIGURAÇÃO DE LAYOUT TRAVADO
        fig_line_reg.update_layout(
            xaxis=dict(fixedrange=True, title="Data"), 
            yaxis=dict(fixedrange=True, title=var_label)
        )
        st.plotly_chart(fig_line_reg, use_container_width=True, config=config_padrao)

    # === ABA 2: ANÁLISE POR ESTADO ===
    with tab_est:
        st.subheader(f"Análise Estadual: {var_label}")

        # Filtro de Estado
        estados_disponiveis = sorted(df_base_regiao['state'].unique().astype(str))
        estados_sel = st.multiselect(
            "Filtre os Estados (Opcional):", 
            estados_disponiveis, 
            default=estados_disponiveis
        )

        if estados_sel:
            df_estado = df_regiao[df_regiao['state'].isin(estados_sel)]
        else:
            df_estado = df_regiao

        with st.expander("### 📊 Estatísticas Detalhadas por Estados", expanded=False):
            tabela_est = df_estado.groupby('state')[var_coluna].agg(['count', 'mean', 'std', 'min', 'max', 'median']).reset_index().sort_values(by='state', ascending=True)
            altura_est = (len(tabela_est) + 1) * 35 + 3

            st.dataframe(
                tabela_est,
                use_container_width=True,
                height=altura_est,
                hide_index=True,
                column_config={"state": "Estado", "mean": st.column_config.NumberColumn("Média", format="%.2f")}
            )

        # === Boxplot (Estado) ===
        if not df_estado.empty:
            st.markdown("**Comparativo de Distribuição**")
            ordem_estados = sorted(df_estado['state'].unique())
            
            fig_box_est = px.box(
                df_estado, 
                x="state", 
                y=var_coluna, 
                color="state",
                title=f"Distribuição de {var_label} (por Estado)",
                color_discrete_map=cores_estados,
                category_orders={"state": ordem_estados}
            )
            # CONFIGURAÇÃO DE LAYOUT TRAVADO
            fig_box_est.update_layout(
                showlegend=False, 
                xaxis=dict(fixedrange=True, title="Estados"), 
                yaxis=dict(fixedrange=True, title=var_label)
            )
            st.plotly_chart(fig_box_est, use_container_width=True, config=config_padrao)
        else:
            st.info("Sem dados para exibir no Boxplot.")
        
        # === Linha (Individual) ===
        st.markdown("**🔍 Detalhe Individual (Foco em 1 Estado)**")
        col_sel, col_graph = st.columns([1, 3])
        with col_sel:
            estado_destaque = st.selectbox(
                "Selecione um estado para destacar:", 
                estados_disponiveis,
                index=0 if estados_disponiveis else None
            )
        with col_graph:
            if estado_destaque:
                df_destaque = df_regiao[df_regiao['state'] == estado_destaque]
                
                if not df_destaque.empty:
                    df_line_dest = df_destaque.groupby('Data_Dia')[var_coluna].mean().reset_index()  
                    
                    fig_dest = px.line(
                        df_line_dest, 
                        x="Data_Dia", 
                        y=var_coluna, 
                        markers=True,
                        title=f"Evolução Isolada: {estado_destaque}"
                    )
                    
                    cor_estado = cores_estados.get(estado_destaque, '#FF4B4B')
                    fig_dest.update_traces(line_color=cor_estado, line_width=3)
                    
                    # CONFIGURAÇÃO DE LAYOUT TRAVADO
                    fig_dest.update_layout(
                        showlegend=False, 
                        xaxis=dict(fixedrange=True, title="Data"), 
                        yaxis=dict(fixedrange=True, title=var_label)
                    )
                    
                    st.plotly_chart(fig_dest, use_container_width=True, config=config_padrao)
                else:
                    st.warning(f"Não há dados para {estado_destaque} no período selecionado.")