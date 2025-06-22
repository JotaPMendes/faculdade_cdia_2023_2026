# Arquivo de configuração com constantes e estilos
import os

# Caminho para arquivos de configuração
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Configuração do Kafka
KAFKA_BROKER = "kafka:29092"
KAFKA_TOPIC = "transacoes"

# Limiar fixo para detecção de anomalias (em desvios padrão)
LIMIAR_DESVIOS = 2.0

# Estilos CSS para a aplicação
CSS_STYLES = """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        color: #424242;
        margin-bottom: 2rem;
        text-align: center;
        font-style: italic;
    }
    
    .alert-card {
        background-color: #FFEBEE;
        border-left: 5px solid #F44336;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    
    .success-message {
        color: #2E7D32;
        font-weight: bold;
    }
    
    .warning-message {
        color: #FF6F00;
        font-weight: bold;
    }
    
    .error-message {
        color: #C62828;
        font-weight: bold;
    }
    
    .metric-card {
        background-color: #E3F2FD;
        border-radius: 5px;
        padding: 1rem;
        text-align: center;
    }
    
    .container {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Personaliza o estilo da sidebar */
    .css-1d391kg {
        background-color: #F5F7F9;
    }
    
    /* Melhora o estilo dos botões */
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: #1565C0;
        border: none;
    }
    
    /* Estilo para os separadores */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background-color: #E0E0E0;
    }
    
    /* Estilizar abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F5F7F9;
        border-radius: 5px 5px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: white;
    }
    
    /* Estilos para o novo cabeçalho de configurações */
    .config-header {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    
    /* Ocultar botão de sidebar */
    button[kind="header"] {
        display: none;
    }
    
    /* Estilos para notificações e mensagens */
    .notification-box {
        text-align: center;
        margin: 10px auto 20px auto;
        max-width: 800px;
        padding: 10px;
        border-radius: 5px;
    }
    
    .success-notification {
        background-color: #E8F5E9;
        border: 1px solid #4CAF50;
        color: #2E7D32;
    }
    
    .info-notification {
        background-color: #E3F2FD;
        border: 1px solid #2196F3;
        color: #0D47A1;
    }
    
    .warning-notification {
        background-color: #FFF8E1;
        border: 1px solid #FFC107;
        color: #FF6F00;
    }
    
    /* Melhorias nos inputs */
    div[data-baseweb="input"] {
        border-radius: 5px !important;
    }
    
    div[data-baseweb="base-input"] {
        border-radius: 5px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Centralizando notificações específicas */
    .center-notification {
        margin: 15px auto;
        max-width: 600px;
        text-align: center;
    }
</style>
"""

# Configuração padrão para e-mail
DEFAULT_EMAIL = "joaopaulosouzamendes11@gmail.com"
DEFAULT_SMTP = "smtp.gmail.com"
DEFAULT_PORT = 587