import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

st.header("🤖 Inteligência Artificial e Modelagem")
st.markdown("Uma suíte completa de algoritmos para entender o passado, detectar padrões ocultos e prever o futuro.")

# --- 1. CARREGAMENTO DE DADOS ---
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
        # Cria uma coluna numérica para o tempo (necessário para regressão temporal)
        df['tempo_ordinal'] = df['semana_ref'].apply(lambda x: x.toordinal())
    
    # Remove linhas com NaNs para não quebrar os modelos
    cols_numericas = ['chuva_media_semanal', 'temperatura_media', 'umidade_media', 
                      'vento_medio', 'pressao_media', 'radiacao_media']
    # Mapeamento para nomes bonitos
    mapa = {c: c.replace('_media', '').replace('_medio', '').replace('_semanal', '').capitalize() for c in cols_numericas}
    
    df = df.dropna(subset=cols_numericas)
    return df, mapa

# Carrega GeoJSON para o mapa de clusters
@st.cache_data
def carregar_geojson_ml():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        return None

df, mapa_nomes = carregar_dados_ml()
geojson = carregar_geojson_ml()

# --- DEFINIÇÃO DAS ABAS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 Regressão (Causa & Efeito)", 
    "🔍 Clustering (Padrões)", 
    "🚨 Anomalias (Extremos)", 
    "🔮 Previsão (Futuro)"
])

# ==============================================================================
# TAB 1: REGRESSÃO LINEAR MÚLTIPLA (Supervisionado)
# ==============================================================================
with tab1:
    st.subheader("Quem influencia quem?")
    st.info("Descubra como variáveis explicativas (X) impactam uma variável alvo (Y).")
    
    col1, col2 = st.columns(2)
    with col1:
        target = st.selectbox("🎯 Variável Alvo (Y):", list(mapa_nomes.keys()), format_func=lambda x: mapa_nomes[x], index=1)
    with col2:
        features_possiveis = [c for c in mapa_nomes.keys() if c != target]
        features = st.multiselect("📊 Variáveis Explicativas (X):", features_possiveis, default=[features_possiveis[0]])

    if features:
        # Preparação
        X = df[features]
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Modelo
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Métricas
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        c1, c2 = st.columns(2)
        c1.metric("R² (Capacidade de Explicação)", f"{r2:.2%}", help="Quanto da variação do Y é explicado pelo X.")
        c2.metric("Erro Médio (MAE)", f"{mae:.2f}", help="Erro médio absoluto na unidade da variável.")
        
        # Tabela de Coeficientes
        coef_df = pd.DataFrame({'Variável': features, 'Impacto (Coef)': model.coef_})
        coef_df = coef_df.sort_values(by='Impacto (Coef)', key=abs, ascending=False)
        st.markdown("#### ⚖️ Peso de cada Variável")
        st.dataframe(coef_df, hide_index=True, use_container_width=True)
        
        # Gráfico Real vs Previsto
        fig = px.scatter(x=y_test, y=y_pred, labels={'x': 'Valor Real', 'y': 'Valor Previsto'}, opacity=0.5, title="Realidade vs Modelo")
        fig.add_shape(type="line", line=dict(dash='dash'), x0=y.min(), y0=y.max(), x1=y.min(), y1=y.max())
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# TAB 2: CLUSTERING (Não Supervisionado - K-Means)
# ==============================================================================
with tab2:
    st.subheader("Redefinindo o Brasil Climático")
    st.markdown("A IA agrupa estados com comportamentos climáticos semelhantes, ignorando fronteiras.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        n_clusters = st.slider("Número de Grupos:", 2, 8, 4)
        features_cluster = st.multiselect(
            "Variáveis para Agrupar:", 
            list(mapa_nomes.keys()),
            default=['temperatura_media', 'chuva_media_semanal', 'umidade_media'],
            format_func=lambda x: mapa_nomes[x],
            key='cluster_features'
        )
        
    if features_cluster:
        # Agrupamento da média histórica por estado
        df_estado = df.groupby('state')[features_cluster].mean().reset_index()
        
        # Normalização (Crucial para K-Means)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_estado[features_cluster])
        
        # Modelo
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_estado['Cluster'] = kmeans.fit_predict(X_scaled).astype(str)
        
        with col2:
            if geojson:
                fig_map = px.choropleth_mapbox(
                    df_estado, geojson=geojson, locations='state', featureidkey="properties.sigla",
                    color='Cluster', mapbox_style="carto-positron", zoom=3, center={"lat": -15.7, "lon": -52},
                    title="Grupos Climáticos Identificados", color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Mapa não carregou (GeoJSON offline).")
        
        with st.expander("Ver detalhes dos grupos"):
            resumo = df_estado.groupby('Cluster')[features_cluster].mean().reset_index()
            st.dataframe(resumo.style.background_gradient(cmap='Blues'), use_container_width=True)

# ==============================================================================
# TAB 3: DETECÇÃO DE ANOMALIAS (Isolation Forest)
# ==============================================================================
with tab3:
    st.subheader("Caçador de Extremos Climáticos")
    st.markdown("O algoritmo detecta semanas 'bizarras' que fogem do padrão normal.")
    
    c_iso1, c_iso2 = st.columns(2)
    contamination = c_iso1.slider("Sensibilidade (% de Anomalias):", 1, 10, 2) / 100
    estado_anomalia = c_iso2.selectbox("Filtrar Estado:", sorted(df['state'].unique()), key='iso_state')
    
    if st.button("Detectar Anomalias"):
        df_iso = df[df['state'] == estado_anomalia].copy()
        features_iso = ['temperatura_media', 'chuva_media_semanal', 'umidade_media', 'vento_medio']
        
        # Modelo
        iso = IsolationForest(contamination=contamination, random_state=42)
        df_iso['anomalia'] = iso.fit_predict(df_iso[features_iso])
        
        anomalias = df_iso[df_iso['anomalia'] == -1]
        st.metric("Semanas Anômalas Encontradas", len(anomalias))
        
        # Gráfico
        fig_iso = px.scatter(
            df_iso, x='semana_ref', y='temperatura_media', 
            color=df_iso['anomalia'].astype(str),
            color_discrete_map={'-1': 'red', '1': 'blue'},
            title=f"Linha do Tempo: Vermelho = Anomalia",
            hover_data=features_iso
        )
        st.plotly_chart(fig_iso, use_container_width=True)
        st.dataframe(anomalias[['semana_ref'] + features_iso].sort_values('semana_ref'), use_container_width=True)

# ==============================================================================
# TAB 4: PREVISÃO TEMPORAL (Séries Temporais com Validação)
# ==============================================================================
with tab4:
    st.subheader("🔮 Previsão de Futuro com Backtesting")
    st.markdown("O modelo aprende Tendência (Anos) e Sazonalidade (Meses) usando Regressão com Dummies.")
    
    var_time = st.selectbox("O que prever?", list(mapa_nomes.keys()), format_func=lambda x: mapa_nomes[x], key='time_var')
    estado_filtro = st.selectbox("Filtrar por Estado:", sorted(df['state'].unique()), key='time_state_filter')
    
    # Preparação
    df_time = df[df['state'] == estado_filtro].copy()
    df_grouped = df_time.groupby('semana_ref')[var_time].mean().reset_index().sort_values('semana_ref')
    
    # Feature Engineering
    df_grouped['dia_ordinal'] = df_grouped['semana_ref'].apply(lambda x: x.toordinal())
    df_grouped['mes'] = df_grouped['semana_ref'].dt.month
    
    # Dummies para Sazonalidade (One-Hot Encoding)
    meses_dummies = pd.get_dummies(df_grouped['mes'], prefix='mes').astype(int)
    # Garante que existem as colunas mes_1 a mes_12 mesmo que falte dados
    for i in range(1, 13):
        if f'mes_{i}' not in meses_dummies.columns: meses_dummies[f'mes_{i}'] = 0
    meses_dummies = meses_dummies[sorted(meses_dummies.columns)]
    
    df_ml = pd.concat([df_grouped, meses_dummies], axis=1)
    features_time = ['dia_ordinal'] + list(meses_dummies.columns)
    
    # --- VALIDAÇÃO (BACKTESTING) ---
    st.markdown("### 1️⃣ Validação: Teste no Passado (Backtesting)")
    qtd_teste = 52 # Último ano (aprox 52 semanas)
    
    if len(df_ml) > qtd_teste * 2:
        # Separação Treino (Passado) e Teste (Último Ano)
        train = df_ml.iloc[:-qtd_teste]
        test = df_ml.iloc[-qtd_teste:]
        
        model_val = LinearRegression()
        model_val.fit(train[features_time], train[var_time])
        pred_val = model_val.predict(test[features_time])
        
        mae_val = mean_absolute_error(test[var_time], pred_val)
        erro_perc = (mae_val / test[var_time].mean()) * 100
        
        c_v1, c_v2, c_v3 = st.columns(3)
        c_v1.metric("Erro Médio (MAE)", f"{mae_val:.2f}")
        c_v2.metric("Margem de Erro (%)", f"{erro_perc:.1f}%")
        
        if erro_perc < 10: c_v3.success("✅ Modelo Confiável")
        elif erro_perc < 20: c_v3.warning("⚠️ Precisão Razoável")
        else: c_v3.error("❌ Modelo Instável")
        
        fig_val = go.Figure()
        fig_val.add_trace(go.Scatter(x=train['semana_ref'], y=train[var_time], name='Treino (O que ele aprendeu)', line=dict(color='gray')))
        fig_val.add_trace(go.Scatter(x=test['semana_ref'], y=test[var_time], name='Realidade (Oculto)', line=dict(color='blue')))
        fig_val.add_trace(go.Scatter(x=test['semana_ref'], y=pred_val, name='Previsão do Modelo', line=dict(color='orange', dash='dot')))
        fig_val.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0), title="Teste Cego: O modelo previu 2021 sem ver os dados?")
        st.plotly_chart(fig_val, use_container_width=True)
    else:
        st.warning("Dados insuficientes para validação.")

    # --- PREVISÃO FUTURA ---
    st.markdown("### 2️⃣ Projeção Futura (Próximos 12 Meses)")
    
    # Treino com TUDO (incluindo o ano de teste)
    model_full = LinearRegression()
    model_full.fit(df_ml[features_time], df_ml[var_time])
    
    # Cria datas futuras
    ultima_data = df_grouped['semana_ref'].max()
    datas_futuras = [ultima_data + pd.Timedelta(days=x) for x in range(7, 365, 7)]
    df_fut = pd.DataFrame({'semana_ref': datas_futuras})
    df_fut['dia_ordinal'] = df_fut['semana_ref'].apply(lambda x: x.toordinal())
    df_fut['mes'] = df_fut['semana_ref'].dt.month
    
    # Dummies futuro (mesma lógica)
    dum_fut = pd.get_dummies(df_fut['mes'], prefix='mes').astype(int)
    for col in meses_dummies.columns:
        if col not in dum_fut.columns: dum_fut[col] = 0
    dum_fut = dum_fut[sorted(meses_dummies.columns)]
    
    X_fut = pd.concat([df_fut[['dia_ordinal']], dum_fut], axis=1)
    y_fut = model_full.predict(X_fut)
    
    # Plot Final
    fig_fut = go.Figure()
    fig_fut.add_trace(go.Scatter(x=df_grouped['semana_ref'], y=df_grouped[var_time], name='Histórico', line=dict(color='blue')))
    fig_fut.add_trace(go.Scatter(x=df_fut['semana_ref'], y=y_fut, name='Previsão Futura', line=dict(color='green', width=3)))
    
    # Intervalo de Confiança (Sombra baseada no erro do teste)
    if 'mae_val' in locals():
        fig_fut.add_trace(go.Scatter(
            x=list(df_fut['semana_ref']) + list(df_fut['semana_ref'])[::-1],
            y=list(y_fut + mae_val) + list(y_fut - mae_val)[::-1],
            fill='toself', fillcolor='rgba(0,128,0,0.2)',
            line=dict(color='rgba(255,255,255,0)'), name='Margem de Erro Esperada'
        ))
        
    fig_fut.update_layout(height=500, title=f"Projeção: {mapa_nomes[var_time]} em {estado_filtro}")
    st.plotly_chart(fig_fut, use_container_width=True)
