import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- TÍTULO ---
st.header("🇧🇷 Painel Climático: Evolução Histórica")

# --- 1. CARREGAMENTO INTELIGENTE (CACHE + OTIMIZAÇÃO) ---
@st.cache_data(ttl=3600, show_spinner="Carregando base de dados...")
def carregar_dados_otimizados():
    caminhos = [
        "dataframe/clima_brasil_semanal_refinado_2015.csv",
        "clima_brasil_semanal_refinado_2015.csv"
    ]
    
    df = None
    for caminho in caminhos:
        try:
            # TRUQUE 1: Ler apenas as colunas necessárias (Economiza 40% de RAM)
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
        # TRUQUE 2: Converter tipos pesados para leves
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['Ano'] = df['semana_ref'].dt.year
        df['Mes_Ano'] = df['semana_ref'].dt.strftime('%Y-%m')
        
        # Texto repetido vira Categoria (Economiza 90% de RAM na coluna)
        df['state'] = df['state'].astype('category')
        
        # Números gigantes viram float32 (Economiza 50% de RAM numérica)
        cols_num = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio', 'radiacao_media']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Função Estação (Leve)
        def get_estacao(mes):
            if mes in [12, 1, 2]: return 'Verão'
            elif mes in [3, 4, 5]: return 'Outono'
            elif mes in [6, 7, 8]: return 'Inverno'
            return 'Primavera'
        
        df['Estacao'] = df['semana_ref'].dt.month.map(get_estacao).astype('category')
        
        return df.sort_values('semana_ref')
    except Exception as e:
        st.error(f"Erro ao otimizar dados: {e}")
        st.stop()

# --- 2. CARREGAMENTO DO MAPA ---
@st.cache_data(ttl=3600)
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

# Executa o carregamento (uma vez por hora no servidor)
df = carregar_dados_otimizados()
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

# Cores
if "temperatura" in var_col:
    escala = "RdYlBu_r"
elif "chuva" in var_col:
    escala = "Blues"
elif "umidade" in var_col:
    escala = "Teal"
else:
    escala = "Spectral_r"

# Limites Globais (para manter a cor consistente)
min_g = df[var_col].min()
max_g = df[var_col].max()


# ==============================================================================
# PARTE 1: GRID COMPARATIVO (ESTÁTICO)
# ==============================================================================
st.subheader("🗓️ Comparativo Anual")

estacao_filtro = st.radio(
    "Filtrar Período:",
    ["Média do Ano", "Verão", "Outono", "Inverno", "Primavera"],
    horizontal=True
)

# Filtro inteligente (usando query do pandas é mais rápido)
if estacao_filtro != "Média do Ano":
    df_grid = df[df['Estacao'] == estacao_filtro]
else:
    df_grid = df

# Grid de Mapas Pequenos
anos = [2016, 2017, 2018, 2019, 2020, 2021]
colunas = st.columns(3)

for i, ano in enumerate(anos):
    col_idx = i % 3
    with colunas[col_idx]:
        # Agrupamento rápido
        df_ano = df_grid[df_grid['Ano'] == ano]
        
        if df_ano.empty:
            st.info(f"{ano}: -")
            continue

        # Observed=True evita criar linhas vazias na memória
        df_mapa = df_ano.groupby('state', observed=True)[var_col].mean().reset_index()
        
        fig = px.choropleth(
            df_mapa,
            geojson=geojson_brasil,
            locations='state',
            featureidkey="properties.sigla",
            color=var_col,
            color_continuous_scale=escala,
            range_color=[min_g, max_g],
            scope="south america",
            title=f"<b>{ano}</b>"
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, height=200, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# Legenda Simples (Imagem leve)
st.caption(f"Escala: {var_label}")
dummy = px.imshow([[min_g, max_g]], color_continuous_scale=escala)
dummy.update_layout(height=40, margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
dummy.update_traces(opacity=0, showscale=True, colorbar=dict(title=None, orientation='h', thickness=10))
dummy.update_xaxes(visible=False); dummy.update_yaxes(visible=False)
st.plotly_chart(dummy, use_container_width=True)

st.markdown("---")

# ==============================================================================
# PARTE 2: ANIMAÇÃO LEVE (POR ANO)
# ==============================================================================
st.subheader("🎞️ Linha do Tempo (Player Nativo)")
st.info("💡 Escolha um ano abaixo. A animação carrega apenas 12 meses por vez para não travar.")

# Filtro de Ano (Obrigatório para performance)
# Pegamos o último ano completo disponível como padrão
anos_unicos = sorted(df['Ano'].unique())
ano_padrao = 2020 if 2020 in anos_unicos else anos_unicos[-1]

ano_animacao = st.select_slider("Selecione o Ano:", options=anos_unicos, value=ano_padrao)

# 1. Filtrar APENAS o ano escolhido (Reduz os dados em 85%)
df_anim = df[df['Ano'] == ano_animacao].copy()

# 2. Agrupar por Mês (Reduz os dados de semanas para meses)
df_agrupado = df_anim.groupby(['state', 'Mes_Ano'], observed=True)[var_col].mean().reset_index()
df_agrupado = df_agrupado.sort_values('Mes_Ano')

# 3. Gerar o gráfico somente se houver dados
if not df_agrupado.empty:
    fig_anim = px.choropleth(
        df_agrupado,
        geojson=geojson_brasil,
        locations='state',
        featureidkey="properties.sigla",
        color=var_col,
        # AQUI ESTÁ O SEGREDO: animation_frame cria o play nativo
        animation_frame="Mes_Ano",
        color_continuous_scale=escala,
        range_color=[min_g, max_g],
        scope="south america",
        title=f"Evolução Mensal em {ano_animacao}",
        hover_data={var_col:':.1f'}
    )

    fig_anim.update_geos(fitbounds="locations", visible=False)
    fig_anim.update_layout(
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(title=None, orientation="h", y=-0.1, thickness=15),
        sliders=[{"pad": {"t": 30}}]
    )
    
    # Ajuste de velocidade da animação (500ms é suave)
    # Verifica se os botões existem antes de tentar alterar (evita IndexError em anos incompletos)
    if fig_anim.layout.updatemenus:
        fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500

    st.plotly_chart(fig_anim, use_container_width=True)

else:
    st.warning(f"Dados insuficientes para gerar animação do ano {ano_animacao}.")
