import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(layout="wide") # Descomente se rodar isolado

st.header("🇧🇷 Painel Climático: Comparativo & Evolução")

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
@st.cache_data
def carregar_dados():
    # Tenta carregar o arquivo
    try:
        # Ajuste o caminho conforme necessário
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Criar colunas de tempo
        df['Ano'] = df['semana_ref'].dt.year
        # Formatamos Mês_Ano como string ordenável (YYYY-MM) para a animação seguir a ordem correta
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Definir Estações
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.apply(get_estacao)
        
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

df = carregar_dados()
geojson_brasil = carregar_geojson()

if df.empty:
    st.stop()

# --- SIDEBAR: VARIÁVEIS ---
st.sidebar.markdown("### ⚙️ Configurações")

variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação Solar": "radiacao_media"
}

var_label = st.sidebar.selectbox("Escolha a Variável:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Definição de Cores
if "temperatura" in var_col:
    escala = "RdYlBu_r"
elif "chuva" in var_col:
    escala = "Blues"
elif "umidade" in var_col:
    escala = "Teal"
else:
    escala = "Spectral_r"

# Calcular Min/Max Global (Crucial para as cores não piscarem)
min_global = df[var_col].min()
max_global = df[var_col].max()


# ==============================================================================
# SEÇÃO 1: GRID COMPARATIVO (ESTÁTICO)
# ==============================================================================
st.markdown("### 🗓️ Comparativo Anual (2016 - 2021)")

estacao_selecionada = st.radio(
    "Filtrar Período (Mapas Estáticos):",
    ["Média do Ano", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

df_grid = df.copy()
if estacao_selecionada != "Média do Ano":
    df_grid = df_grid[df_grid['Estacao'] == estacao_selecionada]

anos_grid = [2016, 2017, 2018, 2019, 2020, 2021]
row1 = st.columns(3)
row2 = st.columns(3)
colunas_grid = row1 + row2

for i, ano in enumerate(anos_grid):
    with colunas_grid[i]:
        df_ano = df_grid[df_grid['Ano'] == ano]
        df_mapa_ano = df_ano.groupby('state')[var_col].mean().reset_index()
        
        if not df_mapa_ano.empty:
            fig = px.choropleth(
                df_mapa_ano,
                geojson=geojson_brasil,
                locations='state',
                featureidkey="properties.sigla",
                color=var_col,
                color_continuous_scale=escala,
                range_color=[min_global, max_global],
                scope="south america",
                title=f"<b>{ano}</b>"
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                margin={"r":0,"t":30,"l":0,"b":0},
                coloraxis_showscale=False,
                height=200
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Sem dados ({ano})")

# Barra de cores auxiliar
st.caption(f"Legenda: {var_label}")
dummy_fig = px.imshow([[min_global, max_global]], color_continuous_scale=escala)
dummy_fig.update_traces(opacity=0)
dummy_fig.update_xaxes(visible=False)
dummy_fig.update_yaxes(visible=False)
dummy_fig.update_layout(height=50, margin={"r":10,"t":0,"l":10,"b":0}, coloraxis_showscale=False)
dummy_fig.update_traces(showscale=True, colorbar=dict(title=None, orientation='h', thickness=15, y=0.5))
st.plotly_chart(dummy_fig, use_container_width=True)


st.markdown("---")


# ==============================================================================
# SEÇÃO 2: MAPA ANIMADO (OTIMIZADO / SEM LAG)
# ==============================================================================
st.markdown("### 🎞️ Evolução Histórica (Player Nativo)")
st.info("💡 Use o botão 'Play' no canto inferior esquerdo do mapa para iniciar a animação suave.")

# 1. Preparar os dados agregados para animação
# Agrupamos por Estado e Mês de uma vez só
df_animacao = df.groupby(['state', 'Mes_Ano'])[var_col].mean().reset_index()

# Ordenar por data para a animação seguir a linha do tempo correta
df_animacao = df_animacao.sort_values('Mes_Ano')

# 2. Criar o gráfico com animation_frame
# O segredo está aqui: passamos TODOS os dados para o Plotly e dizemos
# "Use a coluna Mes_Ano para criar os quadros da animação"
fig_animada = px.choropleth(
    df_animacao,
    geojson=geojson_brasil,
    locations='state',
    featureidkey="properties.sigla",
    color=var_col,
    animation_frame="Mes_Ano", # <--- CRIA A BARRA DE TEMPO AUTOMÁTICA
    color_continuous_scale=escala,
    range_color=[min_global, max_global], # Fixa a escala
    scope="south america",
    title=f"Evolução Temporal: {var_label}",
    hover_data={var_col:':.2f'}
)

# 3. Ajustes de Performance e Estética
fig_animada.update_geos(
    fitbounds="locations", 
    visible=False
)
fig_animada.update_layout(
    height=700, # Mapa grande
    margin={"r":0,"t":50,"l":0,"b":0},
    # Ajustar a velocidade da animação
    updatemenus=[{
        "type": "buttons",
        "showactive": False,
        "buttons": [{
            "label": "Play",
            "method": "animate",
            "args": [None, {"frame": {"duration": 400, "redraw": True}, "fromcurrent": True}] 
            # duration 400ms = um pouco mais rápido que meio segundo por mês
        }]
    }]
)

# Posicionar a barra de tempo (slider)
fig_animada["layout"]["sliders"][0]["pad"] = {"t": 20} 

st.plotly_chart(fig_animada, use_container_width=True)
