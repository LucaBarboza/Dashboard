import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

st.header("🤖 Inteligência Artificial e Modelagem")
st.markdown("Utilizando algoritmos Supervisionados (Previsão) e Não Supervisionados (Descoberta de Padrões).")

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados_ml():
    try:
        df = pd.read_csv("dataframe/clima_brasil_semanal_refinado_2015.csv")
    except:
        df = pd.read_csv("clima_brasil_semanal_refinado_2015.csv")
        
    if 'semana_ref' in df.columns:
        df['semana_ref'] = pd.to_datetime(df['semana_ref'])
        df['ano'] = df['semana_ref'].dt.year
        df['mes'] = df['semana_ref'].dt.month
        df['tempo_ordinal'] = df['semana_ref'].apply(lambda x: x.toordinal())
    
    cols_numericas = ['chuva_media_semanal', 'temperatura_media', 'umidade_media', 
                      'vento_medio', 'pressao_media', 'radiacao_media']
    # Remove NaNs
    df = df.dropna(subset=cols_numericas)
    
    # Mapeamento de nomes
    mapa = {c: c.replace('_media', '').replace('_medio', '').replace('_semanal', '').capitalize() for c in cols_numericas}
    
    return df, mapa

# Carrega GeoJSON para o mapa de clusters (reaproveitando a função se possível, ou simplificando)
@st.cache_data
def carregar_geojson_ml():
    import requests
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

df, mapa_nomes = carregar_dados_ml()
geojson = carregar_geojson_ml()

# --- ABAS DA PÁGINA ---
tab1, tab2, tab3 = st.tabs([
    "🔍 Clustering (Novas Regiões)", 
    "🚨 Detecção de Anomalias", 
    "🔮 Previsão (Séries Temporais)"
])

# ==============================================================================
# TAB 1: CLUSTERING (K-MEANS)
# ==============================================================================
with tab1:
    st.subheader("Redefinindo o Brasil Climático")
    st.markdown("""
    A IA utiliza o algoritmo **K-Means** para agrupar estados com comportamentos climáticos semelhantes, 
    ignorando as fronteiras geográficas oficiais.
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        n_clusters = st.slider("Número de Grupos (Clusters):", 2, 8, 4)
        features_cluster = st.multiselect(
            "Variáveis para Agrupar:", 
            list(mapa_nomes.keys()),
            default=['temperatura_media', 'chuva_media_semanal', 'umidade_media'],
            format_func=lambda x: mapa_nomes[x]
        )
        btn_cluster = st.button("Rodar K-Means")
        
    if btn_cluster:
        # 1. Preparar dados (Agrupando média histórica por estado)
        df_estado = df.groupby('state')[features_cluster].mean().reset_index()
        
        # 2. Normalizar (Importante para o K-Means não dar peso errado)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_estado[features_cluster])
        
        # 3. Rodar IA
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_estado['Cluster'] = kmeans.fit_predict(X_scaled)
        df_estado['Cluster'] = df_estado['Cluster'].astype(str) # Para virar categoria no mapa
        
        # 4. Mapa
        with col2:
            if geojson:
                fig_map = px.choropleth_mapbox(
                    df_estado,
                    geojson=geojson,
                    locations='state',
                    featureidkey="properties.sigla",
                    color='Cluster',
                    mapbox_style="carto-positron",
                    zoom=3, center={"lat": -15.7, "lon": -52},
                    title="Grupos Climáticos Identificados pela IA",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Mapa não carregou, mostrando tabela.")
        
        st.markdown("#### Características de cada Grupo")
        # Mostra a média das variáveis para cada cluster para interpretar
        resumo_clusters = df_estado.groupby('Cluster')[features_cluster].mean().reset_index()
        # Formatação bonita
        st.dataframe(resumo_clusters.style.background_gradient(cmap='Blues'), use_container_width=True)
        st.caption("Nota: O K-Means agrupa estados matematicamente 'próximos'. Veja como ele pode juntar estados do Norte com partes do Nordeste, por exemplo.")

# ==============================================================================
# TAB 2: DETECÇÃO DE ANOMALIAS (ISOLATION FOREST)
# ==============================================================================
with tab2:
    st.subheader("Caçador de Extremos Climáticos")
    st.markdown("""
    O algoritmo **Isolation Forest** analisa todo o histórico para encontrar semanas 'bizarras' 
    (outliers) que fogem completamente do padrão normal.
    """)
    
    col_ano_a, col_ano_b = st.columns(2)
    contamination = col_ano_a.slider("Sensibilidade (% de Anomalias):", 1, 10, 2) / 100
    estado_anomalia = col_ano_b.selectbox("Filtrar Estado:", df['state'].unique())
    
    if st.button("Detectar Anomalias"):
        df_iso = df[df['state'] == estado_anomalia].copy()
        features_iso = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio']
        
        # IA Rodando
        iso = IsolationForest(contamination=contamination, random_state=42)
        df_iso['anomalia'] = iso.fit_predict(df_iso[features_iso])
        
        # -1 é anomalia, 1 é normal
        anomalias = df_iso[df_iso['anomalia'] == -1]
        
        st.metric("Semanas Anômalas Encontradas", len(anomalias))
        
        # Gráfico Scatter para mostrar onde estão as anomalias
        fig_iso = px.scatter(
            df_iso, x='semana_ref', y='temperatura_media', 
            color=df_iso['anomalia'].astype(str),
            color_discrete_map={'-1': 'red', '1': 'blue'},
            title=f"Linha do Tempo: Pontos Vermelhos são Anomalias em {estado_anomalia}",
            hover_data=features_iso
        )
        st.plotly_chart(fig_iso, use_container_width=True)
        
        st.markdown("#### Tabela dos Eventos Extremos")
        st.dataframe(anomalias[['semana_ref'] + features_iso].sort_values('semana_ref'), use_container_width=True)

# ==============================================================================
# TAB 3: PREVISÃO TEMPORAL (MANTIDO DO ANTERIOR)
# ==============================================================================
with tab3:
    st.subheader("🔮 Previsão de Futuro (Séries Temporais)")
    
    var_time = st.selectbox("O que prever?", list(mapa_nomes.keys()), format_func=lambda x: mapa_nomes[x], key='time_var')
    estado_filtro = st.selectbox("Estado:", sorted(df['state'].unique()), key='time_state')
    
    # Preparação (código otimizado da versão anterior)
    df_time = df[df['state'] == estado_filtro].copy()
    df_grouped = df_time.groupby('semana_ref')[var_time].mean().reset_index().sort_values('semana_ref')
    df_grouped['dia_ordinal'] = df_grouped['semana_ref'].apply(lambda x: x.toordinal())
    df_grouped['mes'] = df_grouped['semana_ref'].dt.month
    
    meses_dummies = pd.get_dummies(df_grouped['mes'], prefix='mes').astype(int)
    # Garante 12 colunas
    for i in range(1, 13):
        if f'mes_{i}' not in meses_dummies.columns: meses_dummies[f'mes_{i}'] = 0
    meses_dummies = meses_dummies[sorted(meses_dummies.columns)]
    
    df_ml_t = pd.concat([df_grouped, meses_dummies], axis=1)
    features_time = ['dia_ordinal'] + list(meses_dummies.columns)
    
    # Treino e Previsão
    model_full = LinearRegression()
    model_full.fit(df_ml_t[features_time], df_ml_t[var_time])
    
    # Futuro
    ultima_data = df_grouped['semana_ref'].max()
    datas_futuras = [ultima_data + pd.Timedelta(days=x) for x in range(7, 365, 7)]
    df_futuro = pd.DataFrame({'semana_ref': datas_futuras})
    df_futuro['dia_ordinal'] = df_futuro['semana_ref'].apply(lambda x: x.toordinal())
    df_futuro['mes'] = df_futuro['semana_ref'].dt.month
    
    dummies_fut = pd.get_dummies(df_futuro['mes'], prefix='mes').astype(int)
    for col in meses_dummies.columns:
        if col not in dummies_fut.columns: dummies_fut[col] = 0
    dummies_fut = dummies_fut[sorted(meses_dummies.columns)]
    
    X_futuro = pd.concat([df_futuro[['dia_ordinal']], dummies_fut], axis=1)
    y_fut = model_full.predict(X_futuro)
    
    # Plot
    fig_fut = go.Figure()
    fig_fut.add_trace(go.Scatter(x=df_grouped['semana_ref'], y=df_grouped[var_time], name='Histórico', line=dict(color='blue')))
    fig_fut.add_trace(go.Scatter(x=df_futuro['semana_ref'], y=y_fut, name='Previsão (1 Ano)', line=dict(color='green', width=3)))
    fig_fut.update_layout(title=f"Tendência + Sazonalidade: {mapa_nomes[var_time]} em {estado_filtro}")
    st.plotly_chart(fig_fut, use_container_width=True)
