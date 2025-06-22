import json
import streamlit as st
from kafka import KafkaProducer

@st.cache_resource
def iniciar_kafka():
    """
    Inicializa um produtor Kafka.
    Se não conseguir conectar, o aplicativo continua funcionando sem enviar mensagens.
    
    Returns:
        KafkaProducer: Produtor Kafka ou None em caso de falha
    """
    try:
        # Tenta conectar ao Kafka com vários servidores possíveis
        kafka_servers = ['kafka:29092']
        for server in kafka_servers:
            try:
                producer = KafkaProducer(
                    bootstrap_servers=server,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    api_version_auto_timeout_ms=5000, 
                    request_timeout_ms=5000
                )
                return producer
            except Exception as e:
                pass
        
        return None
    except Exception as e:
        return None

def enviar_para_kafka(mensagem, topico='transacoes'):
    """
    Envia uma mensagem para um tópico Kafka
    
    Args:
        mensagem (dict): Mensagem a ser enviada
        topico (str, optional): Nome do tópico. Defaults to 'transacoes'.
    
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    producer = iniciar_kafka()
    if producer:
        try:
            producer.send(topico, mensagem)
            return True
        except Exception as e:
            return False
    return False