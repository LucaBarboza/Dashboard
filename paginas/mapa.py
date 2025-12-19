import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import gc # Garbage Collector para limpar memória na marra

# --- 1. CONFIGURAÇÃO OTIMIZADA ---
st.set_page_config(page_title="Monitor Climático", layout="wide")

# Limpeza de memória forçada no início
gc.collect()

# --- 2. CARREGAMENTO COM MEMÓRIA REDUZIDA ---
@st.cache_data(ttl=3600)
def carregar_dados_otimizados():
    try:
        # Tenta carregar
        try:
            df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
        except:
            df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
            
        # OTIMIZAÇÃO DE MEMÓRIA: Converter tipos pesados
        cols_numericas = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio', 'radiacao_media']
        for col in cols_numericas:
            if col in df.columns:
                # float32 usa METADE da memória do float64 padrão
                df[col] = pd.to_numeric(df[col], downcast='float')

        # Datas
        if 'semana_ref' in df.columns:
            df['semana_ref'] = pd.to_datetime(df['semana_ref'])
            df['ano'] = df['semana_ref'].dt.year
            df['mes'] = df['semana_ref'].dt.month
            # Converter string para category economiza memória se houver muitas repetições
            df['ano_mes'] = df['semana_ref'].dt.strftime('%Y-%m').astype('category')
            
            def get_estacao(m):
                if m in [12, 1, 2]: return "Verão"
                elif m in [3, 4, 5]: return "Outono"
                elif m in [6, 7, 8]: return "Inverno"
                else: return "Primavera"
            df['estacao'] = df['mes'].apply(get_estacao).astype('category')
            df['state'] = df['state'].astype('category') # Otimização crítica
            
        return df
    except Exception as e:
        st.error(f"Erro dados: {e}")
        st.stop()

# Cache Resource é melhor para arquivos estáticos grandes como GeoJSON
@st.cache_resource(ttl=3600) 
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200: return r.json()
    except: pass
    return None

df = carregar_dados_otimizados()
geojson = carregar_geojson()

if df is None or geojson is None:
    st.warning("Dados não carregados.")
    st.stop()

# --- 3. ESCALAS (Calculadas uma vez) ---
global_ranges = {
    "temperatura_media": [df['temperatura_media'].min(), df['temperatura_media'].max()],
    "chuva_media_semanal": [df['chuva_media_semanal'].min(), df['chuva_media_semanal'].max()],
    "umidade_media": [df['umidade_media'].min(), df['umidade_media'].max()],
    "vento_medio": [df['vento_medio'].min(), df['vento_medio'].max()],
    "radiacao_media": [df['radiacao_media'].min(), df['radiacao_media'].max()]
}

# --- 4. SIDEBAR ---
st.sidebar.header("⚙️ Filtros")
variaveis = {
    "Temperatura (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}
var_label = st.sidebar.selectbox("Variável:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Cores
if "chuva" in var_col: escala = "Blues"
elif "temperatura" in var_col: escala = "RdYlBu_r"
elif "umidade" in var_col: escala = "YlGnBu"
else: escala = "Viridis"

# --- 5. VISUALIZAÇÃO LEVE ---
st.title("🌍 Monitor Climático (Modo Leve)")
st.caption("Use os sliders abaixo para navegar no tempo. Otimizado para não travar.")

tab1, tab2 = st.tabs(["🍂 Por Estação (Anual)", "⏳ Mensal (Detalhado)"])

# === ABA 1: ANUAL (SEM ANIMAÇÃO AUTOMÁTICA) ===
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        estacao = st.radio("Estação:", ["Verão", "Outono", "Inverno", "Primavera"])
    with c2:
        # Slider manual substitui o botão Play
        anos_disponiveis = sorted(df['ano'].unique())
        ano_sel = st.select_slider("Selecione o Ano:", options=anos_disponiveis, value=anos_disponiveis[-1])
    
    # Filtra APENAS O NECESSÁRIO para este momento
    df_filtrado = df[(df['estacao'] == estacao) & (df['ano'] == ano_sel)]
    # Agrupa
    df_mapa1 = df_filtrado.groupby('state')[var_col].mean().reset_index()
    
    # Plota
    fig1 = px.choropleth_mapbox(
        df_mapa1, geojson=geojson, locations='state', featureidkey="properties.sigla",
        color=var_col, 
        color_continuous_scale=escala, range_color=global_ranges[var_col],
        mapbox_style="carto-positron", zoom=3, center={"lat": -15, "lon": -54}, opacity=0.9, height=500
    )
    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, dragmode=False)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Limpa variável temporária
    del df_filtrado, df_mapa1

# === ABA 2: MENSAL (SEM ANIMAÇÃO AUTOMÁTICA) ===
with tab2:
    lista_meses = sorted(df['ano_mes'].unique())
    # Slider manual
    mes_sel = st.select_slider("Linha do Tempo (Mês/Ano):", options=lista_meses, value=lista_meses[-1])
    
    # Filtragem pontual
    df_mes = df[df['ano_mes'] == mes_sel].groupby('state')[var_col].mean().reset_index()
    
    fig2 = px.choropleth_mapbox(
        df_mes, geojson=geojson, locations='state', featureidkey="properties.sigla",
        color=var_col, 
        color_continuous_scale=escala, range_color=global_ranges[var_col],
        mapbox_style="carto-positron", zoom=3, center={"lat": -15, "lon": -54}, opacity=0.9, height=500
    )
    fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, dragmode=False)
    st.plotly_chart(fig2, use_container_width=True)

    # Limpa variável temporária
    del df_mes

# Força limpeza final de RAM
gc.collect()