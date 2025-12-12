import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- TÍTULO ---
st.header("🇧🇷 Painel Climático: Evolução Histórica (2015-2021)")

# --- 1. CARREGAMENTO E OTIMIZAÇÃO (EM MEMÓRIA) ---
@st.cache_data(ttl=3600, show_spinner="Carregando dados...")
def carregar_dados_completo():
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for caminho in caminhos:
        try:
            # Lê apenas o necessário
            cols = [
                'semana_ref', 'state', 'temperatura_media', 
                'chuva_media_semanal', 'umidade_media', 
                'vento_medio', 'radiacao_media'
            ]
            df = pd.read_csv(caminho, usecols=cols)
            break
        except FileNotFoundError:
            continue
            
    if df is None:
        st.error("❌ Erro: Arquivo CSV não encontrado.")
        st.stop()

    try:
        # --- AQUI ACONTECE A MÁGICA (SIMULA O PARQUET) ---
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        
        # Cria a coluna de Mês/Ano que será usada na animação
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Converte Estado para Categoria (Economiza 90% de memória nesta coluna)
        df['state'] = df['state'].astype('category')
        
        # Reduz a precisão numérica (float64 -> float32) para ficar leve
        cols_num = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio', 'radiacao_media']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], downcast='float')
            
        # Agrupa por Estado e Mês AGORA para não processar depois
        # Isso reduz de ~9000 linhas para ~2000 linhas, perfeito para animação
        df_agrupado = df.groupby(['state', 'Mes_Ano'], observed=True)[cols_num].mean().reset_index()
        
        # Ordena cronologicamente para a animação não pular
        df_agrupado = df_agrupado.sort_values('Mes_Ano')
        
        return df_agrupado
        
    except Exception as e:
        st.error(f"Erro ao tratar dados: {e}")
        st.stop()

# --- 2. CARREGAMENTO DO MAPA ---
@st.cache_data(ttl=3600)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

# Carrega os dados já otimizados
df_historico = carregar_dados_completo()
geojson_brasil = carregar_geojson()

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Configurações")

variaveis = {
    "Temperatura Média (°C)": "temperatura_media",
    "Chuva (mm)": "chuva_media_semanal",
    "Umidade (%)": "umidade_media",
    "Vento (m/s)": "vento_medio",
    "Radiação Solar": "radiacao_media"
}

var_label = st.sidebar.selectbox("Variável:", list(variaveis.keys()))
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

# Calcular limites globais (Min/Max de toda a história)
min_g = df_historico[var_col].min()
max_g = df_historico[var_col].max()

# ==============================================================================
# MAPA ANIMADO COMPLETO (2015-2021)
# ==============================================================================
st.info("Aperte o **Play** abaixo do mapa para ver a evolução completa de Jan/2015 a Abr/2021.")

if not df_historico.empty:
    fig_anim = px.choropleth(
        df_historico,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        
        # AQUI: Removemos o filtro de ano. A animação usa TODOS os meses.
        animation_frame="Mes_Ano", 
        
        color_continuous_scale=escala,
        range_color=[min_g, max_g], # Mantém a cor fiel durante toda a animação
        scope="south america",
        title=f"Evolução Histórica: {var_label}",
        hover_data={var_col:':.1f'}
    )

    # Ajustes de Visualização
    fig_anim.update_geos(fitbounds="locations", visible=False)
    fig_anim.update_layout(
        height=650, # Mapa bem grande
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title=None, 
            orientation="h", 
            y=-0.15,
            thickness=15
        ),
        # Estilo dos botões de play
        updatemenus=[{
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }]
    )

    st.plotly_chart(fig_anim, use_container_width=True)
else:
    st.error("Erro ao processar dados para animação.")
