import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise Descritiva", layout="wide")

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("dataframe/dados_AS.csv")
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        df['Data_Dia'] = df['last_updated'].dt.date
        return df
    except: return None

df = carregar_dados()

paises = sorted(df['country'].unique().astype(str))
paises_filtro = st.sidebar.multiselect("Filtrar País:", paises, default=paises)

# Aplica o filtro
if paises_filtro:
    df_filtered = df[df['country'].isin(paises_filtro)]
else:
    df_filtered = df

# Deixando os nomes mais bonitos no seletor
cols_numericas = {
    'Vento (km/h)': 'wind_kph',
    'Pressão (in)': 'pressure_in', 
    'Precipitação (mm)': 'precip_mm', 
    'Umidade (%)': 'humidity', 
    'Cobertura de Nuvens (%)': 'cloud',
    'Índice UV': 'uv_index',
    'Sensação Térmica (C)': 'feels_like_celsius'
}

variavel_analise = st.selectbox(
    "Escolha a variável para análise",
    options=cols_numericas,
    index=0
)

if variavel_analise:
    tabela_final = df.groupby(variavel_analise).agg(
        ['count', 'mean', 'std', 'min', 'max', 'median']
    ).reset_index()
    tabela_final = tabela_final.sort_values(by='mean', ascending=False)

    st.dataframe(
        tabela_final,
        use_container_width=True,
        hide_index=True, # Esconde o índice numérico padrão do Pandas
        column_config={
            variavel_analise: st.column_config.TextColumn(
                "Categoria",
                width="medium"
            ),
            "count": st.column_config.NumberColumn(
                "Tamanho",
                format="%d",
                help="Número de registros"
            ),
            "mean": st.column_config.NumberColumn(
                "Média",
                format="%.2f",
                help="Média Aritmética"
            ),
            "std": st.column_config.NumberColumn(
                "Desvio Padrão",
                format="%.2f",
                help="Medida de dispersão"
            ),
            "min": st.column_config.NumberColumn(
                "Mínimo",
                format="%.2f"
            ),
            "max": st.column_config.NumberColumn(
                "Máximo",
                format="%.2f"
            ),
            "median": st.column_config.NumberColumn(
                "Mediana",
                format="%.2f"
            )
        }
    )

# col_sel1, col_sel2 = st.columns([1, 3])
# with col_sel1:
#     var_label = st.selectbox("Escolha a Variável:", list(cols_numericas.keys()))
#     var_coluna = cols_numericas[var_label]

# st.markdown("---")

# # 1. Tabela de Resumo
# st.subheader(f"Estatísticas: {var_label}")
# # Tabela agrupada por País (opcional) ou geral
# if len(paises_filtro) > 1:
#     st.markdown("**Por País:**")
#     stats_pais = df_filtered.groupby('country')[var_coluna].agg(['mean', 'max', 'min', 'std']).reset_index()
#     stats_pais.columns = ['País', 'Média', 'Máxima', 'Mínima', 'Desvio Padrão']
#     st.dataframe(stats_pais.style.format({"Média": "{:.3f}", "Desvio Padrão": "{:.3f}"}), use_container_width=True)
# else:
#     stats = df_filtered[var_coluna].agg(['mean', 'max', 'min', 'std']).to_frame().T
#     stats.columns = ['Média', 'Máxima', 'Mínima', 'Desvio Padrão']
#     st.dataframe(stats.style.format({"Média": "{:.3f}", "Desvio Padrão": "{:.3f}"}), use_container_width=True)

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

pag.run()