import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

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

tab1, tab2 = st.tabs(["📉 Regressão (Influência)", "🔮 Previsão Temporal (Validada)"])

# --- TAB 1: REGRESSÃO LINEAR MÚLTIPLA ---
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
        X = df[features]
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("R² (Explicação)", f"{r2:.2%}", help="Quanto da variação do Y é explicado pelo X.")
        c2.metric("Erro Médio (MAE)", f"{mae:.2f}", help="Erro médio absoluto na unidade da variável.")
        
        coef_df = pd.DataFrame({'Variável': features, 'Impacto (Coef)': model.coef_})
        coef_df = coef_df.sort_values(by='Impacto (Coef)', key=abs, ascending=False)
        
        st.markdown("#### ⚖️ Peso de cada Variável")
        st.dataframe(coef_df, hide_index=True, use_container_width=True)
        
        fig = px.scatter(x=y_test, y=y_pred, labels={'x': 'Valor Real', 'y': 'Valor Previsto pelo Modelo'}, opacity=0.5)
        fig.add_shape(type="line", line=dict(dash='dash'), x0=y.min(), y0=y.max(), x1=y.min(), y1=y.max())
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: SÉRIES TEMPORAIS (VALIDADA) ---
with tab2:
    st.subheader("🔮 Previsão de Futuro com Backtesting")
    st.markdown("O modelo aprende Tendência (Anos) e Sazonalidade (Meses).")
    
    var_time = st.selectbox("O que queremos prever?", list(mapa_nomes.keys()), format_func=lambda x: mapa_nomes[x], key='time_var')
    
    estados = sorted(df['state'].unique())
    estado_filtro = st.selectbox("Filtrar por Estado:", estados)
    
    # Preparação dos dados
    df_time = df[df['state'] == estado_filtro].copy()
    df_grouped = df_time.groupby('semana_ref')[var_time].mean().reset_index().sort_values('semana_ref')
    
    # Feature Engineering (Criar colunas matemáticas)
    df_grouped['dia_ordinal'] = df_grouped['semana_ref'].apply(lambda x: x.toordinal())
    df_grouped['mes'] = df_grouped['semana_ref'].dt.month
    
    # Dummies para Sazonalidade
    meses_dummies = pd.get_dummies(df_grouped['mes'], prefix='mes').astype(int)
    # Garante que temos todas as colunas de 1 a 12, mesmo se faltar dados
    for i in range(1, 13):
        if f'mes_{i}' not in meses_dummies.columns:
            meses_dummies[f'mes_{i}'] = 0
    meses_dummies = meses_dummies[sorted(meses_dummies.columns)] # Ordena colunas
            
    df_ml = pd.concat([df_grouped, meses_dummies], axis=1)
    features_time = ['dia_ordinal'] + list(meses_dummies.columns)
    
    # --- 1. ETAPA DE VALIDAÇÃO (BACKTESTING) ---
    st.markdown("---")
    st.markdown("### 1️⃣ Validação: O modelo acerta o passado?")
    
    # Separamos o último ano (52 semanas) para teste
    qtd_teste = 52
    if len(df_ml) > qtd_teste * 2: # Só faz se tiver dados suficientes
        train = df_ml.iloc[:-qtd_teste]
        test = df_ml.iloc[-qtd_teste:]
        
        # Treina só no passado antigo
        model_val = LinearRegression()
        model_val.fit(train[features_time], train[var_time])
        
        # Tenta prever o passado recente (que ele não viu)
        pred_val = model_val.predict(test[features_time])
        
        # Calcula Erro
        mae_val = mean_absolute_error(test[var_time], pred_val)
        rmse_val = np.sqrt(mean_squared_error(test[var_time], pred_val))
        media_real = test[var_time].mean()
        erro_percentual = (mae_val / media_real) * 100
        
        col_v1, col_v2, col_v3 = st.columns(3)
        col_v1.metric("Erro Médio (MAE)", f"{mae_val:.2f}", help="O quanto o modelo erra em média (na mesma unidade dos dados).")
        col_v2.metric("Margem de Erro (%)", f"{erro_percentual:.1f}%", help="O erro relativo à média dos valores.")
        
        if erro_percentual < 10:
            col_v3.success("✅ Modelo Confiável")
        elif erro_percentual < 20:
            col_v3.warning("⚠️ Precisão Razoável")
        else:
            col_v3.error("❌ Modelo Instável")
            
        # Gráfico de Validação
        fig_val = go.Figure()
        fig_val.add_trace(go.Scatter(x=train['semana_ref'], y=train[var_time], name='Treino (Passado Antigo)', line=dict(color='gray')))
        fig_val.add_trace(go.Scatter(x=test['semana_ref'], y=test[var_time], name='Realidade (Último Ano)', line=dict(color='blue')))
        fig_val.add_trace(go.Scatter(x=test['semana_ref'], y=pred_val, name='Previsão do Modelo', line=dict(color='orange', dash='dot')))
        fig_val.update_layout(title="Teste de Fidelidade (Backtest)", height=400)
        st.plotly_chart(fig_val, use_container_width=True)
        
    else:
        st.warning("Dados insuficientes para validação histórica segura.")

    # --- 2. ETAPA DE PREVISÃO FUTURA (PRODUÇÃO) ---
    st.markdown("---")
    st.markdown("### 2️⃣ Previsão: Olhando para o Futuro")
    
    # Agora treinamos com TODOS os dados disponíveis para máxima sabedoria
    model_full = LinearRegression()
    model_full.fit(df_ml[features_time], df_ml[var_time])
    
    # Criar datas futuras (1 ano)
    ultima_data = df_grouped['semana_ref'].max()
    datas_futuras = [ultima_data + pd.Timedelta(days=x) for x in range(7, 365, 7)]
    
    df_futuro = pd.DataFrame({'semana_ref': datas_futuras})
    df_futuro['dia_ordinal'] = df_futuro['semana_ref'].apply(lambda x: x.toordinal())
    df_futuro['mes'] = df_futuro['semana_ref'].dt.month
    
    # Dummies futuro
    dummies_fut = pd.get_dummies(df_futuro['mes'], prefix='mes').astype(int)
    for col in meses_dummies.columns:
        if col not in dummies_fut.columns:
            dummies_fut[col] = 0
    dummies_fut = dummies_fut[sorted(meses_dummies.columns)]
    
    X_futuro = pd.concat([df_futuro[['dia_ordinal']], dummies_fut], axis=1)
    
    # Prever
    y_fut = model_full.predict(X_futuro)
    
    # Plotar
    fig_fut = go.Figure()
    fig_fut.add_trace(go.Scatter(x=df_grouped['semana_ref'], y=df_grouped[var_time], name='Histórico Completo', line=dict(color='blue')))
    fig_fut.add_trace(go.Scatter(x=df_futuro['semana_ref'], y=y_fut, name='Previsão Futura (12 Meses)', line=dict(color='green', width=3)))
    
    # Intervalo de Confiança (Visual Simples baseado no MAE da validação)
    if 'mae_val' in locals():
        fig_fut.add_trace(go.Scatter(
            x=list(df_futuro['semana_ref']) + list(df_futuro['semana_ref'])[::-1],
            y=list(y_fut + mae_val) + list(y_fut - mae_val)[::-1],
            fill='toself',
            fillcolor='rgba(0,128,0,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Margem de Erro Esperada'
        ))

    fig_fut.update_layout(title=f"Projeção para os Próximos 12 Meses: {mapa_nomes[var_time]} ({estado_filtro})", height=500)
    st.plotly_chart(fig_fut, use_container_width=True)
