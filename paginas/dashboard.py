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
    return df

df = carregar_dados()

# --- CONFIGURAÇÃO AUTOMÁTICA DE CORES (Novo Bloco) ---
# Define a escala base para cada região (Códigos padrão IBGE: N, NE, CO, SE, S)
paletas_pasteis = {
    # NE: 9 tons de Amarelo (Do Creme ao Dourado Suave)
    'NE': [
        "#FFFDE7", "#FFF9C4", "#FFF59D", "#FFF176", "#FFEE58", 
        "#FFEB3B", "#FDD835", "#FBC02D", "#F9A825"
    ],
    
    # N: 7 tons de Verde (Do Menta ao Verde Folha Claro)
    'N':  [
        "#E8F5E9", "#C8E6C9", "#A5D6A7", "#81C784", 
        "#66BB6A", "#58D68D", "#52BE80"
    ],
    
    # SE: 4 tons de Azul (Do Azul Bebê ao Azul Céu)
    'SE': [
        "#E3F2FD", "#BBDEFB", "#90CAF9", "#64B5F6"
    ],
    
    # CO: 4 tons de ROSA (Do Rosa Claro ao Rosa Chiclete)
    # Assumindo "ce" como Centro-Oeste para combinar com a paleta pastel
    'CO': [
        "#FCE4EC", "#F8BBD0", "#F48FB1", "#F06292"
    ],
    
    # S: 3 tons de Lilás/Roxo (Do Lavanda ao Orquídea)
    'S':  [
        "#F3E5F5", "#E1BEE7", "#CE93D8"
    ]
}

# ---------------------------------------------------------
# LÓGICA DE APLICAÇÃO (IGUAL À ANTERIOR)
# ---------------------------------------------------------

cores_regioes = {}
unique_regions = df['region'].unique()

# Cria cor da Região (Pega o tom médio/final da paleta)
for reg in unique_regions:
    lista_cores = paletas_pasteis.get(reg, ["#E0E0E0"])
    cores_regioes[reg] = lista_cores[-1] 

# Cria cor dos Estados
cores_estados = {}

for regiao in unique_regions:
    lista_cores = paletas_pasteis.get(regiao, [])
    # Ordena estados para distribuir o gradiente
    estados_da_regiao = sorted(df[df['region'] == regiao]['state'].unique())
    
    for estado, cor in zip(estados_da_regiao, lista_cores):
        cores_estados[estado] = cor

# --- TÍTULO ---
st.title("Dashboard Climático")

# --- CONFIGURAÇÃO  ---
cols_numericas = {
    'Chuva Média (mm)': 'chuva_media_acumulada',
    'Temperatura Média (C)': 'temperatura_media',
    'Umidade Média (%)': 'umidade_media', 
    'Vento Médio (Km/h)': 'vento_medio_kmh', 
    'Pressão Média (inHg)': 'pressao_media_inHg',
    'Radiação Média (Kj/m²)': 'radiacao_media'
}

var_label = st.selectbox("1. Escolha a Variável:", options=cols_numericas.keys())
var_coluna = cols_numericas[var_label]

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
    df_regiao = df[df['region'].isin([])]

st.markdown("---")

# --- VISUALIZAÇÃO (ABAS) ---
if df_regiao.empty:
    st.warning("⚠️ Nenhuma região selecionada acima.")
else:
    tab_reg, tab_est = st.tabs(["🌍 Visão por Região", "📍 Visão por Estado"])

    # === ABA 1: ANÁLISE POR REGIÃO ===
    with tab_reg:
        st.subheader(f"Análise Regional: {var_label}")
        
        # === Boxplot ===
        st.markdown("**Distribuição (Boxplot)**")
        fig_box_reg = px.box(
            df_regiao, 
            x="region", 
            y=var_coluna, 
            color="region", 
            points="outliers",
            color_discrete_map=cores_regioes # Aplica cor da região
        )
        fig_box_reg.update_layout(
            showlegend=False,
            xaxis=dict(fixedrange=True, title="Regiões"),
            yaxis=dict(fixedrange=True, title=f"{var_label}")
        )
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
            color_discrete_map=cores_regioes # Aplica cor da região
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
            
        # === Boxplot ===
        if not df_estado.empty:
            st.markdown("**Comparativo de Distribuição**")  
            fig_box_est = px.box(
                df_estado, 
                x="state", 
                y=var_coluna, 
                color="state",
                title=f"Distribuição de {var_label} (por Estado)",
                color_discrete_map=cores_estados # Aplica tons dos estados
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
                
                # Pega a cor correta do estado ou usa vermelho padrão
                cor_estado = cores_estados.get(estado_destaque, '#FF4B4B')
                fig_dest.update_traces(line_color=cor_estado, line_width=3)
                
                st.plotly_chart(fig_dest, use_container_width=True)