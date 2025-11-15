from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import json
import random
from datetime import datetime

app = FastAPI(
    title="ETA Prediction API - Simplified",
    description="API simplificada de Machine Learning para predição de tempo de entrega",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
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

def simple_eta_predictor(request: PredictionRequest) -> PredictionResponse:
    """
    Algoritmo simplificado de predição de ETA
    """
    # Algoritmo base
    base_eta = request.preparation_time_min + (request.distance_km * 8)

    # Ajustes baseados em condições
    if (request.hour_of_day >= 12 and request.hour_of_day <= 14) or \
       (request.hour_of_day >= 18 and request.hour_of_day <= 20):
        base_eta *= 1.3  # Rush hour

    if request.weather == 'rainy':
        base_eta *= 1.2

    if request.traffic_level == 3:
        base_eta *= 1.25

    if request.day_of_week in [0, 6]:  # Weekend
        base_eta *= 1.1

    # Adicionar variação aleatória para simular modelo real
    variation = random.uniform(-0.1, 0.1)
    base_eta *= (1 + variation)

    # Calcular fatores de risco
    risk_factors = []
    
    if request.distance_km > 3.5:
        risk_factors.append('🚗 Distância longa (>3.5km)')
    
    if request.traffic_level >= 3:
        risk_factors.append('🚦 Trânsito intenso')
    
    if request.weather == 'rainy':
        risk_factors.append('🌧️ Condições climáticas adversas')
    
    if (request.hour_of_day >= 12 and request.hour_of_day <= 14) or \
       (request.hour_of_day >= 18 and request.hour_of_day <= 20):
        risk_factors.append('⏰ Horário de pico')
    
    if request.preparation_time_min > 20:
        risk_factors.append('👨‍🍳 Tempo de preparo elevado')

    if request.day_of_week in [5, 6]:  # Sexta/Sábado
        risk_factors.append('🎉 Final de semana (maior demanda)')

    # Calcular confiança
    confidence = max(60, 95 - len(risk_factors) * 8)

    return PredictionResponse(
        eta_minutes=max(5, int(round(base_eta))),
        confidence=confidence,
        risk_factors=risk_factors,
        model_used="Simplified Python Algorithm",
        timestamp=datetime.now().isoformat()
    )

@app.get("/", response_model=Dict)
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "🚀 ETA Prediction API (Simplified)",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "predict": "/predict",
            "metrics": "/metrics",
            "health": "/health"
        },
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica o status da API"""
    return HealthResponse(
        status="healthy",
        model_loaded=True,
        message="API simplificada funcionando corretamente"
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
        
        # Fazer predição
        result = simple_eta_predictor(request)
        return result
        
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
    Retorna métricas simuladas do modelo
    """
    return ModelMetrics(
        accuracy=78.5,
        mae=2.8,
        rmse=3.5,
        r2_score=0.73,
        late_percentage=32.1,
        total_predictions=150,
        model_name="Simplified Algorithm"
    )

@app.get("/analytics")
async def get_analytics():
    """
    Retorna análises simuladas
    """
    return {
        "insights": {
            "insights": [
                "📊 Modelo simplificado funcionando corretamente",
                "⏰ Horários de pico identificados: 12-14h e 18-20h",
                "🌧️ Clima adverso impacta em média +20% no tempo de entrega"
            ],
            "recommendations": [
                "Considere buffer extra para dias chuvosos",
                "Otimize rotas nos horários de pico"
            ]
        },
        "data_summary": {
            "total_records": 150,
            "avg_delivery_time": 24.5,
            "late_rate": 32.1
        },
        "anomalies_count": 8
    }

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

if __name__ == "__main__":
    print("🚀 Iniciando servidor da API Simplificada...")
    print("📖 Documentação disponível em: http://localhost:8000/docs")
    print("⚡ API rodando em: http://localhost:8000")
    
    uvicorn.run(
        "api_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )