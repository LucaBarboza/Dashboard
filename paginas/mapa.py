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
        
    # Converter data e criar timestamp (segundos) para o plugin do mapa
    df['semana_ref'] = pd.to_datetime(df['semana_ref'])
    # O TimeSlider precisa da data em "Unix Timestamp" (segundos desde 1970) convertida para string
    df['timestamp'] = df['semana_ref'].astype(int) // 10**9
    df['timestamp'] = df['timestamp'].astype(str)
    
    return df.sort_values('semana_ref')

@st.cache_data(ttl=3600)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

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

# Definição das cores (Branca Colormap)
if "temperatura" in var_col:
    # Azul -> Amarelo -> Vermelho
    colors = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
elif "chuva" in var_col:
    # Branco -> Azul Escuro
    colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b']
else:
    colors = ['#ffffe5', '#f7fcb9', '#addd8e', '#41ab5d', '#238443', '#005a32']

# --- PREPARAÇÃO DO DICIONÁRIO DE ESTILOS (A Mágica do Folium) ---
# O plugin exige um dicionário no formato: { 'ID_DO_ESTADO': { 'TIMESTAMP': {'color': '#HEX', 'opacity': 0.7} } }

@st.cache_data(show_spinner="Renderizando mapa temporal...")
def gerar_mapa_timeslider(df_data, coluna, _geojson, lista_cores):
    
    # 1. Criar a escala de cores baseada nos dados (Min/Max global)
    min_val = df_data[coluna].min()
    max_val = df_data[coluna].max()
    
    colormap = cm.LinearColormap(
        colors=lista_cores,
        vmin=min_val,
        vmax=max_val,
        caption=var_label
    )

    # 2. Construir o dicionário de estilos (styledict)
    # Isso mapeia: Para o estado "SP", na data "123456789", a cor é "#FF0000"
    styledict = {}
    
    # Iterar por cada estado presente no GeoJSON
    for feature in _geojson['features']:
        sigla = feature['properties']['sigla'] # Ex: "AC", "SP"
        styledict[sigla] = {}
        
        # Filtrar dados desse estado
        df_estado = df_data[df_data['state'] == sigla]
        
        for _, row in df_estado.iterrows():
            valor = row[coluna]
            timestamp = row['timestamp']
            
            # Pega a cor hexadecimal correspondente ao valor
            cor_hex = colormap(valor)
            
            styledict[sigla][timestamp] = {
                'color': cor_hex,
                'opacity': 0.8
            }
    
    return styledict, colormap

# Gerar dados do mapa
try:
    style_dict, colormap = gerar_mapa_timeslider(df, var_col, geojson, colors)

    # --- CRIAÇÃO DO MAPA FOLIUM ---
    m = folium.Map(
        location=[-14.235, -51.925], # Centro do Brasil
        zoom_start=4,
        tiles="cartodbpositron" # Estilo de mapa leve e limpo
    )

    # Adicionar o plugin de tempo
    # Note: feature_id_key deve apontar para onde está a sigla no GeoJSON (properties.sigla)
    TimeSliderChoropleth(
        data=geojson,
        styledict=style_dict,
        name="Evolução Temporal",
        overlay=True,
        control=True,
        show=True
    ).add_to(m)

    # Adicionar a legenda de cores no mapa
    colormap.add_to(m)

    # Exibir no Streamlit
    st_folium(m, width="100%", height=600)

except Exception as e:
    st.error(f"Erro ao gerar visualização: {e}")
    st.info("Dica: Verifique se as siglas dos estados no CSV (coluna 'state') batem com as do GeoJSON (AC, SP, etc).")
