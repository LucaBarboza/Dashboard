import streamlit as st
import pandas as pd
import requests
import folium
from folium.plugins import TimeSliderChoropleth
from streamlit_folium import st_folium
import branca.colormap as cm

# --- TÍTULO ---
st.header("🇧🇷 Evolução Climática: TimeSlider (Alta Performance)")
st.info("Este mapa processa todos os dados de uma vez. A animação roda direto no seu navegador sem travar.")

# --- 1. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados():
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    df = None
    for c in caminhos:
        try:
            df = pd.read_csv(c)
            break
        except: continue
        
    if df is None:
        st.error("Erro: CSV não encontrado.")
        st.stop()
        
    df['semana_ref'] = pd.to_datetime(df['semana_ref'])
    df['timestamp'] = df['semana_ref'].astype(int) // 10**9
    df['timestamp'] = df['timestamp'].astype(str)
    
    return df.sort_values('semana_ref')

@st.cache_data(ttl=3600)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        return requests.get(url).json()
    except Exception as e:
        st.error(f"Erro ao baixar GeoJSON: {e}")
        st.stop()

df = carregar_dados()
geojson = carregar_geojson()

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Variável")
variaveis = {
    "Temperatura (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação": "radiacao_media"
}
var_label = st.sidebar.selectbox("Escolha o indicador:", list(variaveis.keys()))
var_col = variaveis[var_label]

# Definição das cores
if "temperatura" in var_col:
    colors = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
elif "chuva" in var_col:
    colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b']
else:
    colors = ['#ffffe5', '#f7fcb9', '#addd8e', '#41ab5d', '#238443', '#005a32']

# --- PREPARAÇÃO DO DICIONÁRIO DE ESTILOS ---
# Em paginas/mapa.py

@st.cache_data(show_spinner="Renderizando mapa temporal...")
def gerar_mapa_timeslider(df_data, coluna, _geojson, lista_cores):
    
    # 1. Proteção: Verifica se a coluna existe
    if coluna not in df_data.columns:
        st.error(f"Coluna '{coluna}' não encontrada no DataFrame.")
        return None, None
        
    # 2. Proteção: Pega apenas números válidos (ignora vazios/NaN) para calcular a escala
    dados_validos = df_data[coluna].dropna()
    
    if dados_validos.empty:
        st.warning(f"A variável selecionada não contém dados válidos para exibição.")
        return None, None

    min_val = float(dados_validos.min())
    max_val = float(dados_validos.max())
    
    # 3. Proteção CRÍTICA: Evita o erro "Thresholds not sorted"
    # Se min == max (ex: todos os valores são 25.0), o mapa quebra.
    # Adicionamos uma fração minúscula ao max para criar um intervalo artificial.
    if min_val >= max_val:
        max_val = min_val + 0.0001
    
    # Cria a escala de cores
    colormap = cm.LinearColormap(
        colors=lista_cores,
        vmin=min_val,
        vmax=max_val,
        caption=var_label
    )

    # 4. Construir o dicionário de estilos
    styledict = {}
    
    for feature in _geojson['features']:
        sigla = feature['properties']['sigla']
        styledict[sigla] = {}
        
        # Filtra o dataframe original (pode conter NaNs, então usamos fillna ou try/except)
        df_estado = df_data[df_data['state'] == sigla]
        
        for _, row in df_estado.iterrows():
            # Se o valor for nulo, pulamos ou pintamos de cinza (aqui pulamos)
            if pd.isna(row[coluna]):
                continue
                
            valor = row[coluna]
            timestamp = row['timestamp']
            
            cor_hex = colormap(valor)
            
            styledict[sigla][timestamp] = {
                'color': cor_hex,
                'opacity': 0.8
            }
    
    return styledict, colormap
