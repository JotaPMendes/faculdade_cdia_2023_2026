import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Calculator, 
  Loader2, 
  Clock, 
  MapPin, 
  Calendar,
  Zap,
  Target,
  TrendingUp
} from 'lucide-react';
import { getMLApiClient } from '../lib/ml-api-client';
import { customers, getRestaurantById } from '../data/seed-data';
import { calculateDistance } from '../lib/haversine';
import { useToast } from '../hooks/use-toast';

interface ETAPredictorProps {
  restaurantId: string;
}

export const ETAPredictor: React.FC<ETAPredictorProps> = ({ restaurantId }) => {
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [customDistance, setCustomDistance] = useState('');
  const [useCustomDistance, setUseCustomDistance] = useState(false);
  const [itemCount, setItemCount] = useState('2');
  const [prepTime, setPrepTime] = useState('15');
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<{
    eta_minutes: number;
    confidence: number;
    risk_factors: string[];
    model_used: string;
    timestamp: string;
  } | null>(null);
  
  const { toast } = useToast();
  
  // Busca dados do restaurante logado
  const restaurant = getRestaurantById(restaurantId);

  const calculatePrediction = async () => {
    if (!restaurant || (!selectedCustomer && !useCustomDistance)) {
      toast({
        title: "Campos obrigatórios",
        description: "Selecione cliente (ou defina distância personalizada)",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    try {
      let distance: number;
      if (useCustomDistance) {
        distance = parseFloat(customDistance);
        if (isNaN(distance) || distance <= 0) {
          toast({
            title: "Distância inválida",
            description: "Digite uma distância válida em km",
            variant: "destructive"
          });
          return;
        }
      } else {
        const customer = customers.find(c => c.id === selectedCustomer);
        if (!restaurant || !customer) {
          throw new Error('Restaurante ou cliente não encontrado');
        }
        distance = calculateDistance(
          restaurant.lat, 
          restaurant.lon, 
          customer.lat, 
          customer.lon
        );
      }

      // Dados atuais
      const now = new Date();
      const hour = now.getHours();
      const dayOfWeek = now.getDay();
      
      // Simula condições (em produção viria de APIs)
      const weatherConditions = ['sunny', 'cloudy', 'rainy'];
      const currentWeather = weatherConditions[Math.floor(Math.random() * weatherConditions.length)];
      const trafficLevel = hour >= 18 && hour <= 20 ? 3 : hour >= 12 && hour <= 14 ? 2 : 1;

      const predictionRequest = {
        distance_km: distance,
        day_of_week: dayOfWeek,
        hour_of_day: hour,
        weather: currentWeather,
        traffic_level: trafficLevel,
        preparation_time_min: parseInt(prepTime)
      };

      console.log('🔮 Fazendo predição com:', predictionRequest);

      const mlClient = getMLApiClient();
      const result = await mlClient.predictETA(predictionRequest);
      
      if (result) {
        setPrediction(result);
        toast({
          title: "Predição realizada!",
          description: `ETA estimado: ${result.eta_minutes} minutos`,
          variant: "default"
        });
      } else {
        throw new Error('Erro na predição');
      }

    } catch (error) {
      console.error('Erro na predição:', error);
      toast({
        title: "Erro na predição",
        description: "Não foi possível calcular o ETA. Verifique se a API está rodando.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "text-green-600 bg-green-100";
    if (confidence >= 60) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getETAColor = (eta: number) => {
    if (eta <= 30) return "text-green-700";
    if (eta <= 45) return "text-orange-700";
    return "text-red-700";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="w-5 h-5" />
          Preditor de ETA
        </CardTitle>
        <CardDescription>
          Teste o modelo de Machine Learning com diferentes cenários
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Informações do Restaurante */}
        {restaurant && (
          <div className="p-3 bg-primary/5 rounded-lg border">
            <div className="flex items-center gap-2 mb-1">
              <MapPin className="w-4 h-4 text-primary" />
              <span className="font-medium">{restaurant.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Tempo médio de preparo: {restaurant.avg_prep_time_min} minutos
            </p>
          </div>
        )}

        {/* Toggle para distância personalizada */}
        <div className="flex items-center space-x-2">
          <input
            id="custom-distance"
            type="checkbox"
            checked={useCustomDistance}
            onChange={(e) => setUseCustomDistance(e.target.checked)}
            className="rounded border-gray-300"
          />
          <Label htmlFor="custom-distance" className="text-sm">
            Usar distância personalizada
          </Label>
        </div>

        {/* Seleção de Cliente OU Distância Personalizada */}
        {useCustomDistance ? (
          <div className="space-y-2">
            <Label htmlFor="custom-distance-input">Distância (km)</Label>
            <Input
              id="custom-distance-input"
              type="number"
              step="0.1"
              min="0.1"
              max="20"
              value={customDistance}
              onChange={(e) => setCustomDistance(e.target.value)}
              placeholder="Ex: 2.5"
            />
          </div>
        ) : (
          <div className="space-y-2">
            <Label htmlFor="customer">Cliente</Label>
            <Select value={selectedCustomer} onValueChange={setSelectedCustomer}>
              <SelectTrigger id="customer">
                <SelectValue placeholder="Selecione o cliente" />
              </SelectTrigger>
              <SelectContent>
                {customers.map((customer) => (
                  <SelectItem key={customer.id} value={customer.id}>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-3 h-3" />
                      {customer.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Parâmetros do pedido */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="items">Número de Itens</Label>
            <Input
              id="items"
              type="number"
              min="1"
              max="10"
              value={itemCount}
              onChange={(e) => setItemCount(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="prep-time">Tempo Preparo (min)</Label>
            <Input
              id="prep-time"
              type="number"
              min="5"
              max="60"
              value={prepTime}
              onChange={(e) => setPrepTime(e.target.value)}
            />
          </div>
        </div>

        {/* Informações automáticas */}
        <Alert>
          <Calendar className="h-4 w-4" />
          <AlertDescription>
            <strong>Condições atuais:</strong> {new Date().toLocaleString('pt-BR')}, 
            será considerado trânsito e clima aleatórios para simulação.
          </AlertDescription>
        </Alert>

        {/* Botão de predição */}
        <Button 
          onClick={calculatePrediction}
          disabled={isLoading}
          className="w-full gap-2"
          size="lg"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Target className="w-4 h-4" />
          )}
          {isLoading ? 'Calculando...' : 'Calcular ETA'}
        </Button>

        {/* Resultado da predição */}
        {prediction && (
          <div className="space-y-4 p-4 bg-slate-50 rounded-lg border">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Resultado da Predição
              </h3>
              <Badge variant="outline" className="text-xs">
                {prediction.model_used}
              </Badge>
            </div>

            {/* ETA Principal */}
            <div className="text-center p-4 bg-white rounded-lg border">
              <p className="text-3xl font-bold mb-1">
                <span className={getETAColor(prediction.eta_minutes)}>
                  {prediction.eta_minutes} min
                </span>
              </p>
              <p className="text-sm text-muted-foreground">Tempo Estimado de Entrega</p>
            </div>

            {/* Métricas */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-white rounded-lg border">
                <p className="text-xl font-bold">
                  <Badge className={getConfidenceColor(prediction.confidence)}>
                    {prediction.confidence}%
                  </Badge>
                </p>
                <p className="text-xs text-muted-foreground mt-1">Confiança</p>
              </div>
              <div className="text-center p-3 bg-white rounded-lg border">
                <p className="text-xl font-bold text-blue-600">
                  {prediction.risk_factors.length}
                </p>
                <p className="text-xs text-muted-foreground mt-1">Fatores de Risco</p>
              </div>
            </div>

            {/* Fatores de risco */}
            {prediction.risk_factors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Fatores que Afetam o Tempo:
                </h4>
                <div className="space-y-1">
                  {prediction.risk_factors.map((factor, index) => (
                    <Badge key={index} variant="outline" className="text-xs mr-2 mb-1">
                      {factor}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamp */}
            <p className="text-xs text-muted-foreground text-center">
              Calculado em: {new Date(prediction.timestamp).toLocaleString('pt-BR')}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};