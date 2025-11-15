/**
 * Sistema de armazenamento local para pedidos e dados de ML
 */

export interface Order {
  id: string;
  customer_id: string;
  restaurant_id: string;
  status: 'preparing' | 'in_route' | 'delivered' | 'cancelled';
  predicted_eta_min: number | null;
  actual_delivery_min: number | null;
  distance_km: number | null;
  created_at: string;
  delivered_at: string | null;
  items: OrderItem[];
  total_amount: number;
}

export interface OrderItem {
  id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
}

export interface MLTrainingLog {
  id: string;
  order_id: string;
  restaurant_id: string;
  customer_id: string;
  distance_km: number;
  hour_of_day: number;
  day_of_week: number;
  item_count: number;
  predicted_eta_min: number;
  actual_delivery_min: number;
  is_late: boolean;
  created_at: string;
}

export interface Customer {
  id: string;
  name: string;
  lat: number;
  lon: number;
  whatsapp_phone: string;
}

export interface Restaurant {
  id: string;
  name: string;
  lat: number;
  lon: number;
  avg_prep_time_min: number;
}

export interface Product {
  id: string;
  restaurant_id: string;
  name: string;
  price: number;
  additional_prep_min: number;
}

class LocalStorageDB {
  private ordersKey = 'delivery_orders';
  private mlLogsKey = 'ml_training_logs';

  // Orders CRUD
  getOrders(): Order[] {
    const stored = localStorage.getItem(this.ordersKey);
    return stored ? JSON.parse(stored) : [];
  }

  saveOrder(order: Order): void {
    const orders = this.getOrders();
    const existingIndex = orders.findIndex(o => o.id === order.id);
    
    if (existingIndex >= 0) {
      orders[existingIndex] = order;
    } else {
      orders.push(order);
    }
    
    localStorage.setItem(this.ordersKey, JSON.stringify(orders));
  }

  getOrdersByRestaurant(restaurantId: string): Order[] {
    return this.getOrders().filter(order => order.restaurant_id === restaurantId);
  }

  getOrdersByCustomer(customerId: string): Order[] {
    return this.getOrders().filter(order => order.customer_id === customerId);
  }

  getOrderById(orderId: string): Order | null {
    return this.getOrders().find(order => order.id === orderId) || null;
  }

  updateOrderStatus(orderId: string, status: Order['status']): boolean {
    const orders = this.getOrders();
    const order = orders.find(o => o.id === orderId);
    
    if (order) {
      order.status = status;
      
      // Se foi entregue, marca o timestamp
      if (status === 'delivered') {
        order.delivered_at = new Date().toISOString();
        
        // Calcula tempo real de entrega
        const createdAt = new Date(order.created_at);
        const deliveredAt = new Date(order.delivered_at);
        order.actual_delivery_min = Math.round((deliveredAt.getTime() - createdAt.getTime()) / (1000 * 60));
        
        // Salva no ML training log
        this.saveMLTrainingLog(order);
      }
      
      this.saveOrders(orders);
      return true;
    }
    
    return false;
  }

  private saveOrders(orders: Order[]): void {
    localStorage.setItem(this.ordersKey, JSON.stringify(orders));
  }

  // ML Training Logs
  getMLTrainingLogs(): MLTrainingLog[] {
    const stored = localStorage.getItem(this.mlLogsKey);
    return stored ? JSON.parse(stored) : [];
  }

  saveMLTrainingLog(order: Order): void {
    if (!order.actual_delivery_min || !order.predicted_eta_min) return;
    
    const log: MLTrainingLog = {
      id: `ml_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      order_id: order.id,
      restaurant_id: order.restaurant_id,
      customer_id: order.customer_id,
      distance_km: order.distance_km || 0,
      hour_of_day: new Date(order.created_at).getHours(),
      day_of_week: new Date(order.created_at).getDay(),
      item_count: order.items.length,
      predicted_eta_min: order.predicted_eta_min,
      actual_delivery_min: order.actual_delivery_min,
      is_late: order.actual_delivery_min > order.predicted_eta_min,
      created_at: new Date().toISOString()
    };
    
    const logs = this.getMLTrainingLogs();
    logs.push(log);
    localStorage.setItem(this.mlLogsKey, JSON.stringify(logs));
  }

  // Utility methods
  clearAllData(): void {
    localStorage.removeItem(this.ordersKey);
    localStorage.removeItem(this.mlLogsKey);
  }

  exportData(): { orders: Order[], mlLogs: MLTrainingLog[] } {
    return {
      orders: this.getOrders(),
      mlLogs: this.getMLTrainingLogs()
    };
  }

  importData(data: { orders: Order[], mlLogs: MLTrainingLog[] }): void {
    localStorage.setItem(this.ordersKey, JSON.stringify(data.orders));
    localStorage.setItem(this.mlLogsKey, JSON.stringify(data.mlLogs));
  }

  // Analytics
  getOrderStats(restaurantId?: string): {
    totalOrders: number;
    deliveredOrders: number;
    averageDeliveryTime: number;
    accuracyRate: number;
    lateOrders: number;
  } {
    const orders = restaurantId 
      ? this.getOrdersByRestaurant(restaurantId)
      : this.getOrders();
    
    const deliveredOrders = orders.filter(o => o.status === 'delivered');
    const ordersWithTimes = deliveredOrders.filter(o => 
      o.actual_delivery_min && o.predicted_eta_min
    );
    
    const totalDeliveryTime = ordersWithTimes.reduce((sum, o) => 
      sum + (o.actual_delivery_min || 0), 0
    );
    
    const lateOrders = ordersWithTimes.filter(o => 
      (o.actual_delivery_min || 0) > (o.predicted_eta_min || 0)
    ).length;
    
    return {
      totalOrders: orders.length,
      deliveredOrders: deliveredOrders.length,
      averageDeliveryTime: ordersWithTimes.length > 0 
        ? Math.round(totalDeliveryTime / ordersWithTimes.length) 
        : 0,
      accuracyRate: ordersWithTimes.length > 0 
        ? Math.round(((ordersWithTimes.length - lateOrders) / ordersWithTimes.length) * 100)
        : 0,
      lateOrders
    };
  }
}

export const localDB = new LocalStorageDB();

// Functions to manage localStorage interactions (backward compatibility)
export const loadFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Error loading from localStorage:`, error);
    return defaultValue;
  }
};

export const saveToLocalStorage = <T>(key: string, value: T): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error saving to localStorage:`, error);
  }
};

export const removeFromLocalStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing from localStorage:`, error);
  }
};
