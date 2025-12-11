import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Análise Descritiva", layout="wide")

# 2. Carregamento de Dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dataframe/dados_AS2_mensal.csv")
    df['mes'] = pd.to_datetime(df['mes'])
    df['Data_Dia'] = df['mes'].dt.date
    return df

df = carregar_dados()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")

# Filtro de País
paises = sorted(df['country'].unique().astype(str))
paises_filtro = st.sidebar.multiselect("Selecione os Países:", paises, default=paises)

# Aplica o filtro no DataFrame
# Lógica: Se a lista estiver vazia, pega o DF inteiro (Geralzão)
if paises_filtro:
    df_filtered = df[df['country'].isin(paises_filtro)]
    titulo_resumo = "Resumo dos Países Selecionados"
else:
    df_filtered = df
    titulo_resumo = "Resumo GERAL (Todos os Países)"

# --- SELEÇÃO DE VARIÁVEL ---
cols_numericas = {
    'Vento (km/h)': 'wind_kph',
    'Pressão (in)': 'pressure_in', 
    'Precipitação (mm)': 'precip_mm', 
    'Umidade (%)': 'humidity', 
    'Cobertura de Nuvens (%)': 'cloud',
    'Índice UV': 'uv_index',
    'Sensação Térmica (C)': 'feels_like_celsius'
}

st.subheader("Configuração da Análise")

# O usuário escolhe a variável
var_label = st.selectbox(
    "Escolha a variável para analisar:",
    options=list(cols_numericas.keys()),
    index=0
)

var_coluna = cols_numericas[var_label]

st.markdown("---")

# --- ANÁLISE ESTATÍSTICA (Tabela) ---
if not paises_filtro:
    # CENÁRIO 1: NENHUM PAÍS SELECIONADO -> MOSTRAR APENAS NÚMEROS
    st.subheader(f"🌍 Visão Geral: {var_label}")
    
    # Criamos o DataFrame SEM a coluna 'country', apenas com os valores
    tabela_final = pd.DataFrame({
        'count': [df[var_coluna].count()],
        'mean': [df[var_coluna].mean()],
        'std': [df[var_coluna].std()],
        'min': [df[var_coluna].min()],
        'max': [df[var_coluna].max()],
        'median': [df[var_coluna].median()]
    })

else:
    # CENÁRIO 2: PAÍSES SELECIONADOS -> MOSTRAR NOMES DOS PAÍSES
    st.subheader(f"📍 Detalhamento por País: {var_label}")
    
    df_filtered = df[df['country'].isin(paises_filtro)]
    
    # Aqui mantemos a coluna 'country' (que vira index no groupby)
    tabela_final = df_filtered.groupby('country')[var_coluna].agg(
        ['count', 'mean', 'std', 'min', 'max', 'median']
    ).reset_index()
    
    tabela_final = tabela_final.sort_values(by='mean', ascending=False)

# EXIBIÇÃO DA TABELA
# O Streamlit é inteligente: se a coluna "country" não existir (Cenário 1),
# ele ignora a configuração dela e mostra só os números.
st.dataframe(
    tabela_final,
    use_container_width=True,
    hide_index=True,
    column_config={
        "country": st.column_config.TextColumn("Referência", width="large"),
        "count": st.column_config.NumberColumn("Nº Registros", format="%d"),
        "mean": st.column_config.NumberColumn("Média", format="%.2f"),
        "std": st.column_config.NumberColumn("Desv. Padrão", format="%.2f"),
        "min": st.column_config.NumberColumn("Mínimo", format="%.2f"),
        "max": st.column_config.NumberColumn("Máximo", format="%.2f"),
        "median": st.column_config.NumberColumn("Mediana", format="%.2f")
    }
)

# --- GRÁFICOS ---
st.markdown("---")
st.subheader("📈 Visualização Gráfica")

# Define configurações dinâmicas baseadas no filtro
if not paises_filtro:
    # MODO GERAL: Gráficos únicos (sem separar por cores de países)
    cor_grafico = None           # Uma cor só para tudo
    eixo_x_box = None            # Um boxplot único
    colunas_agrupamento = ['Data_Dia'] # Agrupa só por data (média mundial)
    sulfixo_titulo = " (Visão Global)"
else:
    # MODO DETALHADO: Separa por cores dos países
    cor_grafico = "country"
    eixo_x_box = "country"
    colunas_agrupamento = ['Data_Dia', 'country'] # Mantém a separação
    sulfixo_titulo = " (por País)"

# col1, col2 = st.columns(2)

# with col1:
#     st.markdown("**Distribuição (Histograma)**")
#     fig_hist = px.histogram(
#         df_filtered, 
#         x=var_coluna, 
#         color=cor_grafico, # Muda dinamicamente
#         nbins=30,
#         title=f"Distribuição de {var_label}{sulfixo_titulo}",
#         opacity=0.7
#     )
#     # Se for geral, remove a legenda automática que pode ficar poluída
#     if not paises_filtro:
#         fig_hist.update_layout(showlegend=False)
        
#     st.plotly_chart(fig_hist, use_container_width=True)

# with col2:
st.markdown("**Comparação (Boxplot)**")
fig_box = px.box(
    df_filtered, 
    x=eixo_x_box,   # Se for geral, remove o eixo X (fica um box só)
    y=var_coluna, 
    color=cor_grafico, 
    title=f"Boxplot de {var_label}{sulfixo_titulo}"
)
if not paises_filtro:
    fig_box.update_layout(showlegend=False, xaxis_title="Global")
    
st.plotly_chart(fig_box, use_container_width=True)

# Gráfico de Linha (Série Temporal)
st.markdown("**Evolução no Tempo (Média Diária)**")

# Agrupamento dinâmico (Geral ou por País)
df_line = df_filtered.groupby(colunas_agrupamento)[var_coluna].mean().reset_index()

fig_line = px.line(
    df_line, 
    x="Data_Dia", 
    y=var_coluna, 
    color=cor_grafico, # Se for None, desenha uma linha única
    markers=True,
    title=f"Evolução de {var_label}{sulfixo_titulo}"
)
st.plotly_chart(fig_line, use_container_width=True)