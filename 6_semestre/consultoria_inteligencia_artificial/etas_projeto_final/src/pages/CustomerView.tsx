import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LogOut, Package, Clock, MapPin, CheckCircle2, TruckIcon, AlertTriangle, RefreshCw } from "lucide-react";
import { localDB, Order, Customer } from "@/lib/local-storage";
import { getCustomerById, getProductById, getRestaurantById } from "@/data/seed-data";

const CustomerView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);

  useEffect(() => {
    loadCustomer();
    loadOrders();
  }, [id]);

  const loadCustomer = () => {
    if (!id) {
      toast({
        title: "Erro",
        description: "ID do cliente não fornecido",
        variant: "destructive",
      });
      navigate("/");
      return;
    }

    const customerData = getCustomerById(id);
    
    if (!customerData) {
      toast({
        title: "Erro",
        description: "Cliente não encontrado",
        variant: "destructive",
      });
      navigate("/");
      return;
    }

    setCustomer(customerData);
  };

  const loadOrders = () => {
    if (!id) return;
    
    const customerOrders = localDB.getOrdersByCustomer(id);
    const sortedOrders = customerOrders.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    setOrders(sortedOrders);
  };

  const getStatusInfo = (status: Order['status']) => {
    switch (status) {
      case "preparing":
        return { 
          label: "Preparando", 
          icon: Package, 
          variant: "secondary" as const,
          color: "text-yellow-700 bg-yellow-100" 
        };
      case "in_route":
        return { 
          label: "Em Rota", 
          icon: TruckIcon, 
          variant: "default" as const,
          color: "text-blue-700 bg-blue-100" 
        };
      case "delivered":
        return { 
          label: "Entregue", 
          icon: CheckCircle2, 
          variant: "default" as const,
          color: "text-green-700 bg-green-100" 
        };
      case "cancelled":
        return { 
          label: "Cancelado", 
          icon: AlertTriangle, 
          variant: "destructive" as const,
          color: "text-red-700 bg-red-100" 
        };
      default:
        return { 
          label: "Desconhecido", 
          icon: Package, 
          variant: "outline" as const,
          color: "text-gray-700 bg-gray-100" 
        };
    }
  };

  if (!customer) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-accent/5 via-background to-primary/5">
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Olá, {customer.name}!</h1>
            <p className="text-sm text-muted-foreground">Acompanhe seus pedidos</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadOrders} className="gap-2">
              <RefreshCw className="w-4 h-4" />
              Atualizar
            </Button>
            <Button variant="outline" onClick={() => navigate("/")} className="gap-2">
              <LogOut className="w-4 h-4" />
              Sair
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Meus Pedidos ({orders.length})</CardTitle>
            <CardDescription>
              Acompanhe o status dos seus pedidos em tempo real
            </CardDescription>
          </CardHeader>
          <CardContent>
            {orders.length === 0 ? (
              <div className="text-center py-8">
                <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-muted-foreground">Você ainda não fez nenhum pedido</p>
              </div>
            ) : (
              <div className="space-y-4">
                {orders.map((order) => {
                  const statusInfo = getStatusInfo(order.status);
                  const StatusIcon = statusInfo.icon;
                  const restaurant = getRestaurantById(order.restaurant_id);

                  // Debug log
                  console.log('Order debug:', {
                    id: order.id,
                    predicted_eta_min: order.predicted_eta_min,
                    actual_delivery_min: order.actual_delivery_min,
                    status: order.status
                  });

                  return (
                    <Card key={order.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <CardTitle className="text-lg">
                              Pedido #{order.id.slice(-8)}
                            </CardTitle>
                            <CardDescription>
                              {restaurant?.name || 'Restaurante não encontrado'}
                            </CardDescription>
                            <CardDescription className="flex items-center gap-2">
                              <MapPin className="w-3 h-3" />
                              {order.distance_km?.toFixed(2)} km de distância
                            </CardDescription>
                            <CardDescription className="text-xs">
                              {new Date(order.created_at).toLocaleString('pt-BR')}
                            </CardDescription>
                          </div>
                          <Badge variant={statusInfo.variant} className={statusInfo.color}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {statusInfo.label}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <p className="text-sm font-medium">Itens do Pedido:</p>
                          <ul className="space-y-1">
                            {order.items.map((item) => {
                              const product = getProductById(item.product_id);
                              return (
                                <li key={item.id} className="text-sm text-muted-foreground flex justify-between">
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

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {(order.predicted_eta_min !== null && order.predicted_eta_min !== undefined && order.predicted_eta_min > 0) && (
                            <div className="flex items-center gap-2 p-3 bg-primary/5 rounded-lg">
                              <Clock className="w-5 h-5 text-primary" />
                              <div>
                                <p className="text-sm font-medium">Tempo Estimado</p>
                                <p className="text-xs text-muted-foreground">{order.predicted_eta_min} minutos</p>
                              </div>
                            </div>
                          )}

                          {(order.actual_delivery_min !== null && order.actual_delivery_min !== undefined && order.actual_delivery_min > 0) && (
                            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                              <div>
                                <p className="text-sm font-medium">Tempo Real</p>
                                <p className="text-xs text-muted-foreground">{order.actual_delivery_min} minutos</p>
                              </div>
                            </div>
                          )}
                        </div>

                        {order.status === 'delivered' && 
                         order.actual_delivery_min !== null && order.actual_delivery_min !== undefined && order.actual_delivery_min > 0 &&
                         order.predicted_eta_min !== null && order.predicted_eta_min !== undefined && order.predicted_eta_min > 0 && (
                          <div className={`p-3 rounded-lg ${
                            order.actual_delivery_min <= order.predicted_eta_min 
                              ? 'bg-green-50 border border-green-200' 
                              : 'bg-orange-50 border border-orange-200'
                          }`}>
                            <p className={`text-sm font-medium ${
                              order.actual_delivery_min <= order.predicted_eta_min 
                                ? 'text-green-800' 
                                : 'text-orange-800'
                            }`}>
                              {order.actual_delivery_min <= order.predicted_eta_min 
                                ? '✅ Entregue no prazo!' 
                                : '⏰ Entregue com atraso'}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Diferença: {Math.abs(order.actual_delivery_min - order.predicted_eta_min)} minutos
                            </p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default CustomerView;
