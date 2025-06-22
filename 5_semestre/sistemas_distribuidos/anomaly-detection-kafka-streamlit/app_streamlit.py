import streamlit as st
from app.config.config import CSS_STYLES, LIMIAR_DESVIOS
from app.database.connection import inicializar_banco_dados
from app.components.transaction_form import renderizar_formulario_transacao
from app.components.data_viewer import renderizar_visualizacao_dados, renderizar_grafico_anomalias
from app.components.settings import renderizar_configuracoes
from app.services.email_service import enviar_email_alerta

# Configuração da página Streamlit
st.set_page_config(
    page_title="Sistema de Detecção de Transações Anômalas",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Aplicar estilos CSS definidos no módulo de configuração
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🔍 Sistema de Detecção de Transações Anômalas</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monitoramento inteligente de padrões de gastos dos usuários</p>', unsafe_allow_html=True)

# Inicialização do estado da sessão para armazenar alertas
if 'alertas' not in st.session_state:
    st.session_state.alertas = []
    
# Inicializar configurações se não existirem
if 'email_user' not in st.session_state:
    st.session_state.email_user = ""
    st.session_state.email_pass = ""
    st.session_state.email_dest = ""
    st.session_state.smtp_server = "smtp.gmail.com"
    st.session_state.smtp_port = 587
    st.session_state.email_alerta_ativo = False
    st.session_state.modo_demo = False

# Configurações no topo
st.markdown('<div class="config-header">', unsafe_allow_html=True)
renderizar_configuracoes()
st.markdown('</div>', unsafe_allow_html=True)

# Inicializar o sistema de banco de dados
inicializado = inicializar_banco_dados()

# Exibir alertas no topo da página se houver algum
if st.session_state.alertas:
    with st.expander("🚨 ALERTAS DE TRANSAÇÕES ANÔMALAS", expanded=True):
        st.markdown("""
        <div style="background-color: #FFEBEE; padding: 10px; border-radius: 5px; margin-bottom: 15px; 
                    border-left: 5px solid #F44336;">
            <h4 style="color: #C62828; margin-top: 0;">Transações Suspeitas Detectadas</h4>
            <p>As seguintes transações foram identificadas como potencialmente anômalas com base nos padrões de gasto históricos.</p>
        </div>
        """, unsafe_allow_html=True)
        
        for i, alerta in enumerate(reversed(st.session_state.alertas)):
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 5px; 
                        margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-weight: bold; color: #F44336;">⏰ {alerta['horario']}</span>
                    <span style="font-weight: bold;">👤 {alerta['usuario']}</span>
                </div>
                <div style="margin-top: 10px; padding: 10px; background-color: #FFEBEE; 
                            border-radius: 5px; font-size: 0.9em;">
                    {alerta['mensagem']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("Limpar Todos os Alertas", key="clear_alerts"):
            st.session_state.alertas = []
            st.experimental_rerun()

# Criar abas para organizar a interface
tab1, tab2, tab3 = st.tabs(["Inserir Transação", "Visualizar Transações", "Estatísticas por Usuário"])

# Aba 1 - Inserir nova transação
with tab1:
    renderizar_formulario_transacao()

# Aba 2 - Visualização de transações
with tab2:
    renderizar_visualizacao_dados()

# Aba 3 - Estatísticas por usuário
with tab3:
    renderizar_grafico_anomalias()