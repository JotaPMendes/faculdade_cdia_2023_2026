/**
 * Cliente para sincronização de dados ML entre localStorage e API Python
 */

import { localDB } from './local-storage';

export interface TrainingStatus {
  data_files_count: number;
  total_orders: number;
  total_logs: number;
  ready_for_training: boolean;
  retrained_model_exists: boolean;
}

export interface UploadResponse {
  status: 'success' | 'error';
  message: string;
  orders_count?: number;
  ml_logs_count?: number;
}

export interface RetrainResponse {
  status: 'success' | 'error';
  message: string;
  new_accuracy?: number;
  training_samples?: number;
}

class MLDataSync {
  private apiUrl: string;

  constructor(apiUrl: string = 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }

  /**
   * Verifica se a API Python está disponível
   */
  async checkAPIHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Obtém status dos dados de treinamento no servidor
   */
  async getTrainingStatus(): Promise<TrainingStatus | null> {
    try {
      const response = await fetch(`${this.apiUrl}/training/status`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        return await response.json();
      }
      
      console.error('Erro ao obter status:', response.statusText);
      return null;
    } catch (error) {
      console.error('Erro ao conectar com API:', error);
      return null;
    }
  }

  /**
   * Envia dados de treinamento para o servidor Python
   */
  async uploadTrainingData(restaurantId?: string): Promise<UploadResponse> {
    try {
      // Verifica se API está disponível
      const isHealthy = await this.checkAPIHealth();
      if (!isHealthy) {
        return {
          status: 'error',
          message: 'Servidor Python indisponível. Verifique se está rodando em localhost:8000'
        };
      }

      // Exporta dados do localStorage
      const data = localDB.exportData();
      
      // Filtra apenas pedidos entregues (que têm dados úteis para ML)
      let deliveredOrders = data.orders.filter(order => 
        order.status === 'delivered' && 
        order.actual_delivery_min && 
        order.predicted_eta_min
      );

      // Filtra logs ML válidos
      let validMLLogs = data.mlLogs.filter(log => 
        log.actual_delivery_min > 0 &&
        log.distance_km > 0 &&
        log.item_count > 0
      );

      // Se restaurantId foi fornecido, filtra por restaurante
      if (restaurantId) {
        deliveredOrders = deliveredOrders.filter(order => order.restaurant_id === restaurantId);
        validMLLogs = validMLLogs.filter(log => log.restaurant_id === restaurantId);
      }

      if (deliveredOrders.length === 0 && validMLLogs.length === 0) {
        return {
          status: 'error',
          message: 'Nenhum dado válido para enviar. Crie alguns pedidos e marque como entregues.'
        };
      }

      console.log(`📤 Enviando ${deliveredOrders.length} pedidos e ${validMLLogs.length} logs ML...`);

      const response = await fetch(`${this.apiUrl}/training/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orders: deliveredOrders,
          ml_logs: validMLLogs
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Dados enviados com sucesso:', result);
        return result;
      } else {
        const error = await response.json();
        console.error('❌ Erro ao enviar dados:', error);
        return {
          status: 'error',
          message: error.detail || 'Erro desconhecido ao enviar dados'
        };
      }

    } catch (error) {
      console.error('❌ Erro na comunicação:', error);
      return {
        status: 'error',
        message: `Erro de conexão: ${error instanceof Error ? error.message : 'Erro desconhecido'}`
      };
    }
  }

  /**
   * Solicita retreinamento do modelo
   */
  async triggerRetrain(): Promise<RetrainResponse> {
    try {
      console.log('🔄 Solicitando retreinamento do modelo...');

      const response = await fetch(`${this.apiUrl}/training/retrain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();

      if (response.ok && result.status === 'success') {
        console.log('✅ Modelo retreinado com sucesso:', result);
        return result;
      } else {
        console.error('❌ Erro no retreinamento:', result);
        return result;
      }

    } catch (error) {
      console.error('❌ Erro ao retreinar:', error);
      return {
        status: 'error',
        message: `Erro de conexão: ${error instanceof Error ? error.message : 'Erro desconhecido'}`
      };
    }
  }

  /**
   * Sincronização automática completa: upload + retrain
   */
  async autoSync(): Promise<{
    upload: UploadResponse;
    retrain?: RetrainResponse;
  }> {
    console.log('🚀 Iniciando sincronização automática...');

    // 1. Upload dos dados
    const uploadResult = await this.uploadTrainingData();
    
    if (uploadResult.status !== 'success') {
      return { upload: uploadResult };
    }

    // 2. Aguarda um pouco antes de retreinar
    await new Promise(resolve => setTimeout(resolve, 1500));

    // 3. Retreina o modelo
    const retrainResult = await this.triggerRetrain();

    return {
      upload: uploadResult,
      retrain: retrainResult
    };
  }

  /**
   * Obtém estatísticas locais dos dados
   */
  getLocalStats(restaurantId?: string) {
    const data = localDB.exportData();
    
    // Filtra pedidos por restaurante se especificado
    const filteredOrders = restaurantId 
      ? data.orders.filter(o => o.restaurant_id === restaurantId)
      : data.orders;
    
    // Filtra logs ML por restaurante se especificado
    const filteredMLLogs = restaurantId
      ? data.mlLogs.filter(log => log.restaurant_id === restaurantId)
      : data.mlLogs;
    
    const deliveredOrders = filteredOrders.filter(o => o.status === 'delivered');
    const validMLLogs = filteredMLLogs.filter(log => 
      log.actual_delivery_min > 0 && log.distance_km > 0
    );

    const accuratePredictions = validMLLogs.filter(log => 
      Math.abs(log.actual_delivery_min - log.predicted_eta_min) <= 5
    );

    const lateDeliveries = validMLLogs.filter(log => log.is_late);

    return {
      totalOrders: filteredOrders.length,
      deliveredOrders: deliveredOrders.length,
      preparingOrders: filteredOrders.filter(o => o.status === 'preparing').length,
      inRouteOrders: filteredOrders.filter(o => o.status === 'in_route').length,
      cancelledOrders: filteredOrders.filter(o => o.status === 'cancelled').length,
      mlLogs: validMLLogs.length,
      accuratePredictions: accuratePredictions.length,
      accuracyRate: validMLLogs.length > 0 
        ? Math.round((accuratePredictions.length / validMLLogs.length) * 100)
        : 0,
      lateDeliveries: lateDeliveries.length,
      onTimeRate: validMLLogs.length > 0 
        ? Math.round(((validMLLogs.length - lateDeliveries.length) / validMLLogs.length) * 100)
        : 0,
      avgDeliveryTime: validMLLogs.length > 0
        ? Math.round(validMLLogs.reduce((sum, log) => sum + log.actual_delivery_min, 0) / validMLLogs.length)
        : 0,
      readyForTraining: validMLLogs.length >= 5
    };
  }

  /**
   * Gera dados de exemplo para teste
   */
  async generateSampleData(): Promise<boolean> {
    try {
      console.log('🎲 Gerando dados de exemplo...');
      
      // Simula algumas entregas para gerar logs ML
      const orders = localDB.getOrders();
      const preparingOrders = orders.filter(o => o.status === 'preparing').slice(0, 5);
      
      if (preparingOrders.length === 0) {
        console.log('⚠️ Nenhum pedido preparando encontrado. Crie alguns pedidos primeiro.');
        return false;
      }
      
      for (let i = 0; i < preparingOrders.length; i++) {
        const order = preparingOrders[i];
        
        // Simula tempo de entrega real
        const predictedTime = order.predicted_eta_min || 30;
        const variation = (Math.random() - 0.5) * 20; // ±10 min
        const actualTime = Math.max(10, Math.round(predictedTime + variation));
        
        // Atualiza o pedido com tempo real antes de marcar como entregue
        const updatedOrder = { ...order };
        updatedOrder.actual_delivery_min = actualTime;
        localDB.saveOrder(updatedOrder);
        
        // Marca como entregue (isso criará automaticamente o log ML)
        localDB.updateOrderStatus(order.id, 'delivered');
      }
      
      console.log('✅ Dados de exemplo gerados com sucesso!');
      return true;
      
    } catch (error) {
      console.error('❌ Erro ao gerar dados de exemplo:', error);
      return false;
    }
  }
}

// Singleton instance
let mlDataSyncInstance: MLDataSync | null = null;

export function getMLDataSync(): MLDataSync {
  if (!mlDataSyncInstance) {
    mlDataSyncInstance = new MLDataSync();
  }
  return mlDataSyncInstance;
}

export const mlDataSync = getMLDataSync();
export default MLDataSync;