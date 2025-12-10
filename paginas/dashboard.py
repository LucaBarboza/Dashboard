import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Análise Descritiva", layout="wide")

# 2. Carregamento de Dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dataframe/dados_AS.csv")
    df['last_updated'] = pd.to_datetime(df['last_updated'])
    df['Data_Dia'] = df['last_updated'].dt.date
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
# --- AQUI COMEÇA O NOVO BLOCO ---
# Cabeçalho dinâmico (Geral ou Selecionado)
st.subheader(f"📊 {titulo_resumo}: {var_label}")

# Cálculo das métricas gerais
media_geral = df_filtered[var_coluna].mean()
max_geral = df_filtered[var_coluna].max()
min_geral = df_filtered[var_coluna].min()

# Exibição dos cartões (KPIs)
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Média Geral", value=f"{media_geral:.2f}")
kpi2.metric(label="Maior Valor", value=f"{max_geral:.2f}")
kpi3.metric(label="Menor Valor", value=f"{min_geral:.2f}")

st.markdown("---")

# Agrupamos por PAÍS para ver a média/max/min da variável escolhida
tabela_stats = df_filtered.groupby('country')[var_coluna].agg(
    ['count', 'mean', 'std', 'min', 'max', 'median']
).reset_index()

# Ordenar pela média maior
tabela_stats = tabela_stats.sort_values(by='mean', ascending=False)

# Exibe a tabela com formatação bonita
st.dataframe(
    tabela_stats,
    use_container_width=True,
    hide_index=True,
    column_config={
        "country": st.column_config.TextColumn("País"),
        "count": st.column_config.NumberColumn("Nº Registros", format="%d"),
        "mean": st.column_config.NumberColumn("Média", format="%.2f"),
        "std": st.column_config.NumberColumn("Desv. Padrão", format="%.2f"),
        "min": st.column_config.NumberColumn("Mínimo", format="%.2f"),
        "max": st.column_config.NumberColumn("Máximo", format="%.2f"),
        "median": st.column_config.NumberColumn("Mediana", format="%.2f")
    }
)

# # --- GRÁFICOS ---
# st.markdown("---")
# st.subheader("📈 Visualização Gráfica")

# col1, col2 = st.columns(2)

# with col1:
#     st.markdown("**Distribuição (Histograma)**")
#     # Histograma mostra como os dados se distribuem
#     fig_hist = px.histogram(
#         df_filtered, 
#         x=var_coluna, 
#         color="country", 
#         nbins=30,
#         title=f"Distribuição de {var_label}",
#         opacity=0.7
#     )
#     st.plotly_chart(fig_hist, use_container_width=True)

# with col2:
#     st.markdown("**Comparação (Boxplot)**")
#     # Boxplot é ótimo para ver outliers e dispersão entre países
#     fig_box = px.box(
#         df_filtered, 
#         x="country", 
#         y=var_coluna, 
#         color="country", 
#         title=f"Boxplot de {var_label}"
#     )
#     st.plotly_chart(fig_box, use_container_width=True)

# # Gráfico de Linha (Série Temporal)
# st.markdown("**Evolução no Tempo (Média Diária)**")

# # Agrupamos por Dia e País para o gráfico de linha não ficar "sujo" com muitos pontos
# df_line = df_filtered.groupby(['Data_Dia', 'country'])[var_coluna].mean().reset_index()

# fig_line = px.line(
#     df_line, 
#     x="Data_Dia", 
#     y=var_coluna, 
#     color="country", 
#     markers=True,
#     title=f"Evolução de {var_label} ao longo do tempo"
# )
# st.plotly_chart(fig_line, use_container_width=True)