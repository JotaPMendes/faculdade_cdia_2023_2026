/**
 * Cliente para comunicação com a API Python de ML
 */

export interface PredictionRequest {
  distance_km: number;
  day_of_week: number; // 0-6 (domingo-sábado)
  hour_of_day: number; // 0-23
  weather: string; // 'sunny', 'cloudy', 'rainy'
  traffic_level: number; // 1-3
  preparation_time_min: number;
}

export interface PredictionResponse {
  eta_minutes: number;
  confidence: number;
  risk_factors: string[];
  model_used: string;
  timestamp: string;
}

class MLApiClient {
  private baseUrl: string;
  private isServerRunning: boolean = false;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Verifica se o servidor Python está rodando
   */
  async checkServerHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Timeout de 3 segundos
        signal: AbortSignal.timeout(3000),
      });

      if (response.ok) {
        this.isServerRunning = true;
        return true;
      }
      
      this.isServerRunning = false;
      return false;
    } catch (error) {
      console.warn('🐍 Servidor Python não está rodando:', error);
      this.isServerRunning = false;
      return false;
    }
  }

  /**
   * Faz predição de ETA usando o modelo Python
   */
  async predictETA(request: PredictionRequest): Promise<PredictionResponse | null> {
    try {
      const isHealthy = await this.checkServerHealth();
      if (!isHealthy) {
        console.warn('⚠️ Servidor Python indisponível - usando fallback');
        return this.fallbackPrediction(request);
      }

      const response = await fetch(`${this.baseUrl}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro na predição');
      }

      const prediction: PredictionResponse = await response.json();
      return prediction;

    } catch (error) {
      console.error('Erro na predição ML:', error);
      // Fallback para predição local
      return this.fallbackPrediction(request);
    }
  }

  /**
   * Predição de fallback quando servidor Python não está disponível
   */
  private fallbackPrediction(request: PredictionRequest): PredictionResponse {
    console.log('🔄 Usando predição de fallback (JavaScript)');
    
    // Algoritmo simples de fallback
    let baseETA = request.preparation_time_min + (request.distance_km * 8);

    // Ajustes baseados em condições
    if ((request.hour_of_day >= 12 && request.hour_of_day <= 14) || 
        (request.hour_of_day >= 18 && request.hour_of_day <= 20)) {
      baseETA *= 1.3; // Rush hour
    }

    if (request.weather === 'rainy') {
      baseETA *= 1.2;
    }

    if (request.traffic_level === 3) {
      baseETA *= 1.25;
    }

    if (request.day_of_week === 0 || request.day_of_week === 6) {
      baseETA *= 1.1; // Weekend
    }

    // Calcular fatores de risco
    const riskFactors: string[] = [];
    
    if (request.distance_km > 3.5) {
      riskFactors.push('🚗 Distância longa (>3.5km)');
    }
    
    if (request.traffic_level >= 3) {
      riskFactors.push('🚦 Trânsito intenso');
    }
    
    if (request.weather === 'rainy') {
      riskFactors.push('🌧️ Condições climáticas adversas');
    }
    
    if ((request.hour_of_day >= 12 && request.hour_of_day <= 14) || 
        (request.hour_of_day >= 18 && request.hour_of_day <= 20)) {
      riskFactors.push('⏰ Horário de pico');
    }
    
    if (request.preparation_time_min > 20) {
      riskFactors.push('👨‍🍳 Tempo de preparo elevado');
    }

    const confidence = Math.max(60, 95 - riskFactors.length * 10);

    return {
      eta_minutes: Math.max(5, Math.round(baseETA)),
      confidence,
      risk_factors: riskFactors,
      model_used: 'JavaScript Fallback',
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Verifica se o servidor está rodando
   */
  isServerOnline(): boolean {
    return this.isServerRunning;
  }
}

// Singleton instance
let mlApiClient: MLApiClient | null = null;

export function getMLApiClient(): MLApiClient {
  if (!mlApiClient) {
    mlApiClient = new MLApiClient();
  }
  return mlApiClient;
}

export default MLApiClient;