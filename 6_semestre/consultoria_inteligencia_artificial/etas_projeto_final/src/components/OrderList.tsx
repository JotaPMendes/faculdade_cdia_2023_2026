import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Package, Clock, MapPin, TruckIcon, CheckCircle2, AlertTriangle } from "lucide-react";
import { localDB, Order } from "@/lib/local-storage";
import { getCustomerById, getProductById } from "@/data/seed-data";
import { useToast } from "@/hooks/use-toast";

interface OrderListProps {
  restaurantId: string;
  refreshTrigger: number;
}

export const OrderList = ({ restaurantId, refreshTrigger }: OrderListProps) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    loadOrders();
  }, [restaurantId, refreshTrigger]);

  const loadOrders = () => {
    const restaurantOrders = localDB.getOrdersByRestaurant(restaurantId);
    // Ordena por data de criação (mais recentes primeiro)
    const sortedOrders = restaurantOrders.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    setOrders(sortedOrders);
  };

  const updateOrderStatus = (orderId: string, newStatus: Order['status']) => {
    const success = localDB.updateOrderStatus(orderId, newStatus);
    if (success) {
      loadOrders(); // Recarrega a lista
      toast({
        title: "Status atualizado!",
        description: `Pedido marcado como ${getStatusInfo(newStatus).label}`,
        variant: "default"
      });
    } else {
      toast({
        title: "Erro",
        description: "Não foi possível atualizar o status do pedido",
        variant: "destructive"
      });
    }
  };

  const getCustomerName = (customerId: string) => {
    const customer = getCustomerById(customerId);
    return customer?.name || 'Cliente não encontrado';
  };

  const getStatusInfo = (status: Order['status']) => {
    switch (status) {
      case 'preparing':
        return { 
          label: 'Preparando', 
          icon: Package,
          variant: 'secondary' as const
        };
      case 'in_route':
        return { 
          label: 'A caminho', 
          icon: TruckIcon,
          variant: 'default' as const
        };
      case 'delivered':
        return { 
          label: 'Entregue', 
          icon: CheckCircle2,
          variant: 'default' as const
        };
      case 'cancelled':
        return { 
          label: 'Cancelado', 
          icon: AlertTriangle,
          variant: 'destructive' as const
        };
      default:
        return { 
          label: 'Desconhecido', 
          icon: Package,
          variant: 'outline' as const
        };
    }
  };

  const getNextStatus = (currentStatus: Order['status']): Order['status'] | null => {
    switch (currentStatus) {
      case 'preparing':
        return 'in_route';
      case 'in_route':
        return 'delivered';
      default:
        return null;
    }
  };

  const getNextStatusLabel = (currentStatus: Order['status']): string => {
    switch (currentStatus) {
      case 'preparing':
        return 'Marcar como A Caminho';
      case 'in_route':
        return 'Marcar como Entregue';
      default:
        return '';
    }
  };

  if (orders.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="text-muted-foreground">Nenhum pedido encontrado</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Pedidos ({orders.length})</h2>
      {orders.map((order) => {
        const statusInfo = getStatusInfo(order.status);
        const StatusIcon = statusInfo.icon;
        const nextStatus = getNextStatus(order.status);
        const nextStatusLabel = getNextStatusLabel(order.status);

        return (
          <Card key={order.id} className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold">Pedido #{order.id.slice(-8)}</h3>
                <p className="text-sm text-muted-foreground">
                  Cliente: {getCustomerName(order.customer_id)}
                </p>
                <p className="text-sm text-muted-foreground">
                  {new Date(order.created_at).toLocaleString('pt-BR')}
                </p>
              </div>
              <Badge variant={statusInfo.variant}>
                <StatusIcon className="w-4 h-4 mr-1" />
                {statusInfo.label}
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
                <MapPin className="w-5 h-5 text-primary" />
                <div>
                  <p className="text-sm font-medium">Distância</p>
                  <p className="text-xs text-muted-foreground">
                    {order.distance_km?.toFixed(1)} km
                  </p>
                </div>
              </div>

              {order.predicted_eta_min && (
                <div className="flex items-center gap-2 p-3 bg-primary/5 rounded-lg">
                  <Clock className="w-5 h-5 text-primary" />
                  <div>
                    <p className="text-sm font-medium">ETA Previsto</p>
                    <p className="text-xs text-muted-foreground">
                      {order.predicted_eta_min} minutos
                    </p>
                  </div>
                </div>
              )}

              {order.actual_delivery_min && (
                <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">Tempo Real</p>
                    <p className="text-xs text-muted-foreground">
                      {order.actual_delivery_min} minutos
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="mb-4">
              <h4 className="font-medium mb-2">Itens do Pedido:</h4>
              <ul className="space-y-1">
                {order.items.map((item) => {
                  const product = getProductById(item.product_id);
                  return (
                    <li key={item.id} className="flex justify-between text-sm">
                      <span>{item.quantity}x {product?.name || 'Produto'}</span>
                      <span>R$ {(item.quantity * item.unit_price).toFixed(2)}</span>
                    </li>
                  );
                })}
              </ul>
              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between font-medium">
                  <span>Total:</span>
                  <span>R$ {order.total_amount.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {nextStatus && order.status !== 'delivered' && order.status !== 'cancelled' && (
              <Button
                onClick={() => updateOrderStatus(order.id, nextStatus)}
                className="w-full"
              >
                {nextStatusLabel}
              </Button>
            )}
          </Card>
        );
      })}
    </div>
  );
};