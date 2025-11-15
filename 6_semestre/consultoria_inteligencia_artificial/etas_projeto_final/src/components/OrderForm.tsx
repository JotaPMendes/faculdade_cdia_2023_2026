import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Label } from "./ui/label";
import { Checkbox } from "./ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { calculateDistance } from "@/lib/haversine";
import { getMLApiClient, PredictionRequest } from "@/lib/ml-api-client";
import { localDB, Order, OrderItem } from "@/lib/local-storage";
import { restaurants, products, customers as seedCustomers, getRestaurantById, getProductById, getCustomerById, getProductsByRestaurant } from "@/data/seed-data";
import { Loader2, Brain, AlertTriangle, Zap } from "lucide-react";

interface OrderFormProps {
  restaurantId: string;
  onOrderCreated: () => void;
}

export const OrderForm = ({ restaurantId, onOrderCreated }: OrderFormProps) => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState("");
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [mlPrediction, setMlPrediction] = useState<{
    eta: number;
    riskFactors: string[];
    confidence: number;
    modelUsed: string;
  } | null>(null);
  const { toast } = useToast();

  const [restaurantName, setRestaurantName] = useState("");

  useEffect(() => {
    loadData();
  }, [restaurantId]);

  useEffect(() => {
    updateMLPrediction();
  }, [selectedCustomer, selectedProducts]);

  const loadData = () => {
    // Carrega dados dos seeds locais
    const restaurant = getRestaurantById(restaurantId);
    if (restaurant) {
      setRestaurantName(restaurant.name);
    }
    
    const restaurantProducts = getProductsByRestaurant(restaurantId);
    setProducts(restaurantProducts);
    setCustomers(seedCustomers);
  };

  const handleProductToggle = (productId: string) => {
    setSelectedProducts((prev) =>
      prev.includes(productId)
        ? prev.filter((id) => id !== productId)
        : [...prev, productId]
    );
    
    // Recalcular predição quando produtos mudam
    updateMLPrediction();
  };

  const updateMLPrediction = async () => {
    if (!selectedCustomer || selectedProducts.length === 0) {
      setMlPrediction(null);
      return;
    }

    try {
      // Buscar dados do restaurante e cliente dos seeds
      const restaurant = getRestaurantById(restaurantId);
      const customer = getCustomerById(selectedCustomer);

      if (!restaurant || !customer) return;

      // Calcular distância
      const distance = calculateDistance(
        restaurant.lat,
        restaurant.lon,
        customer.lat,
        customer.lon
      );

      // Obter tempo de preparo dos produtos
      const selectedProductsData = selectedProducts.map(id => getProductById(id)).filter(Boolean);

      const additionalPrepTime = selectedProductsData.reduce(
        (sum, p) => sum + (p?.additional_prep_min || 0),
        0
      );

      const totalPrepTime = restaurant.avg_prep_time_min + additionalPrepTime;

      // Simular condições atuais
      const now = new Date();
      const hour = now.getHours();
      const dayOfWeek = now.getDay();
      
      // Simulação de condições (em um app real, isso viria de APIs)
      const weatherConditions = ['sunny', 'cloudy', 'rainy'];
      const currentWeather = weatherConditions[Math.floor(Math.random() * weatherConditions.length)];
      const trafficLevel = hour >= 18 && hour <= 20 ? 3 : hour >= 12 && hour <= 14 ? 2 : 1;

      const predictionInput: PredictionRequest = {
        distance_km: distance,
        day_of_week: dayOfWeek,
        hour_of_day: hour,
        weather: currentWeather,
        traffic_level: trafficLevel,
        preparation_time_min: totalPrepTime
      };

      // Usar modelo de ML Python
      const mlClient = getMLApiClient();
      const etaPrediction = await mlClient.predictETA(predictionInput);
      
      if (etaPrediction) {
        setMlPrediction({
          eta: etaPrediction.eta_minutes,
          riskFactors: etaPrediction.risk_factors,
          confidence: etaPrediction.confidence,
          modelUsed: etaPrediction.model_used
        });
      } else {
        setMlPrediction(null);
      }

    } catch (error) {
      console.error('Erro ao calcular predição ML:', error);
      setMlPrediction(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedCustomer || selectedProducts.length === 0) {
      toast({
        title: "Erro",
        description: "Selecione um cliente e pelo menos um item",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);

    try {
      // Encontra dados do cliente e restaurante
      const customer = getCustomerById(selectedCustomer);
      const restaurant = getRestaurantById(restaurantId);
      
      if (!customer || !restaurant) {
        throw new Error('Cliente ou restaurante não encontrado');
      }

      // Calcula distância
      const distance = calculateDistance(
        restaurant.lat, restaurant.lon,
        customer.lat, customer.lon
      );

      // Calcular total e preparar items do pedido
      const selectedProductsData = selectedProducts.map(id => getProductById(id)).filter(Boolean);
      const total = selectedProductsData.reduce((sum, product) => sum + product!.price, 0);

      // Prepara items do pedido
      const orderItems: OrderItem[] = selectedProductsData.map(product => ({
        id: `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        product_id: product!.id,
        quantity: 1,
        unit_price: product!.price
      }));

      // Cria o pedido
      const order: Order = {
        id: `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        customer_id: selectedCustomer,
        restaurant_id: restaurantId,
        status: 'preparing',
        predicted_eta_min: mlPrediction?.eta || null,
        actual_delivery_min: null,
        distance_km: distance,
        created_at: new Date().toISOString(),
        delivered_at: null,
        items: orderItems,
        total_amount: total
      };

      // Salva no localStorage
      localDB.saveOrder(order);

      toast({
        title: "Pedido criado!",
        description: `Pedido #${order.id.slice(-8)} criado com sucesso. ${order.predicted_eta_min ? `ETA: ${order.predicted_eta_min} min` : ''}`,
        variant: "default"
      });

      // Reset form
      setSelectedCustomer('');
      setSelectedProducts([]);
      setMlPrediction(null);
      
      // Callback para atualizar lista
      onOrderCreated();

    } catch (error: any) {
      console.error('Erro ao criar pedido:', error);
      toast({
        title: "Erro",
        description: "Falha ao criar pedido. Tente novamente.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 p-6 border rounded-lg bg-card">
      <div className="space-y-2">
        <Label htmlFor="customer">Cliente</Label>
        <Select value={selectedCustomer} onValueChange={setSelectedCustomer}>
          <SelectTrigger id="customer">
            <SelectValue placeholder="Selecione o cliente" />
          </SelectTrigger>
          <SelectContent>
            {customers.map((customer) => (
              <SelectItem key={customer.id} value={customer.id}>
                {customer.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-3">
        <Label>Produtos</Label>
        <div className="space-y-2 max-h-60 overflow-y-auto border rounded-md p-3">
          {products.map((product) => (
            <div key={product.id} className="flex items-center space-x-2">
              <Checkbox
                id={product.id}
                checked={selectedProducts.includes(product.id)}
                onCheckedChange={() => handleProductToggle(product.id)}
              />
              <label
                htmlFor={product.id}
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex-1"
              >
                {product.name} - R$ {Number(product.price).toFixed(2)}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Total do Pedido */}
      {selectedProducts.length > 0 && (
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Total do Pedido:</span>
            <span className="text-lg font-bold text-green-600">
              R$ {selectedProducts.reduce((sum, productId) => {
                const product = getProductById(productId);
                return sum + (product?.price || 0);
              }, 0).toFixed(2)}
            </span>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {selectedProducts.length} item(s) selecionado(s)
          </div>
        </div>
      )}

      {/* ML Prediction Display */}
      {mlPrediction && (
        <div className="space-y-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-blue-800">Predição Inteligente de ETA</h3>
            <div className="ml-auto">
              {mlPrediction.modelUsed === 'JavaScript Fallback' ? (
                <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded-full flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  Fallback
                </span>
              ) : (
                <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full flex items-center gap-1">
                  <Brain className="w-3 h-3" />
                  Python ML
                </span>
              )}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <p className="text-sm text-gray-600">Tempo Estimado</p>
              <p className="text-2xl font-bold text-blue-600">{mlPrediction.eta} min</p>
              <p className="text-xs text-gray-500">
                Confiança: {mlPrediction.confidence}% • {mlPrediction.modelUsed}
              </p>
            </div>
            
            {mlPrediction.riskFactors.length > 0 && (
              <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                <div className="flex items-center gap-1 mb-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <p className="text-sm font-medium text-orange-800">Fatores de Risco</p>
                </div>
                <ul className="text-xs text-orange-700 space-y-1">
                  {mlPrediction.riskFactors.map((factor, index) => (
                    <li key={index}>• {factor}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {mlPrediction.riskFactors.length === 0 && (
            <div className="bg-green-50 p-3 rounded-lg border border-green-200 text-center">
              <p className="text-sm text-green-700">✅ Condições favoráveis para entrega</p>
            </div>
          )}
        </div>
      )}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
        {mlPrediction ? (
          <>
            <Brain className="w-4 h-4 mr-2" />
            Criar Pedido (ETA: {mlPrediction.eta} min)
          </>
        ) : (
          "Criar Pedido e Calcular ETA"
        )}
      </Button>
    </form>
  );
};
