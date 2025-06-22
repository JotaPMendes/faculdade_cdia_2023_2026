import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

from app.database.connection import obter_todas_transacoes, obter_transacoes_por_usuario
from app.utils.analysis import formatar_moeda, gerar_metricas_transacoes

def renderizar_dashboard_metricas(df_transacoes):
    """
    Renderiza o dashboard com métricas gerais das transações.
    
    Args:
        df_transacoes (pandas.DataFrame): DataFrame com as transações
    """
    # Obter métricas
    metricas = gerar_metricas_transacoes(df_transacoes)
    
    # Mostrar métricas em colunas
    st.subheader("Métricas Gerais")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total de Transações", 
                  value=f"{metricas['total_transacoes']:,}".replace(",", "."))
    
    with col2:
        st.metric(label="Total de Usuários", 
                  value=f"{metricas['total_usuarios']:,}".replace(",", "."))
    
    with col3:
        st.metric(label="Valor Médio (R$)", 
                  value=f"{metricas['valor_medio']:.2f}")
    
    with col4:
        st.metric(label="Maior Valor (R$)", 
                  value=f"{metricas['maior_valor']:.2f}")
    
    # Mostrar gráficos de distribuição
    st.subheader("Distribuição das Transações")
    col1, col2 = st.columns(2)
    
    # Só gera gráficos se houver dados
    if len(df_transacoes) > 0:
        with col1:
            # Gráfico de tipo de transação
            tipos = pd.DataFrame({
                'Tipo': list(metricas['tipos_transacao'].keys()),
                'Quantidade': list(metricas['tipos_transacao'].values())
            })
            fig_tipos = px.pie(tipos, values='Quantidade', names='Tipo', 
                              title='Transações por Tipo',
                              color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_tipos, use_container_width=True)
            
        with col2:
            # Gráfico de status de transação
            status = pd.DataFrame({
                'Status': list(metricas['status_transacao'].keys()),
                'Quantidade': list(metricas['status_transacao'].values())
            })
            fig_status = px.pie(status, values='Quantidade', names='Status', 
                               title='Transações por Status',
                               color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("Não há dados suficientes para gerar gráficos")

def renderizar_visualizacao_dados():
    """
    Renderiza a visualização de dados e dashboard.
    """
    st.markdown("<h3>Dashboard & Visualização de Dados</h3>", unsafe_allow_html=True)
    
    # Opções de filtro e visualização
    tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Tabelas de Dados"])
    
    # Tab 1: Dashboard
    with tab1:
        # Pegar dados atualizados (limitado a 100 para performance)
        df_transacoes = obter_todas_transacoes(100)
        renderizar_dashboard_metricas(df_transacoes)
        
        # Mostrar gráfico de série temporal se houver dados
        if len(df_transacoes) > 0:
            st.subheader("Série Temporal de Transações")
            
            # Converter data para datetime e agrupar
            df_transacoes['date'] = pd.to_datetime(df_transacoes['date'])
            df_agrupado = df_transacoes.groupby(pd.Grouper(key='date', freq='D')).size().reset_index(name='count')
            
            # Gráfico de linha
            fig = px.line(df_agrupado, x='date', y='count', 
                         title='Volume de Transações por Dia',
                         labels={'date': 'Data', 'count': 'Quantidade'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Dados em tabela
    with tab2:
        # Filtro por usuário
        st.subheader("Visualização de Transações")
        opcao = st.radio("Visualizar:", options=["Todas as Transações", "Filtrar por Usuário"])
        
        if opcao == "Todas as Transações":
            # Limitar para não sobrecarregar a UI
            limite = st.slider("Limite de registros:", min_value=10, max_value=200, value=50)
            df = obter_todas_transacoes(limite)
            st.dataframe(df, use_container_width=True)
        else:
            user_id = st.number_input("ID do usuário:", min_value=1, step=1, value=1)
            limite = st.slider("Limite de registros:", min_value=10, max_value=100, value=30)
            df = obter_transacoes_por_usuario(user_id, limite)
            
            if len(df) > 0:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"Nenhuma transação encontrada para o usuário {user_id}")

def renderizar_grafico_anomalias(user_id=None):
    """
    Renderiza um gráfico de anomalias para um usuário específico ou todos os usuários.
    
    Args:
        user_id (int, optional): ID do usuário ou None para todos. Defaults to None.
    """
    st.markdown("<h3>Análise de Anomalias</h3>", unsafe_allow_html=True)
    
    # Obter dados
    if user_id:
        df = obter_transacoes_por_usuario(user_id)
        titulo = f"Padrão de Transações do Usuário {user_id}"
    else:
        df = obter_todas_transacoes(100)  # Limitar para performance
        titulo = "Padrão de Transações (Todos os Usuários)"
    
    # Verificar se há dados suficientes
    if len(df) < 3:
        st.info("Não há dados suficientes para análise de anomalias")
        return
    
    # Calcular estatísticas globais
    media_global = df['amount'].mean()
    desvio_global = df['amount'].std()
    
    # Criar linha de corte para anomalias (2 desvios padrão)
    limiar_superior = media_global + (2 * desvio_global)
    
    # Classificar transações como normais ou anômalas
    df['anomalia'] = df['amount'] > limiar_superior
    
    # Gráfico de dispersão
    fig = px.scatter(
        df, 
        x='id', 
        y='amount',
        color='anomalia',
        color_discrete_map={True: 'red', False: 'blue'},
        title=titulo,
        labels={'id': 'ID da Transação', 'amount': 'Valor (R$)', 'anomalia': 'Anomalia'},
        hover_data=['user_id', 'date', 'type', 'status']
    )
    
    # Adicionar linha de média e limiar
    fig.add_hline(y=media_global, line_dash="dash", line_color="green", annotation_text="Média")
    fig.add_hline(y=limiar_superior, line_dash="dash", line_color="red", annotation_text="Limiar de Anomalia")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estatísticas
    st.caption(f"Média: R$ {media_global:.2f} | Desvio Padrão: R$ {desvio_global:.2f} | Limiar: R$ {limiar_superior:.2f}")
    
    # Mostrar transações anômalas em tabela
    anomalias = df[df['anomalia']]
    if len(anomalias) > 0:
        st.subheader(f"Transações Anômalas ({len(anomalias)})")
        st.dataframe(anomalias)
    else:
        st.success("Nenhuma transação anômala detectada nos dados analisados")