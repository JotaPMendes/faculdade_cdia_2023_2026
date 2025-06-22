-- Inicialização do banco de dados PostgreSQL
-- Este arquivo será executado quando o container PostgreSQL for iniciado

-- Criar tabela de transações caso ela não exista
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(10) CHECK (type IN ('credit', 'debit')),
    status VARCHAR(20) CHECK (status IN ('completed', 'pending', 'failed'))
);

-- Criar índices para melhorar a performance das consultas
CREATE INDEX IF NOT EXISTS idx_transacoes_user_id ON transacoes(user_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_date ON transacoes(date);

-- Permissões (ajuste de acordo com seu usuário)
GRANT ALL PRIVILEGES ON TABLE transacoes TO admin;
GRANT USAGE, SELECT ON SEQUENCE transacoes_id_seq TO admin;