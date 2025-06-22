import numpy as np
import pandas as pd
import streamlit as st

from app.database.connection import obter_transacoes_por_usuario
from app.config.config import LIMIAR_DESVIOS

def formatar_moeda(valor):
    """
    Formata um valor numérico para o formato de moeda brasileira (R$).
    
    Args:
        valor (float): Valor a ser formatado
        
    Returns:
        str: Valor formatado como moeda (ex: R$ 1.234,56)
    """
    if pd.isna(valor):
        return "R$ 0,00"
        
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def calcular_estatisticas_usuario(user_id):
    """
    Calcula estatísticas para um usuário específico.
    
    Args:
        user_id (int): ID do usuário
    
    Returns:
        dict: Dicionário com estatísticas (media, desvio_padrao, qtd_transacoes)
    """
    # Obter as transações do usuário
    df_usuario = obter_transacoes_por_usuario(user_id)
    
    # Verificar se há transações suficientes
    if len(df_usuario) < 3:
        return {
            "media": 0,
            "desvio_padrao": 0,
            "qtd_transacoes": len(df_usuario)
        }
    
    # Calcular estatísticas básicas
    media = df_usuario['amount'].mean()
    desvio_padrao = df_usuario['amount'].std()
    
    return {
        "media": media,
        "desvio_padrao": desvio_padrao,
        "qtd_transacoes": len(df_usuario)
    }

def detectar_anomalia(amount, user_id):
    """
    Detecta se uma transação é anômala com base nos padrões do usuário.
    Uma transação é considerada anômala se estiver acima de LIMIAR_DESVIOS 
    desvios padrão da média das transações do usuário.
    
    Args:
        amount (float): Valor da transação
        user_id (int): ID do usuário
    
    Returns:
        dict: Resultado da detecção com estatísticas e status
    """
    # Obter estatísticas do usuário
    estatisticas = calcular_estatisticas_usuario(user_id)
    
    # Se não houver transações suficientes, não é possível detectar anomalia
    if estatisticas["qtd_transacoes"] < 3:
        return {
            "is_anomalia": False,
            "mensagem": f"Não há transações suficientes para análise (apenas {estatisticas['qtd_transacoes']})",
            "estatisticas": estatisticas,
            "desvios": 0
        }
    
    # Calcular quantos desvios padrão a transação está da média
    media = estatisticas["media"]
    desvio_padrao = estatisticas["desvio_padrao"]
    
    # Evitar divisão por zero
    if desvio_padrao == 0:
        desvios = 0
    else:
        desvios = abs(amount - media) / desvio_padrao
    
    # Verificar se é anomalia
    is_anomalia = desvios > LIMIAR_DESVIOS
    
    # Preparar mensagem
    if is_anomalia:
        mensagem = f"⚠️ ANOMALIA DETECTADA! Valor R$ {amount:.2f} está {desvios:.1f}x acima do padrão"
    else:
        mensagem = f"✅ Transação normal (dentro de {LIMIAR_DESVIOS} desvios padrão)"
    
    return {
        "is_anomalia": is_anomalia,
        "mensagem": mensagem,
        "estatisticas": estatisticas,
        "desvios": desvios
    }

def gerar_metricas_transacoes(df):
    """
    Gera métricas gerais para as transações.
    
    Args:
        df (pandas.DataFrame): DataFrame com as transações
    
    Returns:
        dict: Dicionário com métricas gerais
    """
    total_transacoes = len(df)
    valor_medio = df['amount'].mean() if total_transacoes > 0 else 0
    maior_valor = df['amount'].max() if total_transacoes > 0 else 0
    total_usuarios = df['user_id'].nunique() if total_transacoes > 0 else 0
    
    # Contagem por tipo de transação
    tipos_transacao = df['type'].value_counts().to_dict() if total_transacoes > 0 else {}
    
    # Contagem por status
    status_transacao = df['status'].value_counts().to_dict() if total_transacoes > 0 else {}
    
    return {
        "total_transacoes": total_transacoes,
        "valor_medio": valor_medio,
        "maior_valor": maior_valor,
        "total_usuarios": total_usuarios,
        "tipos_transacao": tipos_transacao,
        "status_transacao": status_transacao
    }