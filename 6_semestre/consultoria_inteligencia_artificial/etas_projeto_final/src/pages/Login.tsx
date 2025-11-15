import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Clock, MapPin } from "lucide-react";
import { restaurants, customers } from "@/data/seed-data";

const Login = () => {
  const [userType, setUserType] = useState<"restaurant" | "customer" | "">("");
  const [selectedId, setSelectedId] = useState("");
  const [restaurantList, setRestaurantList] = useState<any[]>([]);
  const [customerList, setCustomerList] = useState<any[]>([]);
  const navigate = useNavigate();
  const { toast } = useToast();

  const loadData = (type: "restaurant" | "customer") => {
    if (type === "restaurant") {
      setRestaurantList(restaurants.sort((a, b) => a.name.localeCompare(b.name)));
    } else {
      setCustomerList(customers.sort((a, b) => a.name.localeCompare(b.name)));
    }
  };

  const handleUserTypeChange = (value: "restaurant" | "customer") => {
    setUserType(value);
    setSelectedId("");
    loadData(value);
  };

  const handleLogin = () => {
    if (!userType || !selectedId) {
      toast({
        title: "Seleção necessária",
        description: "Por favor, selecione o tipo de usuário e uma opção",
        variant: "destructive",
      });
      return;
    }

    if (userType === "restaurant") {
      navigate(`/restaurant/${selectedId}`);
    } else {
      navigate(`/customer/${selectedId}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-2 shadow-lg">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center">
            <Clock className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-3xl font-bold">ETA Delivery System</CardTitle>
          <CardDescription className="text-base">
            Sistema de previsão de tempo de entrega para restaurantes e clientes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="userType">Tipo de Usuário</Label>
            <Select value={userType} onValueChange={handleUserTypeChange}>
              <SelectTrigger id="userType">
                <SelectValue placeholder="Selecione o tipo de usuário" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="restaurant">🏪 Restaurante</SelectItem>
                <SelectItem value="customer">👤 Cliente</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {userType && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
              <Label htmlFor="selection">
                {userType === "restaurant" ? "Selecione o Restaurante" : "Selecione o Cliente"}
              </Label>
              <Select value={selectedId} onValueChange={setSelectedId}>
                <SelectTrigger id="selection">
                  <SelectValue placeholder={`Escolha ${userType === "restaurant" ? "um restaurante" : "um cliente"}`} />
                </SelectTrigger>
                <SelectContent>
                  {userType === "restaurant"
                    ? restaurantList.map((r) => (
                        <SelectItem key={r.id} value={r.id}>
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4" />
                            {r.name}
                          </div>
                        </SelectItem>
                      ))
                    : customerList.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4" />
                            {c.name}
                          </div>
                        </SelectItem>
                      ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <Button 
            onClick={handleLogin} 
            className="w-full" 
            size="lg"
            disabled={!userType || !selectedId}
          >
            Entrar no Sistema
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
