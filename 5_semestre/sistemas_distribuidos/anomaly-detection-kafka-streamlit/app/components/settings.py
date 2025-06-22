import streamlit as st
import os
import json

from app.config.config import CONFIG_FILE, KAFKA_BROKER, KAFKA_TOPIC, LIMIAR_DESVIOS

def salvar_configuracoes(config):
    """
    Salva as configurações no arquivo.
    
    Args:
        config (dict): Dicionário com as configurações
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # Salvar configurações
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def carregar_configuracoes():
    """
    Carrega as configurações do arquivo.
    
    Returns:
        dict: Dicionário com as configurações ou valores padrão
    """
    # Valores padrão
    config = {
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_user": "",
            "email_pass": "",
            "email_dest": "",
            "email_alerta_ativo": False
        },
        "kafka": {
            "broker": KAFKA_BROKER,
            "topic": KAFKA_TOPIC,
            "ativo": True
        },
        "analise": {
            "limiar_desvios": LIMIAR_DESVIOS
        }
    }
    
    try:
        # Verificar se arquivo existe
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config_salvo = json.load(f)
                
                # Atualizar configurações (mantendo estrutura)
                if "email" in config_salvo:
                    config["email"].update(config_salvo["email"])
                
                if "kafka" in config_salvo:
                    config["kafka"].update(config_salvo["kafka"])
                
                if "analise" in config_salvo:
                    config["analise"].update(config_salvo["analise"])
    except Exception as e:
        st.warning(f"Erro ao carregar configurações: {str(e)}")
    
    return config

def atualizar_session_state_com_config():
    """
    Atualiza as session_state com as configurações salvas.
    """
    config = carregar_configuracoes()
    
    # Email
    st.session_state["smtp_server"] = config["email"]["smtp_server"]
    st.session_state["smtp_port"] = config["email"]["smtp_port"]
    st.session_state["email_user"] = config["email"]["email_user"]
    st.session_state["email_pass"] = config["email"]["email_pass"]
    st.session_state["email_dest"] = config["email"]["email_dest"]
    st.session_state["email_alerta_ativo"] = config["email"]["email_alerta_ativo"]
    
    # Kafka
    st.session_state["kafka_broker"] = config["kafka"]["broker"]
    st.session_state["kafka_topic"] = config["kafka"]["topic"]
    st.session_state["kafka_ativo"] = config["kafka"]["ativo"]
    
    # Análise
    st.session_state["limiar_desvios"] = config["analise"]["limiar_desvios"]

def renderizar_configuracoes():
    """
    Renderiza a página de configurações.
    """
    st.markdown("<h3>Configurações</h3>", unsafe_allow_html=True)
    
    # Verificar se as configurações foram carregadas
    if "email_user" not in st.session_state:
        atualizar_session_state_com_config()
    
    # Tabs para diferentes configurações
    tab1, tab2, tab3 = st.tabs(["⚙️ Geral", "📧 Email", "🚀 Kafka"])
    
    # Tab 1: Configurações Gerais
    with tab1:
        st.subheader("Configurações Gerais")
        
        # Configuração de análise de anomalias
        st.markdown("#### Detecção de Anomalias")
        limiar = st.slider(
            "Limiar de desvios padrão para detecção de anomalias:", 
            min_value=1.0, 
            max_value=5.0, 
            value=float(st.session_state.get("limiar_desvios", LIMIAR_DESVIOS)),
            step=0.1,
            help="Quanto maior o valor, menos sensível será a detecção de anomalias"
        )
        st.session_state["limiar_desvios"] = limiar
    
    # Tab 2: Configurações de Email
    with tab2:
        st.subheader("Configurações de Email")
        
        # Configurações de SMTP
        st.markdown("#### Servidor SMTP")
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input(
                "Servidor SMTP:", 
                value=st.session_state.get("smtp_server", "smtp.gmail.com"),
                help="Para Gmail, use smtp.gmail.com"
            )
            st.session_state["smtp_server"] = smtp_server
            
        with col2:
            smtp_port = st.number_input(
                "Porta SMTP:", 
                value=int(st.session_state.get("smtp_port", 587)),
                help="Para Gmail, use 587"
            )
            st.session_state["smtp_port"] = smtp_port
        
        # Credenciais
        st.markdown("#### Credenciais")
        email_user = st.text_input(
            "Email de envio:", 
            value=st.session_state.get("email_user", "joaopaulosouzamendes11@gmail.com"),
            help="Email que enviará as notificações"
        )
        st.session_state["email_user"] = email_user
        
        email_pass = st.text_input(
            "Senha ou Chave de App:", 
            value=st.session_state.get("email_pass", ""),
            type="password",
            help="Para Gmail, use uma Senha de App gerada nas configurações de segurança"
        )
        st.session_state["email_pass"] = email_pass
        
        # Destinatário
        st.markdown("#### Notificações")
        email_dest = st.text_input(
            "Email de destino:", 
            value=st.session_state.get("email_dest", "joaopaulosouzamendes11@gmail.com"),
            help="Email que receberá os alertas"
        )
        st.session_state["email_dest"] = email_dest
        
        # Ativar/desativar alertas
        email_ativo = st.checkbox(
            "Ativar alertas por email", 
            value=st.session_state.get("email_alerta_ativo", False),
            help="Enviar alertas por email quando detectar transações anômalas"
        )
        st.session_state["email_alerta_ativo"] = email_ativo
        
    # Tab 3: Configurações do Kafka
    with tab3:
        st.subheader("Configurações do Kafka")
        
        # Configuração do broker
        kafka_broker = st.text_input(
            "Endereço do Broker:", 
            value=st.session_state.get("kafka_broker", KAFKA_BROKER),
            help="Endereço do broker Kafka (host:porta)"
        )
        st.session_state["kafka_broker"] = kafka_broker
        
        # Configuração do tópico
        kafka_topic = st.text_input(
            "Tópico:", 
            value=st.session_state.get("kafka_topic", KAFKA_TOPIC),
            help="Nome do tópico Kafka para enviar as transações"
        )
        st.session_state["kafka_topic"] = kafka_topic
        
        # Ativar/desativar Kafka
        kafka_ativo = st.checkbox(
            "Ativar envio para Kafka", 
            value=st.session_state.get("kafka_ativo", True),
            help="Ative para enviar transações para o Kafka"
        )
        st.session_state["kafka_ativo"] = kafka_ativo
    
    # Botão para salvar configurações
    if st.button("Salvar Configurações", type="primary"):
        config = {
            "email": {
                "smtp_server": st.session_state.get("smtp_server"),
                "smtp_port": st.session_state.get("smtp_port"),
                "email_user": st.session_state.get("email_user"),
                "email_pass": st.session_state.get("email_pass"),
                "email_dest": st.session_state.get("email_dest"),
                "email_alerta_ativo": st.session_state.get("email_alerta_ativo")
            },
            "kafka": {
                "broker": st.session_state.get("kafka_broker"),
                "topic": st.session_state.get("kafka_topic"),
                "ativo": st.session_state.get("kafka_ativo")
            },
            "analise": {
                "limiar_desvios": st.session_state.get("limiar_desvios")
            }
        }
        
        if salvar_configuracoes(config):
            st.success("Configurações salvas com sucesso!")
        else:
            st.error("Erro ao salvar configurações. Verifique os logs.")