import datetime
import streamlit as st

from app.database.connection import inserir_transacao_db
from app.services.kafka_service import enviar_para_kafka
from app.utils.analysis import detectar_anomalia
from app.services.email_service import enviar_email, gerar_email_alerta

def inserir_transacao(user_id, amount, tipo, status):
    """
    Insere uma transação no banco e envia para o Kafka.
    Também detecta anomalias e envia email se configurado.
    
    Args:
        user_id (int): ID do usuário
        amount (float): Valor da transação
        tipo (str): Tipo da transação (credit, debit)
        status (str): Status da transação
    
    Returns:
        int: ID da transação inserida
    """
    # Data atual
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Inserir no banco de dados
    transaction_id = inserir_transacao_db(user_id, amount, data_atual, tipo, status)
    
    # Mostrar notificação de sucesso
    st.markdown(f"""
    <div class="notification-box success-notification center-notification">
        <p><strong>✅ Transação #{transaction_id} registrada com sucesso!</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enviar para o Kafka
    mensagem = {
        "id": transaction_id,
        "user_id": user_id, 
        "amount": amount,
        "date": data_atual,
        "type": tipo,
        "status": status
    }
    
    # Enviar para o Kafka em segundo plano (não bloqueia se falhar)
    enviar_para_kafka(mensagem)
    
    # Retornar o ID da transação
    return transaction_id

def detectar_enviar_alerta_anomalia(user_id, amount, transaction_id):
    """
    Detecta se uma transação é anômala e envia alerta por email se configurado.
    
    Args:
        user_id (int): ID do usuário
        amount (float): Valor da transação
        transaction_id (int): ID da transação
    
    Returns:
        bool: True se alerta foi enviado, False caso contrário
    """
    # Verificar se as configurações de email estão preenchidas
    if not (
        st.session_state.get("email_user") and 
        st.session_state.get("email_pass") and 
        st.session_state.get("email_dest") and
        st.session_state.get("email_alerta_ativo", False)
    ):
        return False
    
    # Detectar anomalia
    resultado = detectar_anomalia(amount, user_id)
    
    # Se for anomalia, enviar email
    if resultado["is_anomalia"]:
        estatisticas = resultado["estatisticas"]
        desvios = resultado["desvios"]
        
        # Gerar conteúdo do email
        mensagem_text, mensagem_html = gerar_email_alerta(
            username=f"Usuário {user_id}",
            user_id=user_id,
            amount=amount,
            media=estatisticas["media"],
            desvio_padrao=estatisticas["desvio_padrao"],
            desvios=desvios,
            qtd_transacoes=estatisticas["qtd_transacoes"]
        )
        
        # Enviar email
        enviado = enviar_email(
            email_user=st.session_state["email_user"],
            email_pass=st.session_state["email_pass"],
            destinatario=st.session_state["email_dest"],
            assunto=f"🚨 ALERTA: Transação Anômala #{transaction_id} Detectada!",
            mensagem_text=mensagem_text,
            mensagem_html=mensagem_html,
            host=st.session_state.get("smtp_server", "smtp.gmail.com"),
            port=st.session_state.get("smtp_port", 587)
        )
        
        # Mostrar resultado
        if enviado:
            st.markdown("""
            <div class="notification-box warning-notification center-notification">
                <p><strong>📧 Email de alerta enviado com sucesso!</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        return enviado
    
    return False

def renderizar_formulario_transacao():
    """
    Renderiza o formulário de inserção de transação.
    """
    st.markdown("<h3>Nova Transação</h3>", unsafe_allow_html=True)
    
    # Formulário de inserção de dados
    with st.form(key="transacao_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Campos de inserção de dados
            user_id = st.number_input("ID do usuário", min_value=1, step=1, value=1)
            amount = st.number_input("Valor (R$)", min_value=0.01, step=0.01, value=100.00)
            
        with col2:
            tipo = st.selectbox("Tipo de transação", ["credit", "debit"])
            status = st.selectbox("Status da transação", ["completed", "pending", "failed"])
        
        submit_button = st.form_submit_button(label="Inserir Transação")
        
        if submit_button:
            transaction_id = inserir_transacao(user_id, amount, tipo, status)
            
            # Se a transação foi bem-sucedida
            if transaction_id:
                # Verificar se é uma anomalia e precisa enviar alerta
                detectar_enviar_alerta_anomalia(user_id, amount, transaction_id)
                
                # Mostrar resultado da detecção de anomalia
                resultado = detectar_anomalia(amount, user_id)
                st.markdown(f"""
                <div class="notification-box {'warning-notification' if resultado['is_anomalia'] else 'info-notification'} center-notification">
                    <p><strong>{resultado['mensagem']}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Adicionar alerta à sessão se for anomalia
                if resultado["is_anomalia"]:
                    agora = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    # Adicionar na lista de alertas da sessão
                    if 'alertas' not in st.session_state:
                        st.session_state.alertas = []
                        
                    st.session_state.alertas.append({
                        "usuario": f"Usuário {user_id}",
                        "mensagem": resultado["mensagem"],
                        "horario": agora
                    })
                    
                    # Recarregar para mostrar alerta no topo
                    st.experimental_rerun()
    
    # Separador
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Modo de demonstração - gerar transação anômala
    st.markdown("<h3>Modo de Demonstração</h3>", unsafe_allow_html=True)
    
    # Ativar/desativar modo de demonstração
    modo_demo = st.checkbox(
        "Ativar modo de demonstração",
        value=st.session_state.get("modo_demo", False),
        help="Gera uma transação anômala para demonstrar a detecção"
    )
    st.session_state["modo_demo"] = modo_demo
    
    if modo_demo:
        st.info("Neste modo, você pode gerar automaticamente uma transação que será detectada como anômala.")
        
        with st.form(key="demo_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_id_demo = st.number_input(
                    "ID do usuário", 
                    min_value=1, 
                    step=1, 
                    value=1,
                    key="user_id_demo"
                )
            
            with col2:
                # Adicionar valor muito acima do normal
                st.markdown("##### Valor automaticamente elevado para ser detectado como anomalia")
                multiplicador = st.slider(
                    "Multiplicador (quanto maior, mais anômala será):", 
                    min_value=3, 
                    max_value=10, 
                    value=5
                )
            
            submit_demo = st.form_submit_button(label="Gerar Transação Anômala de Teste")
            
            if submit_demo:
                # Obter média e desvio padrão de transações anteriores
                resultado = detectar_anomalia(100, user_id_demo)  # Valor inicial qualquer
                estatisticas = resultado["estatisticas"]
                
                # Se não houver estatísticas, usar valores padrão
                if estatisticas["media"] == 0:
                    valor_anomalo = 1000  # Valor padrão alto
                else:
                    # Calcular valor anômalo baseado nas estatísticas
                    valor_anomalo = estatisticas["media"] + (estatisticas["desvio_padrao"] * multiplicador)
                    
                # Inserir a transação anômala
                transaction_id = inserir_transacao(user_id_demo, valor_anomalo, "credit", "completed")
                
                # Verificar se é uma anomalia e enviar alerta
                if transaction_id:
                    detectar_enviar_alerta_anomalia(user_id_demo, valor_anomalo, transaction_id)
                    
                    # Mostrar resultado da detecção de anomalia
                    resultado = detectar_anomalia(valor_anomalo, user_id_demo)
                    st.markdown(f"""
                    <div class="notification-box warning-notification center-notification">
                        <p><strong>{resultado['mensagem']}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Adicionar alerta à sessão
                    if resultado["is_anomalia"]:
                        agora = datetime.datetime.now().strftime("%H:%M:%S")
                        
                        # Adicionar na lista de alertas da sessão
                        if 'alertas' not in st.session_state:
                            st.session_state.alertas = []
                            
                        st.session_state.alertas.append({
                            "usuario": f"Usuário {user_id_demo}",
                            "mensagem": resultado["mensagem"],
                            "horario": agora
                        })
                        
                        # Recarregar para mostrar alerta no topo
                        st.experimental_rerun()