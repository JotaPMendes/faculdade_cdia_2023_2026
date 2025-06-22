import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pandas as pd

def enviar_email(email_user, email_pass, destinatario, assunto, mensagem_text, mensagem_html=None, host="smtp.gmail.com", port=587):
    """
    Envia um email usando os parâmetros fornecidos.
    
    Args:
        email_user (str): Email do remetente
        email_pass (str): Senha do remetente
        destinatario (str): Email do destinatário
        assunto (str): Assunto do email
        mensagem_text (str): Corpo do email em texto plano
        mensagem_html (str, optional): Corpo do email em HTML. Defaults to None.
        host (str, optional): Servidor SMTP. Defaults to "smtp.gmail.com".
        port (int, optional): Porta SMTP. Defaults to 587.
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        st.info(f"Tentando enviar e-mail via {host}:{port}...")
        server = smtplib.SMTP(host, port)
        server.starttls()
        
        # Adicionando logs para debug
        st.info(f"Autenticando como {email_user}...")
        server.login(email_user, email_pass)
        
        email = MIMEMultipart('alternative')
        email['From'] = email_user
        email['To'] = destinatario
        email['Subject'] = assunto
        
        # Sempre adiciona a parte de texto simples
        part1 = MIMEText(mensagem_text, 'plain')
        email.attach(part1)
        
        # Adiciona a parte HTML se fornecida
        if mensagem_html:
            part2 = MIMEText(mensagem_html, 'html')
            email.attach(part2)
        
        st.info(f"Enviando e-mail para {destinatario}...")
        server.sendmail(email_user, destinatario, email.as_string())
        server.quit()
        st.success('✅ E-mail enviado com sucesso!')
        return True
    except Exception as e:
        st.error(f'❌ Erro ao enviar e-mail: {e}')
        st.info("""
        Se estiver usando Gmail, verifique se:
        1. "Acesso a app menos seguro" está ativado ou
        2. Você criou uma "Senha de app" nas configurações de segurança
        3. A verificação em duas etapas está ativada
        """)
        return False

def gerar_email_alerta(username, user_id, amount, media, desvio_padrao, desvios, qtd_transacoes):
    """
    Gera o conteúdo de email para alerta de transação anômala
    
    Args:
        username (str): Nome de usuário
        user_id (int): ID do usuário
        amount (float): Valor da transação
        media (float): Média das transações do usuário
        desvio_padrao (float): Desvio padrão das transações do usuário
        desvios (float): Número de desvios padrão da transação atual
        qtd_transacoes (int): Quantidade de transações do usuário
    
    Returns:
        tuple: (mensagem_text, mensagem_html)
    """
    # Email com HTML para melhor formatação
    mensagem_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #f44336; border-radius: 5px;">
            <div style="background-color: #f44336; color: white; padding: 10px 15px; text-align: center; border-radius: 3px;">
                <h2 style="margin: 0;">⚠️ ALERTA DE TRANSAÇÃO ANÔMALA ⚠️</h2>
            </div>
            <div style="padding: 15px;">
                <p><strong>Usuário:</strong> {username} (ID: {user_id})</p>
                <p><strong>Valor da transação:</strong> R$ {amount:.2f}</p>
                <p><strong>Anomalia detectada:</strong> {desvios:.1f}x acima do padrão normal</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Média histórica:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">R$ {media:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Desvio padrão:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">R$ {desvio_padrao:.2f}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Histórico de transações:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{qtd_transacoes} transações</td>
                    </tr>
                </table>
                <p style="font-size: 0.9em; color: #555; text-align: center; margin-top: 20px;">
                    Este é um alerta automático do sistema de detecção de transações anômalas.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Versão em texto simples para fallback
    mensagem_text = f"""
    🚨 ALERTA DE TRANSAÇÃO ANÔMALA 🚨
    
    Usuário: {username} (ID: {user_id})
    Valor da transação: R$ {amount:.2f}
    Anomalia detectada: {desvios:.1f}x acima do padrão normal
    
    Média histórica: R$ {media:.2f}
    Desvio padrão: R$ {desvio_padrao:.2f}
    Histórico: {qtd_transacoes} transações
    """
    
    return mensagem_text, mensagem_html

def enviar_email_alerta(config, transacao, desvio):
    """
    Envia um email de alerta para transação suspeita.
    
    Args:
        config (dict): Configurações de email
        transacao (dict): Dados da transação suspeita
        desvio (float): Valor do desvio padrão detectado
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    # Verificar se o envio de alertas está ativado
    if not config["email_alerta_ativo"]:
        return False
        
    # Verificar se as configurações estão completas
    if not all([config["smtp_server"], config["smtp_port"], 
                config["email_user"], config["email_pass"], 
                config["email_dest"]]):
        st.warning("Configurações de email incompletas. Verifique a página de configurações.")
        return False
        
    try:
        # Configurar email
        msg = MIMEMultipart()
        msg['From'] = config["email_user"]
        msg['To'] = config["email_dest"]
        msg['Subject'] = f"ALERTA: Transação Suspeita Detectada - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Converter transação em string formatada para o corpo do email
        if isinstance(transacao, dict):
            # Formatando os dados da transação para o corpo do email
            valor = transacao.get('valor', 'N/A')
            if isinstance(valor, (int, float)):
                valor = f"R$ {valor:.2f}"
                
            corpo = f"""
            <h2>Alerta de Transação Suspeita</h2>
            <p>Uma transação com comportamento anômalo foi detectada pelo sistema.</p>
            
            <h3>Detalhes da Transação:</h3>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <td><b>ID:</b></td>
                    <td>{transacao.get('id', 'N/A')}</td>
                </tr>
                <tr>
                    <td><b>Data/Hora:</b></td>
                    <td>{transacao.get('data_hora', 'N/A')}</td>
                </tr>
                <tr>
                    <td><b>Valor:</b></td>
                    <td>{valor}</td>
                </tr>
                <tr>
                    <td><b>Tipo:</b></td>
                    <td>{transacao.get('tipo', 'N/A')}</td>
                </tr>
                <tr>
                    <td><b>Descrição:</b></td>
                    <td>{transacao.get('descricao', 'N/A')}</td>
                </tr>
                <tr>
                    <td><b>Desvio Padrão:</b></td>
                    <td>{desvio:.2f} desvios da média</td>
                </tr>
            </table>
            
            <p>Este é um email automático. Por favor, não responda.</p>
            """
        else:
            corpo = f"""
            <h2>Alerta de Transação Suspeita</h2>
            <p>Uma transação com comportamento anômalo foi detectada pelo sistema.</p>
            <p>Desvio detectado: {desvio:.2f} desvios padrão da média</p>
            <p>Este é um email automático. Por favor, não responda.</p>
            """
            
        # Anexar corpo do email
        msg.attach(MIMEText(corpo, 'html'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["email_user"], config["email_pass"])
        
        # Enviar email
        server.send_message(msg)
        server.quit()
        
        st.success("Email de alerta enviado com sucesso!")
        return True
        
    except Exception as e:
        st.error(f"Erro ao enviar email: {str(e)}")
        return False
        
def testar_conexao_email(config):
    """
    Testa a conexão com o servidor de email.
    
    Args:
        config (dict): Configurações de email
        
    Returns:
        bool: True se a conexão foi bem sucedida, False caso contrário
    """
    try:
        # Verificar se as configurações estão completas
        if not all([config["smtp_server"], config["smtp_port"], 
                   config["email_user"], config["email_pass"]]):
            return False, "Configurações incompletas"
            
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["email_user"], config["email_pass"])
        server.quit()
        
        return True, "Conexão bem sucedida!"
        
    except Exception as e:
        return False, f"Erro: {str(e)}"