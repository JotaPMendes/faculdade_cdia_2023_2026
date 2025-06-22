import sqlite3
import pandas as pd
import streamlit as st

@st.cache_resource
def iniciar_conexao():
    """
    Inicializa uma conexão com o banco de dados SQLite.
    Usa cache_resource para manter a conexão entre as execuções.
    
    Returns:
        sqlite3.Connection: Objeto de conexão com o banco de dados
    """
    try:
        conn = sqlite3.connect('./transacoes.db', check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        st.warning("Usando banco de dados em memória como fallback")
        return sqlite3.connect(':memory:', check_same_thread=False)

def inicializar_banco_dados():
    """
    Inicializa o banco de dados, criando a tabela de transações se não existir
    e importando dados do CSV caso o banco esteja vazio.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    # Criar a tabela se não existir
    conn = iniciar_conexao()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        type TEXT,
        status TEXT
    )
    ''')
    conn.commit()
    
    # Verificar quantos registros existem
    cursor.execute("SELECT COUNT(*) FROM transacoes")
    count = cursor.fetchone()[0]
    
    # Mostrar mensagem centralizada
    if count > 0:
        st.markdown(f"""
        <div class="notification-box success-notification center-notification">
            <p><strong>✅ Banco de dados existente com {count} registros!</strong></p>
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        # Importar dados
        try:
            df = pd.read_csv('transactions.csv')
            st.markdown("""
            <div class="notification-box info-notification center-notification">
                <p><strong>ℹ️ Importando dados do CSV para o banco de dados...</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Inserir dados
            importados = 0
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO transacoes (id, user_id, amount, date, type, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (row['id'], row['user_id'], row['amount'], row['date'], row['type'], row['status'])
                )
                importados += 1
            
            conn.commit()
            
            st.markdown(f"""
            <div class="notification-box success-notification center-notification">
                <p><strong>✅ {importados} transações importadas com sucesso!</strong></p>
            </div>
            """, unsafe_allow_html=True)
            return True
        except Exception as e:
            st.markdown(f"""
            <div class="notification-box warning-notification center-notification">
                <p><strong>⚠️ Erro ao importar dados: {e}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            return False

def inserir_transacao_db(user_id, amount, data_atual, tipo, status):
    """
    Insere uma nova transação no banco de dados.
    
    Args:
        user_id (int): ID do usuário
        amount (float): Valor da transação
        data_atual (str): Data da transação
        tipo (str): Tipo da transação (credit, debit)
        status (str): Status da transação (completed, pending, failed)
        
    Returns:
        int: ID da transação inserida
    """
    conn = iniciar_conexao()
    cursor = conn.cursor()
    
    # Inserir no banco de dados (usando autoincremento para ID)
    cursor.execute(
        "INSERT INTO transacoes (user_id, amount, date, type, status) VALUES (?, ?, ?, ?, ?)", 
        (user_id, amount, data_atual, tipo, status)
    )
    conn.commit()
    
    # Obter o ID da transação inserida
    return cursor.lastrowid

def obter_transacoes_por_usuario(user_id, limit=None):
    """
    Obtém as transações de um usuário específico.
    
    Args:
        user_id (int): ID do usuário
        limit (int, optional): Limite de registros a retornar
    
    Returns:
        pandas.DataFrame: DataFrame com as transações do usuário
    """
    conn = iniciar_conexao()
    query = f"SELECT * FROM transacoes WHERE user_id = {user_id} ORDER BY id DESC"
    
    if limit:
        query += f" LIMIT {limit}"
        
    return pd.read_sql_query(query, conn)

def obter_todas_transacoes(limit=30):
    """
    Obtém todas as transações do banco de dados.
    
    Args:
        limit (int, optional): Limite de registros a retornar. Defaults to 30.
    
    Returns:
        pandas.DataFrame: DataFrame com todas as transações
    """
    conn = iniciar_conexao()
    return pd.read_sql_query(f"SELECT * FROM transacoes ORDER BY id DESC LIMIT {limit}", conn)

def obter_usuarios_unicos():
    """
    Obtém a lista de usuários únicos no banco de dados.
    
    Returns:
        pandas.DataFrame: DataFrame com os IDs de usuários únicos
    """
    conn = iniciar_conexao()
    return pd.read_sql_query("SELECT DISTINCT user_id FROM transacoes", conn)