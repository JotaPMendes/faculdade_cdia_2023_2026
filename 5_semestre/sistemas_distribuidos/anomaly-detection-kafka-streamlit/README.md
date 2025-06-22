# Sistema de Detecção de Transações Anômalas

![Badge](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)
![Badge](https://img.shields.io/badge/Python-3.9-blue)
![Badge](https://img.shields.io/badge/Streamlit-1.22.0-red)
![Badge](https://img.shields.io/badge/Kafka-2.0.2-green)

> Sistema para monitoramento inteligente de padrões de gastos dos usuários e detecção de transações anômalas em tempo real.

## 📋 Índice

* [Visão Geral](#visão-geral)
* [Tecnologias Utilizadas](#tecnologias-utilizadas)
* [Estrutura do Projeto](#estrutura-do-projeto)
* [Funcionalidades](#funcionalidades)
* [Como Executar](#como-executar)
* [Demonstração](#demonstração)
* [Contribuindo](#contribuindo)

## 🔍 Visão Geral

Este projeto é uma Prova de Conceito (POC) que demonstra a utilização do Apache Kafka juntamente com Streamlit para criar um sistema de detecção de transações anômalas em tempo real. O sistema monitora os padrões de gastos dos usuários e alerta quando uma transação se desvia significativamente do padrão histórico.

Principais características:
- Interface web interativa com Streamlit
- Processamento de eventos em tempo real com Kafka
- Algoritmos de detecção de anomalias baseados em desvio padrão
- Sistema de alertas via e-mail
- Visualização de dados com gráficos interativos
- Armazenamento em banco de dados SQLite

## 🛠 Tecnologias Utilizadas

- **Frontend/Interface**: Streamlit 1.22.0
- **Processamento de eventos**: Apache Kafka 7.3.0
- **Banco de Dados**: SQLite (local) / PostgreSQL (Docker)
- **Linguagem**: Python 3.9
- **Visualização de dados**: Plotly, Matplotlib, Seaborn
- **Contêinerização**: Docker e Docker Compose
- **Análise de Dados**: Pandas, NumPy

## 📁 Estrutura do Projeto

```
.
├── app_streamlit.py           # Arquivo principal da aplicação Streamlit
├── docker-compose.yml         # Configuração dos serviços Docker
├── requirements.txt           # Dependências Python do projeto
├── transactions.csv           # Dados iniciais para importação
├── transacoes.db              # Banco de dados SQLite
└── app/                       # Pasta com módulos da aplicação
    ├── components/            # Componentes da interface
    │   ├── data_viewer.py     # Visualização de dados e dashboards
    │   ├── settings.py        # Configurações da aplicação
    │   └── transaction_form.py# Formulário para inserção de transações
    ├── config/                # Configurações do sistema
    │   └── config.py          # Constantes e configurações
    ├── database/              # Módulos de banco de dados
    │   ├── connection.py      # Conexão com SQLite
    │   └── sql/               # Scripts SQL
    │       └── init.sql       # Inicialização do PostgreSQL
    ├── services/              # Serviços externos
    │   ├── email_service.py   # Serviço de envio de e-mails
    │   └── kafka_service.py   # Integração com Apache Kafka
    └── utils/                 # Utilitários
        └── analysis.py        # Algoritmos de análise e detecção
```

## ⚙️ Funcionalidades

1. **Inserção de Transações**
   - Cadastro manual de transações
   - Importação via CSV
   - Processamento via Kafka

2. **Detecção de Anomalias**
   - Algoritmo baseado em desvio padrão
   - Limite configurável para alertas
   - Análise do histórico do usuário

3. **Sistema de Alertas**
   - Notificações na interface
   - Envio de e-mails detalhados
   - Histórico de alertas

4. **Dashboard Analítico**
   - Visualização de todas as transações
   - Gráficos por usuário, tipo e status
   - Métricas e estatísticas em tempo real

5. **Configurações Personalizáveis**
   - Ajuste de parâmetros de detecção
   - Configuração de e-mail
   - Modo de demonstração

## 🚀 Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados
- Git

### Usando Docker (recomendado)

1. **Clone o repositório**
   ```bash
   git clone https://github.com/JotaPMendes/anomaly-detection-kafka-streamlit.git
   cd anomaly-detection-kafka-streamlit
   ```

2. **Inicie os serviços com Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Acesse a aplicação**
   Abra o navegador e acesse: http://localhost:8501

4. **Parar a aplicação**
   ```bash
   docker-compose down
   ```

### Execução Local (sem Docker)

1. **Clone o repositório**
   ```bash
   git clone https://github.com/JotaPMendes/anomaly-detection-kafka-streamlit.git
   cd anomaly-detection-kafka-streamlit
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação Streamlit**
   ```bash
   streamlit run app_streamlit.py
   ```

## 📊 Demonstração

O sistema possui um modo de demonstração onde você pode facilmente testar a detecção de anomalias:

1. Navegue até a aba "Inserir Transação"
2. Use o formulário "Gerar Transação Anômala para Demonstração"
3. O sistema criará automaticamente uma transação que será detectada como anômala
4. Você verá um alerta na interface e, se configurado, receberá um e-mail
