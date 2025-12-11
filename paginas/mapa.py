import streamlit as st
import pandas as pd
import plotly.express as px
import time
import matplotlib.colors as mcolors

# --- CONFIGURAÇÃO INICIAL ---
st.header("🗺️ Mapa Climático Sazonal (Mensal)")

# --- CARREGAMENTO E TRATAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_mapa():
    try:
        df = pd.read_csv("dataframe/dados_AS.csv")
        
        # 1. Filtrar Colômbia dos dados (ela ficará sem valor, logo aparecerá a cor de fundo)
        df = df[df['country'] != 'Colombia']
        
        # 2. Converter data
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        
        # 3. Criar coluna de MÊS (Ano-Mês) para o slider mensal
        df['Mes_Ano'] = df['last_updated'].dt.strftime('%Y-%m')
        
        # 4. Criar coluna de Estação (para o filtro)
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
            
        df['Estacao'] = df['last_updated'].dt.month.apply(get_estacao)
        
        # Ordenar cronologicamente
        df = df.sort_values('last_updated')
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'dataframe/dados_AS.csv' não encontrado.")
        return pd.DataFrame()

df = carregar_dados_mapa()

if df.empty:
    st.stop()

# --- SIDEBAR: CONFIGURAÇÕES ---
st.sidebar.markdown("### ⚙️ Configurações")

# Dicionário de Variáveis
variaveis = {
    "Temperatura (°C)": "temperature_celsius",
    "Precipitação (mm)": "precip_mm",
    "Umidade (%)": "humidity",
    "Vento (km/h)": "wind_kph",
    "Pressão (in)": "pressure_in",
    "Nuvens (%)": "cloud",
    "Sensação Térmica (°C)": "feels_like_celsius",
    "Índice UV": "uv_index"
}

# Cores
cores_mapa = {
    "temperature_celsius": "RdYlBu_r",
    "precip_mm": "Blues",
    "humidity": "Teal",
    "wind_kph": "Viridis",
    "cloud": "Greys",
    "uv_index": "Magma",
    "feels_like_celsius": "RdYlBu_r"
}

var_selecionada = st.sidebar.selectbox("Variável:", options=list(variaveis.keys()))
coluna_dados = variaveis[var_selecionada]
escala_cor = cores_mapa.get(coluna_dados, "Viridis")

# Calcular Min/Max global para fixar a escala de cores (evita piscar na animação)
min_global = df[coluna_dados].min()
max_global = df[coluna_dados].max()

# --- FILTROS DE ESTAÇÃO ---
st.subheader("📅 Filtro de Período")

# Botões de Estação
estacao_filtro = st.radio(
    "Filtrar meses por estação:",
    ["Todas", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

# Aplicar Filtro no DataFrame
if estacao_filtro != "Todas":
    df_filtrado = df[df['Estacao'] == estacao_filtro]
else:
    df_filtrado = df

# Obter lista de meses disponíveis após o filtro
meses_unicos = df_filtrado['Mes_Ano'].unique()
meses_unicos.sort() # Garantir ordem cronológica

if len(meses_unicos) == 0:
    st.warning("Não há dados para esta estação.")
    st.stop()

# --- CONTROLES DE ANIMAÇÃO ---
col_play, col_slider = st.columns([1, 4])

# Estado da sessão
if 'animacao_ativa' not in st.session_state:
    st.session_state.animacao_ativa = False
if 'indice_tempo' not in st.session_state:
    st.session_state.indice_tempo = 0

# Botão Play
with col_play:
    # Espaço para alinhar verticalmente com o slider
    st.write("") 
    st.write("")
    label_botao = "⏹️ Parar" if st.session_state.animacao_ativa else "▶️ Reproduzir"
    if st.button(label_botao, use_container_width=True):
        st.session_state.animacao_ativa = not st.session_state.animacao_ativa

# Lógica do Loop de Animação
if st.session_state.animacao_ativa:
    if st.session_state.indice_tempo < len(meses_unicos) - 1:
        st.session_state.indice_tempo += 1
    else:
        st.session_state.indice_tempo = 0 # Reinicia o loop
    time.sleep(0.7) # Velocidade da animação (mais lenta para mês)
    st.rerun()

# Slider Manual
with col_slider:
    # Garante que o índice não estoure se mudarmos de filtro (ex: de Todos para Verão)
    if st.session_state.indice_tempo >= len(meses_unicos):
        st.session_state.indice_tempo = 0
        
    mes_escolhido = st.select_slider(
        "Linha do Tempo (Mês/Ano)",
        options=meses_unicos,
        value=meses_unicos[st.session_state.indice_tempo],
        key="slider_tempo_mapa"
    )
    # Sincroniza slider manual com o índice interno
    st.session_state.indice_tempo = list(meses_unicos).index(mes_escolhido)

# --- PROCESSAMENTO E PLOTAGEM ---

# 1. Filtrar dados do mês escolhido
df_mes = df[df['Mes_Ano'] == mes_escolhido]

# 2. Agrupar por PAÍS (Média do mês inteiro)
df_mapa = df_mes.groupby('country')[coluna_dados].mean().reset_index()

# 3. Gerar Mapa
if not df_mapa.empty:
    fig = px.choropleth(
        df_mapa,
        locations="country",
        locationmode="country names",
        color=coluna_dados,
        scope="south america",
        color_continuous_scale=escala_cor,
        range_color=[min_global, max_global], # Escala fixa
        title=f"Média: {var_selecionada} em {mes_escolhido} ({estacao_filtro if estacao_filtro != 'Todas' else df_mes['Estacao'].iloc[0]})",
        labels={coluna_dados: var_selecionada}
    )
    
    # --- APLICANDO A COLÔMBIA PRETA ---
    fig.update_geos(
        fitbounds="locations", 
        visible=False,
        showcountries=True, 
        countrycolor="white", # Bordas dos países brancas
        showland=True, 
        landcolor="black",    # <--- AQUI ESTÁ O TRUQUE! O fundo (terra sem dados) vira preto.
        showocean=True,
        oceancolor="#e6f2ff"  # Azulzinho claro para o mar
    )
    
    fig.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0},
        paper_bgcolor="#f9f9f9",
        geo=dict(bgcolor= '#f9f9f9')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 4. Tabela de Apoio (Expander)
    with st.expander("📊 Ver Dados Detalhados deste Mês"):
        st.dataframe(
            df_mapa.sort_values(coluna_dados, ascending=False).style.format({coluna_dados: "{:.2f}"}),
            use_container_width=True
        )

else:
    st.warning(f"Sem dados disponíveis para {mes_escolhido}")
