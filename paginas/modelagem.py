import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

st.header("🤖 Modelagem e Previsões (Machine Learning)")
st.markdown("Aqui utilizamos algoritmos de aprendizado de máquina para entender impactos e prever o futuro.")

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
        # Cria uma coluna numérica para o tempo (necessário para regressão temporal)
        df['tempo_ordinal'] = df['semana_ref'].apply(lambda x: x.toordinal())
    
    # Remove linhas com NaNs para não quebrar o modelo
    cols_numericas = ['chuva_media_semanal', 'temperatura_media', 'umidade_media', 
                      'vento_medio', 'pressao_media', 'radiacao_media']
    # Mapeamento para nomes bonitos
    mapa = {c: c.replace('_media', '').replace('_medio', '').replace('_semanal', '').capitalize() for c in cols_numericas}
    df = df.dropna(subset=cols_numericas)
    return df, mapa

df, mapa_nomes = carregar_dados_ml()

tab1, tab2 = st.tabs(["📉 Regressão (Influência)", "u23f1\ufe0f Previsão Temporal"])

# --- TAB 1: REGRESSÃO LINEAR MÚLTIPLA ---
with tab1:
    st.subheader("Quem influencia quem?")
    st.info("Descubra como variáveis explicativas (X) impactam uma variável alvo (Y).")
    
    col1, col2 = st.columns(2)
    with col1:
        target = st.selectbox("🎯 Variável Alvo (Y):", list(mapa_nomes.keys()), format_func=lambda x: mapa_nomes[x], index=1)
    with col2:
        # Remove a target da lista de features possíveis
        features_possiveis = [c for c in mapa_nomes.keys() if c != target]
        features = st.multiselect("📊 Variáveis Explicativas (X):", features_possiveis, default=[features_possiveis[0]])

    if features:
        # Preparar dados
        X = df[features]
        y = df[target]
        
        # Divisão Treino/Teste
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Treinar Modelo
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Previsões e Métricas
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        # Exibir Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("R² (Explicação)", f"{r2:.2%}", help="Quanto da variação do Y é explicado pelo X.")
        c2.metric("Erro Médio (MAE)", f"{mae:.2f}", help="Erro médio absoluto na unidade da variável.")
        
        # Exibir Coeficientes (Importância)
        coef_df = pd.DataFrame({'Variável': features, 'Impacto (Coef)': model.coef_})
        coef_df = coef_df.sort_values(by='Impacto (Coef)', key=abs, ascending=False)
        
        st.markdown("#### ⚖️ Peso de cada Variável")
        st.dataframe(coef_df, hide_index=True, use_container_width=True)
        
        # Gráfico Real vs Previsto
        st.markdown("#### 👁️ Real vs Previsto (Conjunto de Teste)")
        fig = px.scatter(x=y_test, y=y_pred, labels={'x': 'Valor Real', 'y': 'Valor Previsto pelo Modelo'}, opacity=0.5)
        fig.add_shape(type="line", line=dict(dash='dash'), x0=y.min(), y0=y.max(), x1=y.min(), y1=y.max())
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: SÉRIES TEMPORAIS (FORECAST) ---
with tab2:
    st.subheader("🔮 Previsão de Futuro")
    st.markdown("Este modelo aprende a **Tendência** (anos) e a **Sazonalidade** (meses) para projetar o futuro.")
    
    var_time = st.selectbox("O que queremos prever?", list(mapa_nomes.keys()), format_func=lambda x: mapa_nomes[x], key='time_var')
    
    # Filtrar por estado (opcional, para reduzir ruído)
    estados = sorted(df['state'].unique())
    estado_filtro = st.selectbox("Filtrar por Estado (Recomendado para melhor precisão):", estados)
    
    df_time = df[df['state'] == estado_filtro].copy()
    
    # Agrupar por data (média semanal)
    df_grouped = df_time.groupby('semana_ref')[var_time].mean().reset_index()
    df_grouped = df_grouped.sort_values('semana_ref')
    
    # --- ENGENHARIA DE RECURSOS (Feature Engineering) ---
    # Criamos colunas para "ensinar" o modelo sobre sazonalidade
    df_grouped['dia_ordinal'] = df_grouped['semana_ref'].apply(lambda x: x.toordinal())
    df_grouped['mes'] = df_grouped['semana_ref'].dt.month
    
    # Cria One-Hot Encoding para os meses (Janeiro=1, Fevereiro=0...) 
    # Isso permite ao modelo linear capturar curvas sazonais!
    meses_dummies = pd.get_dummies(df_grouped['mes'], prefix='mes').astype(int)
    df_ml = pd.concat([df_grouped, meses_dummies], axis=1)
    
    # Definição de X e Y
    features_time = ['dia_ordinal'] + list(meses_dummies.columns)
    X_t = df_ml[features_time]
    y_t = df_ml[var_time]
    
    # Treino
    model_t = LinearRegression()
    model_t.fit(X_t, y_t)
    
    # --- PREVISÃO FUTURA ---
    dias_futuros = 365 # Prever 1 ano
    ultima_data = df_grouped['semana_ref'].max()
    datas_futuras = [ultima_data + pd.Timedelta(days=x) for x in range(7, dias_futuros, 7)] # Semanal
    
    df_futuro = pd.DataFrame({'semana_ref': datas_futuras})
    df_futuro['dia_ordinal'] = df_futuro['semana_ref'].apply(lambda x: x.toordinal())
    df_futuro['mes'] = df_futuro['semana_ref'].dt.month
    
    # Recria as dummies para o futuro (garantindo todas as colunas de meses)
    dummies_futuro = pd.get_dummies(df_futuro['mes'], prefix='mes').astype(int)
    # Garante que colunas faltantes (ex: se previsão for curta) sejam preenchidas com 0
    for col in meses_dummies.columns:
        if col not in dummies_futuro.columns:
            dummies_futuro[col] = 0
    dummies_futuro = dummies_futuro[meses_dummies.columns] # Garante ordem
    
    X_futuro = pd.concat([df_futuro[['dia_ordinal']], dummies_futuro], axis=1)
    
    # Prever
    y_futuro_pred = model_t.predict(X_futuro)
    df_futuro['previsao'] = y_futuro_pred
    df_futuro['tipo'] = 'Previsão'
    
    # Plotar
    df_grouped['tipo'] = 'Histórico'
    df_grouped = df_grouped.rename(columns={var_time: 'valor'})
    df_futuro = df_futuro.rename(columns={'previsao': 'valor'})
    
    df_final = pd.concat([df_grouped[['semana_ref', 'valor', 'tipo']], df_futuro[['semana_ref', 'valor', 'tipo']]])
    
    fig_time = px.line(df_final, x='semana_ref', y='valor', color='tipo', 
                       color_discrete_map={'Histórico': 'blue', 'Previsão': 'orange'},
                       title=f"Previsão de {mapa_nomes[var_time]} para {estado_filtro} (Próximos 12 meses)")
    
    st.plotly_chart(fig_time, use_container_width=True)
    st.caption("Nota: Este modelo usa Regressão Linear com componentes sazonais (Dummy Variables) para estimar o padrão anual.")
