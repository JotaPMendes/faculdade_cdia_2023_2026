import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Upload, 
  Zap, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  BarChart3, 
  Database,
  Clock,
  TrendingUp,
  Wifi,
  WifiOff,
  RefreshCw,
  Target,
  Dice6
} from 'lucide-react';
import { mlDataSync, TrainingStatus } from '../lib/ml-data-sync';
import { localDB } from '../lib/local-storage';
import { useToast } from '../hooks/use-toast';
import { ETAPredictor } from './ETAPredictor';

interface MLSyncManagerProps {
  restaurantId: string;
}

export const MLSyncManager: React.FC<MLSyncManagerProps> = ({ restaurantId }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [serverStatus, setServerStatus] = useState<TrainingStatus | null>(null);
  const [isAPIOnline, setIsAPIOnline] = useState(false);
  const [localStats, setLocalStats] = useState(mlDataSync.getLocalStats(restaurantId));
  
  const { toast } = useToast();

  // Carrega status inicial
  useEffect(() => {
    checkAPIStatus();
    refreshLocalStats();
  }, [restaurantId]);

  const checkAPIStatus = async () => {
    const isOnline = await mlDataSync.checkAPIHealth();
    setIsAPIOnline(isOnline);
    
    if (isOnline) {
      const status = await mlDataSync.getTrainingStatus();
      setServerStatus(status);
    }
  };

  const refreshLocalStats = () => {
    setLocalStats(mlDataSync.getLocalStats(restaurantId));
  };

  const handleUpload = async () => {
    setIsUploading(true);
    try {
      const result = await mlDataSync.uploadTrainingData(restaurantId);
      
      if (result.status === 'success') {
        toast({
          title: "Upload realizado!",
          description: `${result.orders_count} pedidos e ${result.ml_logs_count} logs enviados`,
          variant: "default"
        });
        setLastSync(new Date().toLocaleString('pt-BR'));
        await checkAPIStatus(); // Atualiza status do servidor
      } else {
        toast({
          title: "Erro no upload",
          description: result.message,
          variant: "destructive"
        });
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleRetrain = async () => {
    setIsRetraining(true);
    try {
      const result = await mlDataSync.triggerRetrain();
      
      if (result.status === 'success') {
        toast({
          title: "Modelo retreinado!",
          description: `Nova acurácia: ${(result.new_accuracy! * 100).toFixed(1)}% com ${result.training_samples} amostras`,
          variant: "default"
        });
        await checkAPIStatus(); // Atualiza status do servidor
      } else {
        toast({
          title: "Erro no retreinamento",
          description: result.message,
          variant: "destructive"
        });
      }
    } finally {
      setIsRetraining(false);
    }
  };

  const handleAutoSync = async () => {
    setIsUploading(true);
    setIsRetraining(true);
    try {
      const results = await mlDataSync.autoSync();
      
      if (results.upload.status === 'success') {
        if (results.retrain?.status === 'success') {
          toast({
            title: "Sincronização completa!",
            description: `Dados enviados e modelo retreinado. Nova acurácia: ${(results.retrain.new_accuracy! * 100).toFixed(1)}%`,
            variant: "default"
          });
        } else {
          toast({
            title: "Upload OK, erro no treino",
            description: results.retrain?.message || "Erro desconhecido",
            variant: "destructive"
          });
        }
        setLastSync(new Date().toLocaleString('pt-BR'));
        await checkAPIStatus();
      } else {
        toast({
          title: "Erro na sincronização",
          description: results.upload.message,
          variant: "destructive"
        });
      }
    } finally {
      setIsUploading(false);
      setIsRetraining(false);
    }
  };

  const handleGenerateSample = async () => {
    setIsGenerating(true);
    try {
      const success = await mlDataSync.generateSampleData();
      
      if (success) {
        toast({
          title: "Dados gerados!",
          description: "Alguns pedidos foram marcados como entregues para gerar dados ML",
          variant: "default"
        });
        refreshLocalStats();
      } else {
        toast({
          title: "Erro ao gerar dados",
          description: "Não há pedidos suficientes para converter. Crie alguns pedidos primeiro.",
          variant: "destructive"
        });
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const getStatusBadge = () => {
    if (!isAPIOnline) {
      return (
        <Badge variant="destructive" className="gap-1">
          <WifiOff className="w-3 h-3" />
          API Offline
        </Badge>
      );
    }
    
    if (localStats.readyForTraining) {
      return (
        <Badge variant="default" className="bg-green-100 text-green-800 gap-1">
          <CheckCircle className="w-3 h-3" />
          Pronto para treinar
        </Badge>
      );
    }
    
    return (
      <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 gap-1">
        <AlertCircle className="w-3 h-3" />
        Precisa de mais dados
      </Badge>
    );
  };

  const progressValue = Math.min(100, (localStats.mlLogs / 10) * 100);

  return (
    <div className="space-y-6">
      {/* Preditor de ETA */}
      <ETAPredictor restaurantId={restaurantId} />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                Sincronização de Machine Learning
              </CardTitle>
              <CardDescription>
                Gerencie dados de treinamento e melhore as predições de ETA
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge()}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={checkAPIStatus}
                className="gap-2"
              >
                <RefreshCw className="w-3 h-3" />
                Atualizar
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Estatísticas Locais */}
          <div>
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Dados Locais
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg border">
                <p className="text-2xl font-bold text-blue-600">{localStats.deliveredOrders}</p>
                <p className="text-xs text-blue-800">Pedidos Entregues</p>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg border">
                <p className="text-2xl font-bold text-green-600">{localStats.mlLogs}</p>
                <p className="text-xs text-green-800">Logs ML</p>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg border">
                <p className="text-2xl font-bold text-purple-600">{localStats.accuracyRate}%</p>
                <p className="text-xs text-purple-800">Precisão</p>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded-lg border">
                <p className="text-2xl font-bold text-orange-600">{localStats.avgDeliveryTime}min</p>
                <p className="text-xs text-orange-800">Tempo Médio</p>
              </div>
            </div>
          </div>

          {/* Progress para dados de treinamento */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Progresso para treinamento:</span>
              <span className="text-sm text-muted-foreground">{localStats.mlLogs}/10 amostras</span>
            </div>
            <Progress value={progressValue} className="h-2" />
            {!localStats.readyForTraining && (
              <p className="text-xs text-muted-foreground mt-1">
                Precisamos de pelo menos 10 pedidos entregues para treinar o modelo
              </p>
            )}
          </div>

          {/* Status do Servidor */}
          {isAPIOnline && serverStatus && (
            <div>
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Wifi className="w-4 h-4" />
                Status do Servidor
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="text-center p-3 bg-slate-50 rounded-lg border">
                  <p className="text-xl font-bold text-slate-600">{serverStatus.total_orders}</p>
                  <p className="text-xs text-slate-800">Pedidos no Servidor</p>
                </div>
                <div className="text-center p-3 bg-indigo-50 rounded-lg border">
                  <p className="text-xl font-bold text-indigo-600">{serverStatus.total_logs}</p>
                  <p className="text-xs text-indigo-800">Logs no Servidor</p>
                </div>
                <div className="text-center p-3 bg-emerald-50 rounded-lg border">
                  <p className="text-xl font-bold text-emerald-600">
                    {serverStatus.retrained_model_exists ? '✅' : '❌'}
                  </p>
                  <p className="text-xs text-emerald-800">Modelo Retreinado</p>
                </div>
              </div>
            </div>
          )}

          {/* Informações de sincronização */}
          {lastSync && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                Última sincronização: {lastSync}
              </AlertDescription>
            </Alert>
          )}

          {/* Ações */}
          <div className="flex flex-wrap gap-3">
            <Button 
              onClick={handleUpload}
              disabled={isUploading || localStats.deliveredOrders === 0 || !isAPIOnline}
              className="flex items-center gap-2"
            >
              {isUploading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              {isUploading ? 'Enviando...' : 'Enviar Dados'}
            </Button>
            
            <Button 
              onClick={handleRetrain}
              disabled={isRetraining || !localStats.readyForTraining || !isAPIOnline}
              variant="outline"
              className="flex items-center gap-2"
            >
              {isRetraining ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              {isRetraining ? 'Treinando...' : 'Retreinar Modelo'}
            </Button>
            
            <Button 
              onClick={handleAutoSync}
              disabled={isUploading || isRetraining || localStats.deliveredOrders === 0 || !isAPIOnline}
              variant="secondary"
              className="flex items-center gap-2"
            >
              {(isUploading || isRetraining) ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Target className="w-4 h-4" />
              )}
              Sincronizar Tudo
            </Button>

            <Button 
              onClick={handleGenerateSample}
              disabled={isGenerating || localStats.totalOrders === 0}
              variant="outline"
              className="flex items-center gap-2"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Dice6 className="w-4 h-4" />
              )}
              Gerar Dados Teste
            </Button>
          </div>

          {/* Alertas informativos */}
          {!isAPIOnline && (
            <Alert variant="destructive">
              <WifiOff className="h-4 w-4" />
              <AlertDescription>
                API Python offline. Execute: <code>cd ml_system && python api.py</code>
              </AlertDescription>
            </Alert>
          )}

          {localStats.deliveredOrders === 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Crie alguns pedidos e marque como "entregues" para gerar dados de treinamento.
                Ou use "Gerar Dados Teste" para simular entregas.
              </AlertDescription>
            </Alert>
          )}

          {localStats.readyForTraining && isAPIOnline && (
            <Alert>
              <TrendingUp className="h-4 w-4" />
              <AlertDescription>
                🎉 Você tem dados suficientes! Use "Sincronizar Tudo" para treinar um modelo personalizado.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};