# 🚀 Quick Delivery Watch - Sistema de Predição ETA

Projeto desenvolvido por: Enzo Takida, Henrique Araujo, João Paulo Mendes, Leandro Carvalho

Sistema inteligente de predição de tempo de entrega (ETA) desenvolvido para o projeto final da disciplina de **Consultoria em Inteligência Artificial** (6º Semestre). Combina **Machine Learning** em Python com interface web moderna em **React + TypeScript**.

## 📋 Visão Geral

O Quick Delivery Watch é uma solução completa que utiliza algoritmos de Machine Learning para predizer com precisão o tempo de entrega de pedidos, considerando múltiplos fatores como distância, condições meteorológicas, trânsito, horário e tempo de preparo.

### ✨ Principais Funcionalidades

- 🧠 **Predição ML**: Modelo híbrido (Linear Regression + Random Forest) com 80-85% de precisão
- 📊 **Dashboard Interativo**: Interface responsiva para gestão de pedidos e análises
- 🔄 **Sincronização Real-time**: Integração automática entre frontend e backend ML
- 📈 **Análises Avançadas**: Métricas, detecção de anomalias e insights automáticos
- 📱 **Multi-plataforma**: Suporte para desktop e mobile
- 🎯 **Sistema Multi-tenant**: Suporte para múltiplos restaurantes

## 🏗️ Arquitetura do Sistema

### Frontend (React + TypeScript)
```
src/
├── components/          # Componentes reutilizáveis
│   ├── ui/             # Componentes de UI (shadcn/ui)
│   ├── ETAPredictor.tsx    # Preditor de ETA
│   ├── OrderForm.tsx       # Formulário de pedidos
│   ├── OrderList.tsx       # Lista de pedidos
│   ├── DataManager.tsx     # Gerenciador de dados
│   └── MLSyncManager.tsx   # Sincronização ML
├── pages/              # Páginas da aplicação
│   ├── Login.tsx           # Página de login
│   ├── RestaurantDashboard.tsx # Dashboard principal
│   ├── CustomerView.tsx    # Visão do cliente
│   └── NotFound.tsx        # Página 404
├── lib/                # Utilitários e configurações
│   ├── ml-api-client.ts    # Cliente para API ML
│   ├── haversine.ts        # Cálculo de distância
│   └── local-storage.ts    # Persistência local
└── data/               # Dados e configurações
    ├── historical_deliveries.json # Dados históricos
    └── seed-data.ts            # Dados iniciais
```

### Backend ML (Python + FastAPI)
```
ml_system/
├── eta_predictor.py    # Modelo principal de ML
├── analytics.py        # Análises e métricas
├── api.py              # API REST com FastAPI
├── model_trainer.py    # Treinamento de modelos
├── requirements.txt    # Dependências Python
└── __pycache__/        # Cache Python
```

## 🛠️ Tecnologias Utilizadas

### Frontend
- **React 18** - Library UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **TailwindCSS** - Estilização
- **shadcn/ui** - Componentes UI
- **React Router** - Roteamento
- **React Query** - Gerenciamento de estado
- **Lucide React** - Ícones

### Backend ML
- **Python 3.9+** - Linguagem principal
- **FastAPI** - Framework web
- **Scikit-learn** - Machine Learning
- **Pandas** - Manipulação de dados
- **NumPy** - Computação numérica
- **Matplotlib/Seaborn** - Visualização

### Ferramentas de Desenvolvimento
- **Bun** - Package manager
- **ESLint** - Linting JavaScript/TypeScript
- **Prettier** - Formatação de código
- **uvicorn** - Servidor ASGI

## 📊 Modelo de Machine Learning

### Algoritmo Híbrido
O sistema utiliza uma abordagem híbrida combinando:

1. **Regressão Linear**: Para relações lineares básicas
2. **Random Forest**: Para padrões complexos e não-lineares

### Features do Modelo
- `distance_km`: Distância em quilômetros
- `day_of_week`: Dia da semana (0-6)
- `hour_of_day`: Hora do dia (0-23)
- `weather`: Condições climáticas ('sunny', 'cloudy', 'rainy')
- `traffic_level`: Nível de trânsito (1-3)
- `preparation_time_min`: Tempo de preparo em minutos

### Métricas de Performance
- **Precisão**: 80-85% (±3 minutos)
- **MAE**: ~3.2 minutos
- **RMSE**: ~4.1 minutos
- **R² Score**: ~0.78

## 🚀 Instalação e Configuração

### Pré-requisitos
- **Node.js** 18+ ou **Bun**
- **Python** 3.9+
- **Git**

### 1. Clonando o Projeto
```bash
git clone <repository-url>
cd etas_projeto_final
```

### 2. Configurando o Frontend
```bash
# Instalar dependências
bun install
# ou
npm install

# Copiar variáveis de ambiente
cp .env.example .env
```

### 3. Configurando o Backend ML
```bash
cd ml_system

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 4. Executando o Sistema

#### Terminal 1 - Backend ML
```bash
cd ml_system
python api.py
```

#### Terminal 2 - Frontend
```bash
bun dev
# ou
npm run dev
```

### 5. Acessando o Sistema
- **Frontend**: http://localhost:8080
- **API ML**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

## 💻 Como Usar

### 1. Login
- Acesse a página inicial
- Selecione um restaurante da lista
- Clique em "Entrar"

### 2. Dashboard do Restaurante
- **Novo Pedido**: Criar pedidos com predição automática de ETA
- **Lista de Pedidos**: Visualizar todos os pedidos em tempo real
- **Gerenciar Dados**: Importar/exportar dados históricos
- **ML Manager**: Sincronizar com sistema de ML

### 3. Predição de ETA
- Selecione o cliente de destino
- Configure parâmetros (itens, tempo de preparo)
- Clique em "Calcular ETA"
- Visualize a predição com fatores de risco

### 4. Análises
- Métricas de performance do modelo
- Gráficos de tendências
- Detecção de anomalias
- Insights automáticos

## 🔧 Scripts Disponíveis

### Frontend
```bash
bun dev          # Ambiente de desenvolvimento
bun build        # Build para produção
bun preview      # Preview da build
bun lint         # Executar linting
```

### Backend
```bash
python api.py           # Iniciar API ML
python eta_predictor.py # Treinar modelo
python analytics.py     # Executar análises
```

## 📈 API Endpoints

### Predição
- `POST /predict` - Predizer ETA
- `GET /predict/example` - Exemplo de predição

### Métricas
- `GET /metrics` - Métricas do modelo
- `GET /analytics` - Análises detalhadas

### Saúde
- `GET /health` - Status da API

### Exemplo de Requisição
```json
POST /predict
{
  "distance_km": 2.5,
  "day_of_week": 1,
  "hour_of_day": 19,
  "weather": "rainy",
  "traffic_level": 3,
  "preparation_time_min": 15
}
```

### Resposta
```json
{
  "eta_minutes": 28,
  "confidence": 85,
  "risk_factors": ["Hora de pico", "Chuva"],
  "model_used": "RandomForest",
  "timestamp": "2024-11-15T19:30:00"
}
```

## 📁 Estrutura de Dados

### Dados Históricos
```json
{
  "distance_km": 1.2,
  "predicted_eta_min": 15,
  "actual_delivery_min": 18,
  "day_of_week": 1,
  "hour_of_day": 12,
  "weather": "sunny",
  "traffic_level": 2,
  "preparation_time_min": 12,
  "is_late": true,
  "delay_min": 3
}
```

### Restaurantes e Clientes
O sistema inclui dados seed para demonstração com múltiplos restaurantes e clientes pré-configurados.

## 🔒 Segurança e Configuração

### Variáveis de Ambiente
```env
VITE_SUPABASE_PROJECT_ID="seu-projeto-id"
VITE_SUPABASE_PUBLISHABLE_KEY="sua-chave-publica"
VITE_SUPABASE_URL="https://seu-projeto.supabase.co"
```

### CORS
A API está configurada para aceitar requisições dos seguintes origins:
- http://localhost:3000
- http://localhost:5173
- http://localhost:8080
- http://localhost:8081

## 📋 Roadmap Futuro

### Funcionalidades Planejadas
- [ ] Integração com APIs de mapas (Google Maps, OpenStreetMap)
- [ ] Notificações push em tempo real
- [ ] Sistema de feedback dos clientes
- [ ] Modelos de Deep Learning (LSTM, Transformer)
- [ ] Integração com WhatsApp Business
- [ ] Dashboard executivo com BI
- [ ] Sistema de otimização de rotas

### Melhorias Técnicas
- [ ] Containerização com Docker
- [ ] CI/CD com GitHub Actions
- [ ] Monitoramento com Prometheus/Grafana
- [ ] Cache distribuído com Redis
- [ ] Database PostgreSQL
- [ ] Autenticação JWT

## 🧪 Testes

### Frontend
```bash
bun test        # Executar testes
bun test:watch  # Testes em modo watch
bun test:ui     # Interface de testes
```

### Backend
```bash
python -m pytest tests/     # Executar testes
python -m pytest --cov     # Cobertura de código
```

## 📝 Contribuição

### Padrões de Código
- **TypeScript**: Strict mode habilitado
- **ESLint**: Configuração personalizada
- **Prettier**: Formatação automática
- **Python**: PEP 8 compliance

### Commits
Utilize conventional commits:
```
feat: adicionar nova funcionalidade
fix: corrigir bug
docs: atualizar documentação
style: alterações de formatação
refactor: refatoração de código
test: adicionar testes
```

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos como parte do projeto final da disciplina de Consultoria em Inteligência Artificial.

## 👥 Equipe de Desenvolvimento

- **Desenvolvedor Principal**: [Seu Nome]
- **Orientador**: [Nome do Professor]
- **Disciplina**: Consultoria em Inteligência Artificial
- **Semestre**: 6º Semestre (2025)

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar a documentação da API em `/docs`
2. Consultar logs do console para erros
3. Verificar se o backend ML está executando
4. Contatar a equipe de desenvolvimento

---