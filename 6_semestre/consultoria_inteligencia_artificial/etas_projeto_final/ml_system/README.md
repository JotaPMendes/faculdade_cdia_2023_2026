# 🧠 Quick Delivery Watch - Sistema de Machine Learning

Sistema avançado de Machine Learning em Python para predição de tempo de entrega (ETA) com análises em tempo real.

## 🎯 Funcionalidades

### 🤖 Modelo de ML
- **Algoritmo**: Regressão Linear + Random Forest
- **Features**: distância, horário, clima, trânsito, tempo de preparo
- **Precisão**: ~80-85% (±3 minutos)
- **Treinamento**: Automático com dados históricos

### 📊 Análises Avançadas
- Detecção de anomalias em entregas
- Correlação entre variáveis
- Padrões temporais e sazonais
- Insights automáticos

### 🚀 API REST
- **FastAPI** com documentação automática
- Endpoints para predição, métricas e análises
- CORS configurado para frontend
- Validação de dados com Pydantic

## 📁 Estrutura

```
ml_system/
├── requirements.txt      # Dependências Python
├── eta_predictor.py     # Modelo principal de ML
├── analytics.py         # Análises e métricas
├── api.py              # API FastAPI
└── README.md           # Este arquivo
```

## 🛠️ Instalação

### Opção 1: Script Automático
```bash
./setup_ml.sh
```

### Opção 2: Manual
```bash
cd ml_system/

# Criar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

## 🚀 Execução

### 1. Iniciar API
```bash
cd ml_system/
python api.py
```

A API estará disponível em:
- **Servidor**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Interface**: http://localhost:8000/redoc

### 2. Verificar Status
```bash
curl http://localhost:8000/health
```

### 3. Testar Predição
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "distance_km": 2.5,
    "day_of_week": 1,
    "hour_of_day": 19,
    "weather": "rainy",
    "traffic_level": 3,
    "preparation_time_min": 15
  }'
```

## 📡 Endpoints da API

### Predição
- **POST** `/predict` - Prediz ETA para um pedido
- **GET** `/predict/example` - Exemplo de predição

### Métricas
- **GET** `/metrics` - Métricas do modelo (precisão, erro, etc.)
- **GET** `/analytics` - Análises detalhadas dos dados

### Administração
- **GET** `/health` - Status da API e modelo
- **POST** `/retrain` - Retreina o modelo
- **GET** `/risk-factors` - Info sobre fatores de risco

## 🎛️ Configuração

### Parâmetros do Modelo
```python
# eta_predictor.py
class ETAPredictor:
    def __init__(self, data_path: str = "../src/data/historical_deliveries.json"):
        # Configurações...
```

### CORS (Cross-Origin)
```python
# api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Integração com Frontend

O frontend TypeScript se conecta automaticamente à API Python:

```typescript
// src/lib/ml-api-client.ts
const mlClient = getMLApiClient();
const prediction = await mlClient.predictETA({
  distance_km: 2.5,
  // ... outros parâmetros
});
```

### Fallback
Se a API Python não estiver disponível, o sistema usa um algoritmo JavaScript simples como fallback.

## 🔬 Desenvolvimento

### Adicionar Novos Features
1. Modificar `feature_engineering()` em `eta_predictor.py`
2. Atualizar `PredictionRequest` em `api.py`
3. Retreinar o modelo

### Melhorar Precisão
1. Adicionar mais dados históricos
2. Usar algoritmos mais avançados (XGBoost, LightGBM)
3. Fazer feature engineering mais sofisticada

### Monitoramento
```python
# Verificar métricas
from eta_predictor import get_eta_predictor
predictor = get_eta_predictor()
metrics = predictor.get_model_metrics()
print(f"Precisão: {metrics['accuracy']}%")
```

## 🐛 Solução de Problemas

### Erro de Importação
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Porta em Uso
```python
# Mudar porta em api.py
uvicorn.run("api:app", host="0.0.0.0", port=8001)
```

### Dados Não Encontrados
O sistema cria dados sintéticos automaticamente se não encontrar `historical_deliveries.json`.

### CORS Error
Adicione sua URL do frontend nas origens permitidas em `api.py`.

## 📈 Métricas Típicas

- **Precisão**: 75-85% (±3 min)
- **MAE**: ~2.5 minutos
- **R²**: 0.7-0.8
- **Taxa de Atrasos**: ~35%

## 🔄 Ciclo de Vida

1. **Dados** → Coleta de dados históricos
2. **Treinamento** → Modelo treina automaticamente
3. **Predição** → API serve predições em tempo real
4. **Feedback** → Dados reais alimentam o sistema
5. **Retreinamento** → Modelo melhora continuamente

## 🎯 Roadmap

- [ ] Integração com APIs de clima/trânsito
- [ ] Modelos mais avançados (Deep Learning)
- [ ] A/B Testing para comparar modelos
- [ ] Deploy automático (Docker + CI/CD)
- [ ] Monitoramento de drift do modelo

## 📚 Dependências

```txt
numpy==1.24.3           # Computação numérica
pandas==2.0.3           # Manipulação de dados
scikit-learn==1.3.0     # Machine Learning
fastapi==0.103.1        # API framework
uvicorn==0.23.2         # ASGI server
pydantic==2.3.0         # Validação de dados
matplotlib==3.7.2       # Visualizações
seaborn==0.12.2         # Gráficos estatísticos
```

---

**Desenvolvido com ❤️ para otimizar entregas através de Inteligência Artificial**