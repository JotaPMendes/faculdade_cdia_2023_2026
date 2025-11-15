from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import os
import sys
import json
import glob
from datetime import datetime

# Adicionar o diretório atual ao path para importar nossos módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from eta_predictor import get_eta_predictor
    from analytics import DeliveryAnalytics
except ImportError as e:
    print(f"⚠️ Erro na importação: {e}")
    print("📦 Instale as dependências com: pip install -r requirements.txt")

app = FastAPI(
    title="ETA Prediction API",
    description="API de Machine Learning para predição de tempo de entrega",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para validação de dados
class PredictionRequest(BaseModel):
    distance_km: float
    day_of_week: int  # 0-6 (domingo-sábado)
    hour_of_day: int  # 0-23
    weather: str  # 'sunny', 'cloudy', 'rainy'
    traffic_level: int  # 1-3
    preparation_time_min: int

class PredictionResponse(BaseModel):
    eta_minutes: int
    confidence: int
    risk_factors: List[str]
    model_used: str
    timestamp: str

class ModelMetrics(BaseModel):
    accuracy: float
    mae: float
    rmse: float
    r2_score: float
    late_percentage: float
    total_predictions: int
    model_name: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    message: str

# Instância global do preditor (carregada uma vez)
predictor = None

def get_predictor():
    """Obtém ou carrega o preditor"""
    global predictor
    if predictor is None:
        try:
            predictor = get_eta_predictor()
            return predictor
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Erro ao carregar modelo ML: {str(e)}"
            )
    return predictor

@app.get("/", response_model=Dict)
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "🚀 ETA Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "metrics": "/metrics",
            "health": "/health",
            "analytics": "/analytics"
        },
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica o status da API e do modelo"""
    try:
        predictor = get_predictor()
        return HealthResponse(
            status="healthy",
            model_loaded=predictor.is_trained,
            message="API funcionando corretamente"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            message=f"Erro: {str(e)}"
        )

@app.post("/predict", response_model=PredictionResponse)
async def predict_eta(request: PredictionRequest):
    """
    Prediz o tempo de entrega (ETA) baseado nas condições fornecidas
    """
    try:
        # Validações básicas
        if not (0 <= request.day_of_week <= 6):
            raise HTTPException(status_code=400, detail="day_of_week deve estar entre 0-6")
        
        if not (0 <= request.hour_of_day <= 23):
            raise HTTPException(status_code=400, detail="hour_of_day deve estar entre 0-23")
        
        if request.weather not in ['sunny', 'cloudy', 'rainy']:
            raise HTTPException(status_code=400, detail="weather deve ser 'sunny', 'cloudy' ou 'rainy'")
        
        if not (1 <= request.traffic_level <= 3):
            raise HTTPException(status_code=400, detail="traffic_level deve estar entre 1-3")
        
        if request.distance_km <= 0:
            raise HTTPException(status_code=400, detail="distance_km deve ser positiva")
        
        if request.preparation_time_min <= 0:
            raise HTTPException(status_code=400, detail="preparation_time_min deve ser positivo")
        
        # Obter preditor
        predictor = get_predictor()
        
        # Converter request para dict
        input_data = request.dict()
        
        # Fazer predição
        result = predictor.predict_eta(input_data)
        
        # Adicionar timestamp
        from datetime import datetime
        result['timestamp'] = datetime.now().isoformat()
        
        return PredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno na predição: {str(e)}"
        )

@app.get("/metrics", response_model=ModelMetrics)
async def get_model_metrics():
    """
    Retorna métricas de performance do modelo ML
    """
    try:
        predictor = get_predictor()
        metrics = predictor.get_model_metrics()
        
        if not metrics:
            raise HTTPException(
                status_code=503, 
                detail="Métricas não disponíveis - modelo não treinado"
            )
        
        return ModelMetrics(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter métricas: {str(e)}"
        )

@app.get("/analytics")
async def get_analytics():
    """
    Retorna análises detalhadas dos dados de entrega
    """
    try:
        analytics = DeliveryAnalytics()
        
        if analytics.df.empty:
            return {
                "error": "Dados não encontrados",
                "message": "Verifique se o arquivo de dados históricos existe"
            }
        
        # Gerar análises
        insights = analytics.generate_insights()
        patterns = analytics.analyze_delivery_patterns()
        anomalies = analytics.detect_anomalies()
        correlations = analytics.correlation_analysis()
        
        return {
            "insights": insights,
            "patterns": patterns,
            "anomalies_count": len(anomalies),
            "correlations": correlations,
            "data_summary": {
                "total_records": len(analytics.df),
                "date_range": "Dados simulados",
                "avg_delivery_time": round(analytics.df['actual_delivery_min'].mean(), 1),
                "late_rate": round((analytics.df['is_late'].sum() / len(analytics.df)) * 100, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar análises: {str(e)}"
        )

@app.post("/retrain")
async def retrain_model():
    """
    Retreina o modelo com dados atualizados
    """
    try:
        global predictor
        
        # Recarregar dados e retreinar
        predictor = None  # Força recriação
        predictor = get_predictor()
        
        # Obter métricas do novo modelo
        metrics = predictor.get_model_metrics()
        
        from datetime import datetime
        return {
            "message": "Modelo retreinado com sucesso",
            "new_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao retreinar modelo: {str(e)}"
        )

@app.get("/risk-factors")
async def get_risk_factors_info():
    """
    Retorna informações sobre os fatores de risco considerados
    """
    return {
        "risk_factors": {
            "distance": {
                "description": "Distância longa (>3.5km)",
                "threshold": 3.5,
                "impact": "Alto"
            },
            "traffic": {
                "description": "Trânsito intenso (nível 3)",
                "threshold": 3,
                "impact": "Alto"
            },
            "weather": {
                "description": "Condições climáticas adversas (chuva)",
                "condition": "rainy",
                "impact": "Médio"
            },
            "rush_hour": {
                "description": "Horários de pico (12-14h, 18-20h)",
                "periods": ["12:00-14:00", "18:00-20:00"],
                "impact": "Alto"
            },
            "prep_time": {
                "description": "Tempo de preparo elevado (>20 min)",
                "threshold": 20,
                "impact": "Médio"
            },
            "weekend": {
                "description": "Final de semana (sexta/sábado)",
                "days": [5, 6],
                "impact": "Baixo"
            }
        }
    }

# Endpoint para testar predição com dados de exemplo
@app.get("/predict/example")
async def predict_example():
    """
    Faz uma predição com dados de exemplo
    """
    example_data = PredictionRequest(
        distance_km=2.5,
        day_of_week=1,  # Segunda-feira
        hour_of_day=19,  # 19h (horário de pico)
        weather="rainy",
        traffic_level=3,
        preparation_time_min=15
    )
    
    return await predict_eta(example_data)

# Novos endpoints para treinamento
@app.post("/training/upload")
async def upload_training_data(data: dict):
    """Endpoint para receber dados de treinamento do frontend"""
    try:
        orders = data.get('orders', [])
        ml_logs = data.get('ml_logs', [])
        
        # Salva dados em arquivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_data_{timestamp}.json"
        filepath = f"data/{filename}"
        
        # Cria pasta data se não existir
        os.makedirs("data", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'orders': orders,
                'ml_logs': ml_logs,
                'collected_at': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "message": f"Dados salvos em {filepath}",
            "orders_count": len(orders),
            "ml_logs_count": len(ml_logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/retrain")
async def retrain_model():
    """Retreina o modelo com dados coletados"""
    try:
        from model_trainer import retrain_model_with_data
        
        # Carrega todos os arquivos de dados
        data_files = glob.glob("data/training_data_*.json")
        
        all_logs = []
        for file in data_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_logs.extend(data.get('ml_logs', []))
        
        if len(all_logs) < 5:  # Mínimo reduzido para teste
            return {
                "status": "error",
                "message": f"Não há dados suficientes para treinar. Mínimo: 5, Atual: {len(all_logs)}"
            }
        
        # Treina novo modelo
        accuracy = retrain_model_with_data(all_logs)
        
        return {
            "status": "success",
            "message": "Modelo retreinado com sucesso",
            "new_accuracy": round(accuracy, 3),
            "training_samples": len(all_logs)
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Erro ao retreinar modelo: {str(e)}"
        }

@app.get("/training/status")
async def get_training_status():
    """Retorna status dos dados de treinamento"""
    try:
        data_files = glob.glob("data/training_data_*.json")
        
        total_orders = 0
        total_logs = 0
        
        for file in data_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_orders += len(data.get('orders', []))
                total_logs += len(data.get('ml_logs', []))
        
        # Verifica se existe modelo retreinado
        retrained_model_exists = os.path.exists("models/eta_model_retrained.pkl")
        
        return {
            "data_files_count": len(data_files),
            "total_orders": total_orders,
            "total_logs": total_logs,
            "ready_for_training": total_logs >= 5,
            "retrained_model_exists": retrained_model_exists
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Iniciando servidor da API...")
    print("📖 Documentação disponível em: http://localhost:8000/docs")
    print("⚡ API rodando em: http://localhost:8000")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )