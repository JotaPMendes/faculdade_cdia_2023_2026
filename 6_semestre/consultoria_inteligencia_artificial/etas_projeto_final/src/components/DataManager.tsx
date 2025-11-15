import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { localDB } from '@/lib/local-storage';
import { Download, Upload, Trash2, BarChart3, Database, FileJson } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { generateSampleOrders } from '@/data/seed-data';

export const DataManager = () => {
  const { toast } = useToast();

  const exportData = () => {
    try {
      const data = localDB.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `delivery-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Dados exportados!",
        description: "Arquivo baixado com sucesso.",
        variant: "default"
      });
    } catch (error) {
      toast({
        title: "Erro",
        description: "Falha ao exportar dados.",
        variant: "destructive"
      });
    }
  };

  const importData = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string);
        localDB.importData(data);
        toast({
          title: "Dados importados!",
          description: "Dados carregados com sucesso. A página será recarregada.",
          variant: "default"
        });
        setTimeout(() => window.location.reload(), 2000);
      } catch (error) {
        toast({
          title: "Erro",
          description: "Erro ao importar dados. Verifique o formato do arquivo.",
          variant: "destructive"
        });
      }
    };
    reader.readAsText(file);
    
    // Reset input
    event.target.value = '';
  };

  const clearAllData = () => {
    if (confirm('Tem certeza que deseja limpar todos os dados? Esta ação não pode ser desfeita.')) {
      localDB.clearAllData();
      toast({
        title: "Dados removidos!",
        description: "Todos os dados foram removidos. A página será recarregada.",
        variant: "default"
      });
      setTimeout(() => window.location.reload(), 2000);
    }
  };

  const generateSampleData = () => {
    if (confirm('Deseja gerar pedidos de exemplo? Isso adicionará 10 pedidos fictícios.')) {
      const sampleOrders = generateSampleOrders();
      sampleOrders.forEach(order => localDB.saveOrder(order as any));
      
      toast({
        title: "Dados de exemplo criados!",
        description: "10 pedidos fictícios foram adicionados.",
        variant: "default"
      });
      
      setTimeout(() => window.location.reload(), 2000);
    }
  };

  const data = localDB.exportData();
  const stats = localDB.getOrderStats();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Estatísticas dos Dados
          </CardTitle>
          <CardDescription>
            Visão geral dos dados armazenados localmente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{data.orders.length}</p>
              <p className="text-sm text-blue-800">Pedidos Total</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{stats.deliveredOrders}</p>
              <p className="text-sm text-green-800">Entregues</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">{data.mlLogs.length}</p>
              <p className="text-sm text-purple-800">Logs ML</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">{stats.accuracyRate}%</p>
              <p className="text-sm text-orange-800">Precisão</p>
            </div>
          </div>

          {stats.averageDeliveryTime > 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4" />
                <span className="font-medium">Métricas de Performance</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Tempo médio de entrega:</span>
                  <span className="ml-2 font-medium">{stats.averageDeliveryTime} min</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Pedidos atrasados:</span>
                  <span className="ml-2 font-medium">{stats.lateOrders}</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileJson className="w-5 h-5" />
            Gerenciamento de Dados
          </CardTitle>
          <CardDescription>
            Exporte, importe ou limpe os dados armazenados
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button onClick={exportData} className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              Exportar Dados
            </Button>
            
            <label className="cursor-pointer">
              <Button variant="outline" className="flex items-center gap-2 w-full">
                <Upload className="w-4 h-4" />
                Importar Dados
              </Button>
              <input
                type="file"
                accept=".json"
                onChange={importData}
                className="hidden"
              />
            </label>
            
            <Button onClick={generateSampleData} variant="secondary" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Gerar Dados de Exemplo
            </Button>
            
            <Button 
              onClick={clearAllData} 
              variant="destructive"
              className="flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Limpar Todos os Dados
            </Button>
          </div>

          <div className="mt-6 p-4 border rounded-lg bg-yellow-50 border-yellow-200">
            <h4 className="font-medium text-yellow-800 mb-2">⚠️ Importante</h4>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>• Os dados são armazenados no navegador (localStorage)</li>
              <li>• Limpar o cache do navegador remove todos os dados</li>
              <li>• Faça backup regular exportando os dados</li>
              <li>• Os dados não são sincronizados entre dispositivos</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};