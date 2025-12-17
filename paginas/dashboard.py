import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Análise Descritiva - Clima Brasil", layout="wide")

# 2. Carregamento de Dados
@st.cache_data
def carregar_dados():
    # Certifique-se que o caminho do arquivo está correto no seu projeto
    df = pd.read_csv("dataframe/clima_brasil_mensal_refinado_2015.csv")
    df['mes'] = pd.to_datetime(df['periodo_ref'])
    df['Data_Dia'] = df['mes'].dt.date
    # Cria coluna de Ano para o filtro
    df['Ano'] = df['mes'].dt.year
    return df

df = carregar_dados()

# --- CONFIGURAÇÃO AUTOMÁTICA DE CORES ---
# Define a escala base para cada região (Códigos padrão IBGE: N, NE, CO, SE, S)
paletas_estados_matte = {
    # NE: 9 tons
    'NE': ["#D4E157", "#FFEE58", "#FDD835", "#FFCA28", "#FFA726", "#FF7043", "#8D6E63", "#FFCC80", "#E6EE9C"],
    # N: 7 tons
    'N':  ["#4DB6AC", "#81C784", "#AED581", "#43A047", "#26A69A", "#558B2F", "#00897B"],
    # SE: 4 tons
    'SE': ["#4FC3F7", "#64B5F6", "#7986CB", "#9575CD"],
    # CO: 4 tons
    'CO': ["#FF8A65", "#F06292", "#BA68C8", "#E57373"],
    # S: 3 tons
    'S':  ["#CE93D8", "#BA68C8", "#9575CD"]
}

# B. PALETA REGIÕES (Tons Pastéis)
paletas_regioes_pastel = {
    'NE': "#FFF59D", 'N':  "#C8E6C9", 'SE': "#BBDEFB", 'CO': "#F8BBD0", 'S':  "#E1BEE7"
}

# ---------------------------------------------------------
# 2. LÓGICA DE APLICAÇÃO (AUTOMÁTICA)
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
    # --- NOVO BLOCO: FILTRO APENAS POR ANO ---
    usar_filtro_ano = st.checkbox("Deseja filtrar o ano?")
    
    # Define valores padrão (todos os dados)
    df_filtrado_tempo = df
    
    if usar_filtro_ano:
        min_ano = int(df['Ano'].min())
        max_ano = int(df['Ano'].max())
        
        # Se só tiver um ano no dataset (ex: só 2015), o slider fica travado nesse ano
        if min_ano == max_ano:
            st.info(f"Dados disponíveis apenas para {min_ano}.")
            ano_inicio, ano_fim = min_ano, max_ano
        else:
            ano_inicio, ano_fim = st.slider(
                "Selecione a faixa de anos:",
                min_value=min_ano,
                max_value=max_ano,
                value=(min_ano, max_ano)
            )
        
        # Aplica o filtro
        df_filtrado_tempo = df[(df['Ano'] >= ano_inicio) & (df['Ano'] <= ano_fim)]

# --- LÓGICA DE FILTRAGEM FINAL (Região + Tempo) ---
if regioes_sel:
    df_regiao = df_filtrado_tempo[df_filtrado_tempo['region'].isin(regioes_sel)]
else:
    df_regiao = df_filtrado_tempo[df_filtrado_tempo['region'].isin([])]

st.markdown("---")

# --- VISUALIZAÇÃO (ABAS) ---
if df_regiao.empty:
    st.warning("⚠️ Nenhuma região selecionada ou sem dados para o período escolhido.")
else:
    tab_reg, tab_est = st.tabs(["🌍 Visão por Região", "📍 Visão por Estado"])

    # === ABA 1: ANÁLISE POR REGIÃO ===
    with tab_reg:
        st.subheader(f"Análise Regional: {var_label}")
        
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

        # === Boxplot ===
        st.markdown("**Distribuição (Boxplot)**")
        fig_box_reg = px.box(
            df_regiao, 
            x="region", 
            y=var_coluna, 
            color="region", 
            points="outliers",
            color_discrete_map=cores_regioes
        )
        fig_box_reg.update_layout(
            showlegend=False,
            xaxis=dict(fixedrange=True, title="Regiões"),
            yaxis=dict(fixedrange=True, title=f"{var_label}")
        )
        fig_box_reg.update_traces(marker_opacity=1)
        st.plotly_chart(fig_box_reg, use_container_width=True)
            
        # === Linhas ===
        st.markdown("**Evolução Temporal (Média das Regiões)**")
        df_line_reg = df_regiao.groupby(['Data_Dia', 'region'])[var_coluna].mean().reset_index()
        fig_line_reg = px.line(
            df_line_reg, 
            x="Data_Dia", 
            y=var_coluna, 
            color="region",
            markers=True,
            color_discrete_map=cores_regioes
        )
        fig_line_reg.update_layout(
            xaxis=dict(fixedrange=True, title="Data"),
            yaxis=dict(fixedrange=True, title=f"{var_label}")
        )
        st.plotly_chart(fig_line_reg, use_container_width=True)

    # === ABA 2: ANÁLISE POR ESTADO ===
    with tab_est:
        st.subheader(f"Análise Estadual: {var_label}")

        # Filtro de Estado
        estados_disponiveis = sorted(df_regiao['state'].unique().astype(str))
        estados_sel = st.multiselect(
            "3. Filtre os Estados (Opcional):", 
            estados_disponiveis, 
            default=estados_disponiveis
        )

        # Cria DF para esta aba
        if estados_sel:
            df_estado = df_regiao[df_regiao['state'].isin(estados_sel)]
        else:
            df_estado = df_regiao

        with st.expander("### 📊 Estatísticas Detalhadas por Estados", expanded=False):
            tabela_est = df_estado.groupby('state')[var_coluna].agg(['count', 'mean', 'std', 'min', 'max', 'median']).reset_index().sort_values(by='mean', ascending=False)
            altura_est = (len(tabela_est) + 1) * 35 + 3

            st.dataframe(
                tabela_est,
                use_container_width=True,
                height=altura_est,
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

        # === Boxplot ===
        if not df_estado.empty:
            st.markdown("**Comparativo de Distribuição**")  
            fig_box_est = px.box(
                df_estado, 
                x="state", 
                y=var_coluna, 
                color="state",
                title=f"Distribuição de {var_label} (por Estado)",
                color_discrete_map=cores_estados
            )
            fig_box_est.update_layout(
                showlegend=False,
                xaxis=dict(fixedrange=True, title="Estados"),
                yaxis=dict(fixedrange=True, title=f"{var_label}")
            )
            st.plotly_chart(fig_box_est, use_container_width=True)
        else:
            st.info("Selecione estados para ver o boxplot.")
        
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
                fig_dest.update_layout(
                    showlegend=False,
                    xaxis=dict(fixedrange=True, title="Data"),
                    yaxis=dict(fixedrange=True, title=f"{var_label}")
                )
                
                cor_estado = cores_estados.get(estado_destaque, '#FF4B4B')
                fig_dest.update_traces(line_color=cor_estado, line_width=3)
                
                st.plotly_chart(fig_dest, use_container_width=True)