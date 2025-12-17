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

# --- CONFIGURAÇÃO PADRÃO DE PLOTLY (Reutilizável) ---
# Define os botões que serão removidos de todos os gráficos
config_padrao = {
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'
    ]
}

# --- TÍTULO ---
st.title("Dashboard Climático")

# --- FILTROS GLOBAIS (EM CIMA DA PÁGINA) ---
col_var, col_reg = st.columns([1, 2])

cols_numericas = {
    'Chuva Média (mm)': 'chuva_media_acumulada',
    'Temperatura Média (C)': 'temperatura_media',
    'Umidade Média (%)': 'umidade_media', 
    'Vento Médio (Km/h)': 'vento_medio_kmh', 
    'Pressão Média (inHg)': 'pressao_media_inHg',
    'Radiação Média (Kj/m²)': 'radiacao_media'
}

with col_var:
    var_label = st.selectbox("1. Escolha a Variável:", options=cols_numericas.keys())
    var_coluna = cols_numericas[var_label]

with col_reg:
    regioes_disponiveis = sorted(df['region'].unique().astype(str))
    regioes_sel = st.multiselect(
        "2. Filtre as Regiões (Impacta todas as abas):", 
        regioes_disponiveis, 
        default=regioes_disponiveis
    )

# Lógica de Filtragem Principal
if regioes_sel:
    df_regiao = df[df['region'].isin(regioes_sel)]
else:
    df_regiao = df[df['region'].isin([])] # Zera se nada selecionado

st.markdown("---")

# --- VISUALIZAÇÃO (ABAS) ---
if df_regiao.empty:
    st.warning("⚠️ Nenhuma região selecionada acima.")
else:
    tab_reg, tab_est = st.tabs(["🌍 Visão por Região", "📍 Visão por Estado"])

    # === ABA 1: ANÁLISE POR REGIÃO ===
    with tab_reg:
        st.subheader(f"Análise Regional: {var_label}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Distribuição (Boxplot)**")
            fig_box_reg = px.box(
                df_regiao, 
                x="region", 
                y=var_coluna, 
                color="region", 
                points="outliers"
            )
            # Aplica config padrão
            fig_box_reg.update_layout(
                xaxis=dict(fixedrange=True, title="Região"),
                yaxis=dict(fixedrange=True, title=var_label),
                showlegend=False
            )
            st.plotly_chart(fig_box_reg, use_container_width=True, theme="streamlit", config=config_padrao)
            
        with col2:
            st.markdown("**Evolução Temporal (Média das Regiões)**")
            df_line_reg = df_regiao.groupby(['Data_Dia', 'region'])[var_coluna].mean().reset_index()
            
            fig_line_reg = px.line(
                df_line_reg, 
                x="Data_Dia", 
                y=var_coluna, 
                color="region",
                markers=True
            )
            # Aplica config padrão
            fig_line_reg.update_layout(
                xaxis=dict(fixedrange=True, title="Data"),
                yaxis=dict(fixedrange=True, title=var_label)
            )
            st.plotly_chart(fig_line_reg, use_container_width=True, theme="streamlit", config=config_padrao)

        # --- TABELA DE ESTATÍSTICAS POR REGIÃO ---
        with st.expander("### 📊 Estatísticas Detalhadas por Região", expanded=False):
            tabela_reg = df_regiao.groupby('region')[var_coluna].agg(
                ['count', 'mean', 'std', 'min', 'max', 'median']
            ).reset_index().sort_values(by='mean', ascending=False)

            st.dataframe(
                tabela_reg,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "region": "Região",
                    "count": st.column_config.NumberColumn("Nº Registros", format="%d"),
                    "mean": st.column_config.NumberColumn("Média", format="%.2f"),
                    "std": st.column_config.NumberColumn("Desv. Padrão", format="%.2f"),
                    "min": st.column_config.NumberColumn("Mínimo", format="%.2f"),
                    "max": st.column_config.NumberColumn("Máximo", format="%.2f"),
                    "median": st.column_config.NumberColumn("Mediana", format="%.2f")
                }
            )

    # === ABA 2: ANÁLISE POR ESTADO ===
    with tab_est:
        st.subheader(f"Análise Estadual: {var_label}")
        
        # Filtro de Estado (LOCAL)
        estados_disponiveis = sorted(df_regiao['state'].unique().astype(str))
        estados_sel = st.multiselect(
            "3. Filtre os Estados (Opcional):", 
            estados_disponiveis, 
            default=estados_disponiveis
        )
        
        # Cria DF específico para esta aba
        if estados_sel:
            df_estado = df_regiao[df_regiao['state'].isin(estados_sel)]
        else:
            df_estado = df_regiao
            
        col_est1, col_est2 = st.columns(2)
        
        with col_est1:
            if not df_estado.empty:
                st.markdown("**Comparativo de Distribuição**")
                
                fig_box_est = px.box(
                    df_estado, 
                    x="state", 
                    y=var_coluna, 
                    color="state", 
                    title=f"Distribuição de {var_label}"
                )
                # Aplica config padrão + eixos travados
                fig_box_est.update_layout(
                    showlegend=False,
                    xaxis=dict(fixedrange=True, title="Estados"),
                    yaxis=dict(fixedrange=True, title=var_label)
                )
                st.plotly_chart(fig_box_est, use_container_width=True, theme="streamlit", config=config_padrao)
            else:
                st.info("Selecione estados para ver o boxplot.")
        
        with col_est2:
            if not df_estado.empty:
                st.markdown("**Comparativo Temporal**")
                df_line_est = df_estado.groupby(['Data_Dia', 'state'])[var_coluna].mean().reset_index()
                
                fig_line_est = px.line(
                    df_line_est,
                    x="Data_Dia",
                    y=var_coluna,
                    color="state", 
                    markers=True,
                    title=f"Evolução"
                )
                # Aplica config padrão
                fig_line_est.update_layout(
                    xaxis=dict(fixedrange=True, title="Data"),
                    yaxis=dict(fixedrange=True, title=var_label)
                )
                st.plotly_chart(fig_line_est, use_container_width=True, theme="streamlit", config=config_padrao)
            else:
                st.info("Selecione estados para ver a evolução.")
        
        # --- TABELA DE ESTATÍSTICAS POR ESTADO ---
        if not df_estado.empty:
            with st.expander("### 📊 Estatísticas Detalhadas por Estados", expanded=False):
                # Agrupamento correto por estado
                tabela_est = df_estado.groupby('state')[var_coluna].agg(
                    ['count', 'mean', 'std', 'min', 'max', 'median']
                ).reset_index().sort_values(by='mean', ascending=False)

                st.dataframe(
                    tabela_est,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "state": "Estado",
                        "count": st.column_config.NumberColumn("Nº Registros", format="%d"),
                        "mean": st.column_config.NumberColumn("Média", format="%.2f"),
                        "std": st.column_config.NumberColumn("Desv. Padrão", format="%.2f"),
                        "min": st.column_config.NumberColumn("Mínimo", format="%.2f"),
                        "max": st.column_config.NumberColumn("Máximo", format="%.2f"),
                        "median": st.column_config.NumberColumn("Mediana", format="%.2f")
                    }
                )

        st.markdown("---")
        
        # Destaque Individual
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
                df_line_dest = df_destaque.groupby('Data_Dia')[var_coluna].mean().reset_index()
                
                fig_dest = px.line(
                    df_line_dest, 
                    x="Data_Dia", 
                    y=var_coluna, 
                    markers=True,
                    title=f"Evolução Isolada: {estado_destaque}"
                )
                fig_dest.update_traces(line_color='#FF4B4B', line_width=3) 
                
                # Aplica config padrão
                fig_dest.update_layout(
                    xaxis=dict(fixedrange=True, title="Data"),
                    yaxis=dict(fixedrange=True, title=var_label)
                )
                st.plotly_chart(fig_dest, use_container_width=True, theme="streamlit", config=config_padrao)