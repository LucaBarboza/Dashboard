import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- TÍTULO ---
st.header("🗺️ Mapa Climático Sazonal: Comparativo")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados_mapa():
    try:
        df = pd.read_csv("dataframe/dados_AS.csv")
        
        # 1. Filtrar Colômbia
        df = df[df['country'] != 'Colombia']
        
        # 2. Converter data
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        
        # 3. Criar coluna Mês/Ano (Ex: 2024-01)
        df['Mes_Ano'] = df['last_updated'].dt.strftime('%Y-%m')
        
        # 4. Criar coluna Estação
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            else: return 'Primavera'
            
        df['Estacao'] = df['last_updated'].dt.month.apply(get_estacao)
        
        df = df.sort_values('last_updated')
        return df
    except FileNotFoundError:
        st.error("Arquivo CSV não encontrado.")
        return pd.DataFrame()

df = carregar_dados_mapa()

if df.empty:
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Configurações")

variaveis = {
    "Temperatura (°C)": "temperature_celsius",
    "Precipitação (mm)": "precip_mm",
    "Umidade (%)": "humidity",
    "Vento (km/h)": "wind_kph",
    "Pressão (in)": "pressure_in",
    "Nuvens (%)": "cloud"
}

var_selecionada = st.sidebar.selectbox("Variável:", options=list(variaveis.keys()))
coluna_dados = variaveis[var_selecionada]

# Definição de Cores Lógica
if coluna_dados == "temperature_celsius":
    escala_cor = "RdYlBu_r" # Vermelho é quente, Azul é frio
elif coluna_dados == "precip_mm":
    escala_cor = "Blues"    # Azul é chuva
else:
    escala_cor = "Viridis"

# Calcular Min/Max Global para travar a escala de cores
min_global = df[coluna_dados].min()
max_global = df[coluna_dados].max()

# --- 1. MAPA GERAL (COMPARATIVO) ---
st.subheader(f"🌎 Média Geral do Período ({var_selecionada})")

# Média de todo o período por país
df_geral = df.groupby('country')[coluna_dados].mean().reset_index()

fig_geral = px.choropleth(
    df_geral,
    locations="country",
    locationmode="country names",
    color=coluna_dados,
    scope="south america",
    color_continuous_scale=escala_cor,
    range_color=[min_global, max_global], # Trava a escala
    labels={coluna_dados: var_selecionada}
)
# Fundo Preto para Colômbia e bordas brancas
fig_geral.update_geos(
    fitbounds="locations", visible=False, showcountries=True, countrycolor="white",
    showland=True, landcolor="black"
)
fig_geral.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(fig_geral, use_container_width=True)

st.markdown("---")

# --- 2. ANIMAÇÃO NO TEMPO ---
st.subheader(f"📅 Evolução no Tempo: {var_selecionada}")

# Filtro de Estação (Botões)
estacao_filtro = st.radio(
    "Filtrar Estação:",
    ["Todas", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

# Filtra o DataFrame base
if estacao_filtro != "Todas":
    df_filtrado = df[df['Estacao'] == estacao_filtro]
else:
    df_filtrado = df

# Lista de meses disponíveis para o slider
meses_unicos = sorted(df_filtrado['Mes_Ano'].unique())

if len(meses_unicos) == 0:
    st.warning("Sem dados para esta estação.")
    st.stop()

# --- LÓGICA DE CONTROLE DA ANIMAÇÃO ---

# Inicializar estados se não existirem
if 'animacao_ativa' not in st.session_state:
    st.session_state.animacao_ativa = False
if 'idx_mes' not in st.session_state:
    st.session_state.idx_mes = 0

# Se mudou o filtro de estação, reseta o índice para não dar erro
if st.session_state.idx_mes >= len(meses_unicos):
    st.session_state.idx_mes = 0

col_btn, col_sli = st.columns([1, 4])

with col_btn:
    st.write("") # Espaçamento
    st.write("")
    label_botao = "⏹️ Parar" if st.session_state.animacao_ativa else "▶️ Iniciar Animação"
    if st.button(label_botao, use_container_width=True):
        st.session_state.animacao_ativa = not st.session_state.animacao_ativa

# Lógica do Loop (Só roda se estiver ativo)
if st.session_state.animacao_ativa:
    if st.session_state.idx_mes < len(meses_unicos) - 1:
        st.session_state.idx_mes += 1
    else:
        st.session_state.idx_mes = 0 # Volta pro começo
    time.sleep(0.8) # Velocidade
    st.rerun() # Recarrega a página para atualizar o slider visualmente

with col_sli:
    # O Slider agora recebe o valor do session_state
    mes_selecionado = st.select_slider(
        "Linha do Tempo",
        options=meses_unicos,
        value=meses_unicos[st.session_state.idx_mes] # <--- ISSO FAZ ELE MEXER SOZINHO
    )
    # Se o usuário mexer manualmente, atualizamos o estado interno
    st.session_state.idx_mes = list(meses_unicos).index(mes_selecionado)

# --- PLOT DO MAPA MENSAL ---
# 1. Filtra dados do mês
df_mes = df[df['Mes_Ano'] == mes_selecionado]

# 2. Agrupa por país
df_mapa = df_mes.groupby('country')[coluna_dados].mean().reset_index()

if not df_mapa.empty:
    fig_anim = px.choropleth(
        df_mapa,
        locations="country",
        locationmode="country names",
        color=coluna_dados,
        scope="south america",
        color_continuous_scale=escala_cor,
        range_color=[min_global, max_global], # Escala travada igual ao Geral
        title=f"Média em: {mes_selecionado} ({df_mes['Estacao'].iloc[0]})",
        labels={coluna_dados: var_selecionada}
    )
    
    # Colômbia Preta e Visual Limpo
    fig_anim.update_geos(
        fitbounds="locations", visible=False, showcountries=True, countrycolor="white",
        showland=True, landcolor="black"
    )
    fig_anim.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    
    st.plotly_chart(fig_anim, use_container_width=True)

    # Dados numéricos
    with st.expander("Ver tabela de dados deste mês"):
        st.dataframe(df_mapa.style.format({coluna_dados: "{:.2f}"}), use_container_width=True)

else:
    st.warning(f"Sem dados para {mes_selecionado}")
