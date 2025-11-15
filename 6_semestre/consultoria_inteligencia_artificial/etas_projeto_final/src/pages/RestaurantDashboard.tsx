import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LogOut, Plus, Settings, Brain } from "lucide-react";
import { OrderForm } from "@/components/OrderForm";
import { OrderList } from "@/components/OrderList";
import { DataManager } from "@/components/DataManager";
import { MLSyncManager } from "@/components/MLSyncManager";
import { getRestaurantById } from "@/data/seed-data";
import { Restaurant } from "@/lib/local-storage";

const RestaurantDashboard = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [showDataManager, setShowDataManager] = useState(false);
  const [showMLManager, setShowMLManager] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    loadRestaurant();
  }, [id]);

  const loadRestaurant = () => {
    if (!id) {
      toast({
        title: "Erro",
        description: "ID do restaurante não fornecido",
        variant: "destructive",
      });
      navigate("/");
      return;
    }

    const restaurantData = getRestaurantById(id);
    
    if (!restaurantData) {
      toast({
        title: "Erro",
        description: "Restaurante não encontrado",
        variant: "destructive",
      });
      navigate("/");
      return;
    }

    setRestaurant(restaurantData);
  };

  const handleOrderCreated = () => {
    setShowOrderForm(false);
    setRefreshTrigger(prev => prev + 1);
  };

  if (!restaurant) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{restaurant.name}</h1>
            <p className="text-sm text-muted-foreground">Dashboard do Restaurante</p>
          </div>
          <Button variant="outline" onClick={() => navigate("/")} className="gap-2">
            <LogOut className="w-4 h-4" />
            Sair
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-6">
        <div className="flex gap-4 mb-6">
          <Button 
            onClick={() => setShowOrderForm(!showOrderForm)} 
            className="gap-2"
            variant={showOrderForm ? "outline" : "default"}
          >
            <Plus className="w-4 h-4" />
            {showOrderForm ? "Cancelar" : "Novo Pedido"}
          </Button>
          
          <Button 
            onClick={() => setShowDataManager(!showDataManager)} 
            variant={showDataManager ? "outline" : "secondary"}
            className="gap-2"
          >
            <Settings className="w-4 h-4" />
            {showDataManager ? "Fechar" : "Gerenciar Dados"}
          </Button>

          <Button 
            onClick={() => setShowMLManager(!showMLManager)} 
            variant={showMLManager ? "outline" : "secondary"}
            className="gap-2"
          >
            <Brain className="w-4 h-4" />
            {showMLManager ? "Fechar" : "Machine Learning"}
          </Button>
        </div>

        {showOrderForm && (
          <Card className="border-2">
            <CardHeader>
              <CardTitle>Criar Novo Pedido</CardTitle>
              <CardDescription>Preencha os dados do pedido e o ETA será calculado automaticamente</CardDescription>
            </CardHeader>
            <CardContent>
              <OrderForm restaurantId={id!} onOrderCreated={handleOrderCreated} />
            </CardContent>
          </Card>
        )}

        {showDataManager && (
          <Card className="border-2">
            <CardHeader>
              <CardTitle>Gerenciamento de Dados</CardTitle>
              <CardDescription>Exporte, importe ou visualize estatísticas dos dados</CardDescription>
            </CardHeader>
            <CardContent>
              <DataManager />
            </CardContent>
          </Card>
        )}

        {showMLManager && (
          <MLSyncManager restaurantId={id!} />
        )}

        <OrderList restaurantId={id!} refreshTrigger={refreshTrigger} />
      </main>
    </div>
  );
};

export default RestaurantDashboard;
