import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DeliveryAnalytics:
    """
    Classe para análises avançadas de dados de delivery
    """
    
    def __init__(self, data_path: str = "../src/data/historical_deliveries.json"):
        self.data_path = data_path
        self.df = self.load_data()
    
    def load_data(self) -> pd.DataFrame:
        """Carrega dados históricos"""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {self.data_path}")
            return pd.DataFrame()
    
    def calculate_error_metrics(self, predictions: List[float], actuals: List[float]) -> Dict:
        """Calcula métricas de erro detalhadas"""
        if len(predictions) != len(actuals):
            raise ValueError("Arrays devem ter o mesmo tamanho")
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Métricas básicas
        mae = np.mean(np.abs(predictions - actuals))
        mse = np.mean((predictions - actuals) ** 2)
        rmse = np.sqrt(mse)
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
        
        # R-squared
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Métricas personalizadas
        within_3min = np.mean(np.abs(predictions - actuals) <= 3) * 100
        within_5min = np.mean(np.abs(predictions - actuals) <= 5) * 100
        
        return {
            'mae': round(mae, 2),
            'mse': round(mse, 2),
            'rmse': round(rmse, 2),
            'mape': round(mape, 2),
            'r2': round(r2, 3),
            'accuracy_3min': round(within_3min, 1),
            'accuracy_5min': round(within_5min, 1)
        }
    
    def analyze_delivery_patterns(self) -> Dict:
        """Analisa padrões de entrega por diferentes dimensões"""
        if self.df.empty:
            return {}
        
        # Análise por horário
        hourly_stats = self.df.groupby('hour_of_day').agg({
            'actual_delivery_min': ['mean', 'std', 'count'],
            'is_late': ['sum', 'mean']
        }).round(2)
        
        # Análise por dia da semana
        daily_stats = self.df.groupby('day_of_week').agg({
            'actual_delivery_min': ['mean', 'std', 'count'],
            'is_late': ['sum', 'mean']
        }).round(2)
        
        # Análise por condições climáticas
        weather_stats = self.df.groupby('weather').agg({
            'actual_delivery_min': ['mean', 'std', 'count'],
            'is_late': ['sum', 'mean'],
            'delay_min': 'mean'
        }).round(2)
        
        # Análise por nível de trânsito
        traffic_stats = self.df.groupby('traffic_level').agg({
            'actual_delivery_min': ['mean', 'std', 'count'],
            'is_late': ['sum', 'mean']
        }).round(2)
        
        return {
            'hourly_patterns': hourly_stats.to_dict(),
            'daily_patterns': daily_stats.to_dict(),
            'weather_impact': weather_stats.to_dict(),
            'traffic_impact': traffic_stats.to_dict()
        }
    
    def detect_anomalies(self, method: str = 'zscore', threshold: float = 2.5) -> pd.DataFrame:
        """Detecta anomalias nos tempos de entrega"""
        if self.df.empty:
            return pd.DataFrame()
        
        df_anomalies = self.df.copy()
        
        if method == 'zscore':
            # Z-score method
            mean_delivery = df_anomalies['actual_delivery_min'].mean()
            std_delivery = df_anomalies['actual_delivery_min'].std()
            
            df_anomalies['z_score'] = np.abs(
                (df_anomalies['actual_delivery_min'] - mean_delivery) / std_delivery
            )
            
            anomalies = df_anomalies[df_anomalies['z_score'] > threshold].copy()
            
        elif method == 'iqr':
            # Interquartile Range method
            Q1 = df_anomalies['actual_delivery_min'].quantile(0.25)
            Q3 = df_anomalies['actual_delivery_min'].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            anomalies = df_anomalies[
                (df_anomalies['actual_delivery_min'] < lower_bound) |
                (df_anomalies['actual_delivery_min'] > upper_bound)
            ].copy()
            
            anomalies['outlier_score'] = np.where(
                anomalies['actual_delivery_min'] < lower_bound,
                lower_bound - anomalies['actual_delivery_min'],
                anomalies['actual_delivery_min'] - upper_bound
            )
        
        # Adicionar classificação da anomalia
        if not anomalies.empty:
            anomalies['anomaly_type'] = anomalies.apply(
                lambda row: self._classify_anomaly(row), axis=1
            )
        
        return anomalies
    
    def _classify_anomaly(self, row) -> str:
        """Classifica o tipo de anomalia"""
        if row['actual_delivery_min'] > row['predicted_eta_min'] + 10:
            return "Atraso extremo"
        elif row['actual_delivery_min'] < row['predicted_eta_min'] - 5:
            return "Entrega muito rápida"
        elif row['weather'] == 'rainy' and row['delay_min'] > 5:
            return "Atraso por clima"
        elif row['traffic_level'] == 3 and row['delay_min'] > 5:
            return "Atraso por trânsito"
        else:
            return "Anomalia não classificada"
    
    def correlation_analysis(self) -> Dict:
        """Analisa correlações entre variáveis"""
        if self.df.empty:
            return {}
        
        # Preparar dados numéricos
        numeric_columns = [
            'distance_km', 'predicted_eta_min', 'actual_delivery_min',
            'hour_of_day', 'day_of_week', 'traffic_level', 
            'preparation_time_min', 'delay_min'
        ]
        
        # Adicionar encoding para weather
        weather_encoded = pd.get_dummies(self.df['weather'], prefix='weather')
        df_numeric = pd.concat([self.df[numeric_columns], weather_encoded], axis=1)
        
        # Calcular matriz de correlação
        correlation_matrix = df_numeric.corr()
        
        # Correlações com tempo de entrega
        delivery_correlations = correlation_matrix['actual_delivery_min'].abs().sort_values(ascending=False)
        
        # Top correlações
        strong_correlations = delivery_correlations[delivery_correlations > 0.3]
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'delivery_time_correlations': delivery_correlations.to_dict(),
            'strong_correlations': strong_correlations.to_dict()
        }
    
    def time_series_analysis(self) -> Dict:
        """Análise temporal dos dados"""
        if self.df.empty:
            return {}
        
        # Simular timestamps baseados nos dados
        df_ts = self.df.copy()
        base_date = datetime.now() - timedelta(days=len(df_ts))
        df_ts['timestamp'] = [base_date + timedelta(hours=i*2) for i in range(len(df_ts))]
        df_ts.set_index('timestamp', inplace=True)
        
        # Métricas por período
        daily_metrics = df_ts.resample('D').agg({
            'actual_delivery_min': ['mean', 'std', 'count'],
            'is_late': 'mean',
            'delay_min': 'mean'
        }).round(2)
        
        # Tendências
        rolling_avg = df_ts['actual_delivery_min'].rolling(window=5).mean()
        
        return {
            'daily_metrics': daily_metrics.to_dict(),
            'rolling_average': rolling_avg.to_dict(),
            'trend_direction': 'increasing' if rolling_avg.iloc[-1] > rolling_avg.iloc[0] else 'decreasing'
        }
    
    def generate_insights(self) -> Dict:
        """Gera insights automáticos dos dados"""
        if self.df.empty:
            return {}
        
        insights = []
        
        # Análise de performance geral
        avg_delivery = self.df['actual_delivery_min'].mean()
        late_percentage = (self.df['is_late'].sum() / len(self.df)) * 100
        
        if late_percentage > 40:
            insights.append("⚠️ Alta taxa de atrasos detectada (>40%)")
        elif late_percentage < 20:
            insights.append("✅ Baixa taxa de atrasos (<20%)")
        
        # Análise por distância
        long_distance_late = self.df[self.df['distance_km'] > 3]['is_late'].mean() * 100
        short_distance_late = self.df[self.df['distance_km'] <= 1]['is_late'].mean() * 100
        
        if long_distance_late > short_distance_late + 20:
            insights.append("📍 Entregas longas (>3km) têm significativamente mais atrasos")
        
        # Análise por horário
        peak_hours = self.df.groupby('hour_of_day')['is_late'].mean()
        worst_hour = peak_hours.idxmax()
        worst_rate = peak_hours.max() * 100
        
        if worst_rate > 50:
            insights.append(f"⏰ Horário crítico: {worst_hour}h com {worst_rate:.0f}% de atrasos")
        
        # Análise climática
        weather_impact = self.df.groupby('weather')['delay_min'].mean()
        if 'rainy' in weather_impact.index and weather_impact['rainy'] > 3:
            insights.append("🌧️ Chuva causa atrasos médios de +{:.1f} min".format(weather_impact['rainy']))
        
        # Análise de eficiência
        accuracy_3min = (np.abs(self.df['predicted_eta_min'] - self.df['actual_delivery_min']) <= 3).mean() * 100
        if accuracy_3min > 80:
            insights.append("🎯 Predições muito precisas (>80% dentro de ±3min)")
        elif accuracy_3min < 60:
            insights.append("📈 Predições precisam melhorar (<60% dentro de ±3min)")
        
        return {
            'summary_stats': {
                'avg_delivery_time': round(avg_delivery, 1),
                'late_percentage': round(late_percentage, 1),
                'prediction_accuracy': round(accuracy_3min, 1),
                'total_deliveries': len(self.df)
            },
            'insights': insights,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos dados"""
        recommendations = []
        
        # Análise de horários problemáticos
        hourly_late_rate = self.df.groupby('hour_of_day')['is_late'].mean()
        problematic_hours = hourly_late_rate[hourly_late_rate > 0.4].index.tolist()
        
        if problematic_hours:
            recommendations.append(
                f"Considere aumentar tempo estimado nos horários: {', '.join(map(str, problematic_hours))}h"
            )
        
        # Análise de distância
        long_distance_issues = self.df[self.df['distance_km'] > 3]['is_late'].mean()
        if long_distance_issues > 0.5:
            recommendations.append("Revisar estimativas para entregas >3km")
        
        # Análise de preparo
        high_prep_time = self.df[self.df['preparation_time_min'] > 20]['is_late'].mean()
        if high_prep_time > 0.4:
            recommendations.append("Otimizar processo de preparo para pedidos complexos")
        
        # Análise climática
        if 'rainy' in self.df['weather'].values:
            rainy_delay = self.df[self.df['weather'] == 'rainy']['delay_min'].mean()
            if rainy_delay > 3:
                recommendations.append("Adicionar buffer de tempo para dias chuvosos")
        
        return recommendations

def create_visualizations(analytics: DeliveryAnalytics, save_path: str = "ml_system/analytics/"):
    """Cria visualizações dos dados"""
    import os
    
    os.makedirs(save_path, exist_ok=True)
    
    if analytics.df.empty:
        print("Dados vazios - não é possível criar visualizações")
        return
    
    plt.style.use('seaborn-v0_8')
    
    # 1. Distribuição dos tempos de entrega
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.hist(analytics.df['actual_delivery_min'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title('Distribuição dos Tempos de Entrega')
    plt.xlabel('Tempo (minutos)')
    plt.ylabel('Frequência')
    
    # 2. Comparação ETA vs Real
    plt.subplot(2, 2, 2)
    plt.scatter(analytics.df['predicted_eta_min'], analytics.df['actual_delivery_min'], alpha=0.6)
    plt.plot([0, 60], [0, 60], 'r--', label='Linha Perfeita')
    plt.title('ETA Previsto vs Real')
    plt.xlabel('ETA Previsto (min)')
    plt.ylabel('Tempo Real (min)')
    plt.legend()
    
    # 3. Atrasos por horário
    plt.subplot(2, 2, 3)
    hourly_late = analytics.df.groupby('hour_of_day')['is_late'].mean() * 100
    plt.bar(hourly_late.index, hourly_late.values, color='coral')
    plt.title('Taxa de Atrasos por Horário')
    plt.xlabel('Hora do Dia')
    plt.ylabel('% de Atrasos')
    
    # 4. Impacto do clima
    plt.subplot(2, 2, 4)
    weather_impact = analytics.df.groupby('weather')['delay_min'].mean()
    plt.bar(weather_impact.index, weather_impact.values, 
            color=['gold', 'lightblue', 'lightcoral'])
    plt.title('Atraso Médio por Condição Climática')
    plt.xlabel('Condição')
    plt.ylabel('Atraso Médio (min)')
    
    plt.tight_layout()
    plt.savefig(f"{save_path}delivery_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Visualizações salvas em: {save_path}delivery_analysis.png")

if __name__ == "__main__":
    # Teste das análises
    analytics = DeliveryAnalytics()
    
    if not analytics.df.empty:
        # Métricas de erro
        predictions = analytics.df['predicted_eta_min'].tolist()
        actuals = analytics.df['actual_delivery_min'].tolist()
        error_metrics = analytics.calculate_error_metrics(predictions, actuals)
        
        print("📊 Métricas de Erro:")
        for metric, value in error_metrics.items():
            print(f"  {metric}: {value}")
        
        # Detectar anomalias
        anomalies = analytics.detect_anomalies()
        print(f"\n🚨 Anomalias detectadas: {len(anomalies)}")
        
        # Insights automáticos
        insights = analytics.generate_insights()
        print("\n💡 Insights:")
        for insight in insights['insights']:
            print(f"  • {insight}")
        
        print("\n📋 Recomendações:")
        for rec in insights['recommendations']:
            print(f"  • {rec}")
        
        # Criar visualizações
        try:
            create_visualizations(analytics)
        except Exception as e:
            print(f"Erro ao criar visualizações: {e}")
    
    else:
        print("❌ Nenhum dado encontrado para análise")