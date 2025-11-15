import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ETAPredictor:
    """
    Preditor de ETA usando Machine Learning avançado em Python
    """
    
    def __init__(self, data_path: str = "../src/data/historical_deliveries.json"):
        self.data_path = data_path
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.is_trained = False
        
        # Carregar dados e treinar modelo
        self.load_data()
        self.train_model()
    
    def load_data(self) -> pd.DataFrame:
        """Carrega e processa os dados históricos"""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            self.df = pd.DataFrame(data)
            print(f"✅ Dados carregados: {len(self.df)} registros")
            return self.df
            
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {self.data_path}")
            # Criar dados mock se arquivo não existir
            self.create_mock_data()
            return self.df
    
    def create_mock_data(self):
        """Cria dados sintéticos para treinamento"""
        np.random.seed(42)
        n_samples = 200
        
        # Gerar dados sintéticos mais realistas
        data = []
        for i in range(n_samples):
            distance = np.random.uniform(0.5, 5.0)
            hour = np.random.randint(6, 23)
            day_of_week = np.random.randint(0, 7)
            weather = np.random.choice(['sunny', 'cloudy', 'rainy'], p=[0.6, 0.3, 0.1])
            traffic = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
            prep_time = np.random.uniform(8, 25)
            
            # Calcular ETA base
            base_eta = prep_time + (distance * 8)  # ~8 min por km
            
            # Ajustes baseados em condições
            if hour >= 18 and hour <= 20:  # Rush hour
                base_eta *= 1.3
            if weather == 'rainy':
                base_eta *= 1.2
            if traffic == 3:
                base_eta *= 1.25
            if day_of_week in [5, 6]:  # Weekend
                base_eta *= 1.1
                
            # Adicionar ruído realista
            actual_eta = base_eta + np.random.normal(0, 3)
            actual_eta = max(5, actual_eta)  # Mínimo 5 min
            
            predicted_eta = base_eta + np.random.normal(0, 2)
            predicted_eta = max(5, predicted_eta)
            
            delay = actual_eta - predicted_eta
            is_late = delay > 5
            
            data.append({
                'distance_km': round(distance, 1),
                'predicted_eta_min': round(predicted_eta),
                'actual_delivery_min': round(actual_eta),
                'day_of_week': day_of_week,
                'hour_of_day': hour,
                'weather': weather,
                'traffic_level': traffic,
                'preparation_time_min': round(prep_time),
                'is_late': is_late,
                'delay_min': round(delay, 1)
            })
        
        self.df = pd.DataFrame(data)
        print(f"✅ Dados sintéticos criados: {len(self.df)} registros")
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engenharia de features avançada"""
        df_processed = df.copy()
        
        # Features temporais
        df_processed['is_weekend'] = df_processed['day_of_week'].isin([0, 6]).astype(int)
        df_processed['is_rush_hour'] = ((df_processed['hour_of_day'] >= 12) & 
                                       (df_processed['hour_of_day'] <= 14) |
                                       (df_processed['hour_of_day'] >= 18) & 
                                       (df_processed['hour_of_day'] <= 20)).astype(int)
        
        # Features de interação
        df_processed['distance_x_traffic'] = df_processed['distance_km'] * df_processed['traffic_level']
        df_processed['prep_time_x_distance'] = df_processed['preparation_time_min'] * df_processed['distance_km']
        
        # Normalização de horário (circular)
        df_processed['hour_sin'] = np.sin(2 * np.pi * df_processed['hour_of_day'] / 24)
        df_processed['hour_cos'] = np.cos(2 * np.pi * df_processed['hour_of_day'] / 24)
        
        # Normalização de dia da semana (circular)
        df_processed['day_sin'] = np.sin(2 * np.pi * df_processed['day_of_week'] / 7)
        df_processed['day_cos'] = np.cos(2 * np.pi * df_processed['day_of_week'] / 7)
        
        # Encoding do weather
        if 'weather' not in self.label_encoders:
            self.label_encoders['weather'] = LabelEncoder()
            df_processed['weather_encoded'] = self.label_encoders['weather'].fit_transform(df_processed['weather'])
        else:
            df_processed['weather_encoded'] = self.label_encoders['weather'].transform(df_processed['weather'])
        
        return df_processed
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara features para treinamento"""
        df_processed = self.feature_engineering(df)
        
        # Selecionar features
        feature_columns = [
            'distance_km', 'preparation_time_min', 'traffic_level',
            'weather_encoded', 'is_weekend', 'is_rush_hour',
            'distance_x_traffic', 'prep_time_x_distance',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
        ]
        
        self.feature_names = feature_columns
        X = df_processed[feature_columns].values
        y = df_processed['actual_delivery_min'].values
        
        return X, y
    
    def train_model(self):
        """Treina o modelo de ML"""
        print("🤖 Iniciando treinamento do modelo...")
        
        # Preparar dados
        X, y = self.prepare_features(self.df)
        
        # Split dos dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Normalização
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Treinar múltiplos modelos e escolher o melhor
        models = {
            'Linear Regression': LinearRegression(),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        }
        
        best_score = float('-inf')
        best_model = None
        best_name = ""
        
        for name, model in models.items():
            # Cross-validation
            if name == 'Linear Regression':
                scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            score = scores.mean()
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            print(f"📊 {name}:")
            print(f"   R² Score: {score:.3f} (±{scores.std()*2:.3f})")
            print(f"   MAE: {mae:.2f} min")
            print(f"   RMSE: {rmse:.2f} min")
            print(f"   R² Test: {r2:.3f}")
            
            if score > best_score:
                best_score = score
                best_model = model
                best_name = name
        
        self.model = best_model
        self.model_name = best_name
        self.is_trained = True
        
        print(f"🏆 Melhor modelo: {best_name} (R² = {best_score:.3f})")
        
        # Salvar modelo
        self.save_model()
    
    def predict_eta(self, input_data: Dict) -> Dict:
        """Faz predição de ETA"""
        if not self.is_trained:
            raise ValueError("Modelo não foi treinado")
        
        # Converter input para DataFrame
        df_input = pd.DataFrame([input_data])
        df_processed = self.feature_engineering(df_input)
        X = df_processed[self.feature_names].values
        
        # Aplicar escalonamento se for modelo linear
        if self.model_name == 'Linear Regression':
            X = self.scaler.transform(X)
        
        # Predição
        eta_prediction = self.model.predict(X)[0]
        eta_prediction = max(5, round(eta_prediction))  # Mínimo 5 min
        
        # Calcular fatores de risco
        risk_factors = self.get_risk_factors(input_data)
        
        # Calcular confiança baseada nos fatores de risco
        confidence = max(60, 95 - len(risk_factors) * 8)
        
        return {
            'eta_minutes': int(eta_prediction),
            'confidence': confidence,
            'risk_factors': risk_factors,
            'model_used': self.model_name
        }
    
    def get_risk_factors(self, input_data: Dict) -> List[str]:
        """Identifica fatores de risco"""
        risks = []
        
        if input_data['distance_km'] > 3.5:
            risks.append('🚗 Distância longa (>3.5km)')
        
        if input_data['traffic_level'] >= 3:
            risks.append('🚦 Trânsito intenso')
        
        if input_data['weather'] == 'rainy':
            risks.append('🌧️ Condições climáticas adversas')
        
        hour = input_data['hour_of_day']
        if (12 <= hour <= 14) or (18 <= hour <= 20):
            risks.append('⏰ Horário de pico')
        
        if input_data['preparation_time_min'] > 20:
            risks.append('👨‍🍳 Tempo de preparo elevado')
        
        if input_data['day_of_week'] in [5, 6]:  # Sexta/Sábado
            risks.append('🎉 Final de semana (maior demanda)')
        
        return risks
    
    def get_model_metrics(self) -> Dict:
        """Calcula métricas do modelo"""
        if not self.is_trained:
            return {}
        
        X, y = self.prepare_features(self.df)
        
        if self.model_name == 'Linear Regression':
            X = self.scaler.transform(X)
        
        y_pred = self.model.predict(X)
        
        # Calcular métricas
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        
        # Calcular precisão (predições dentro de ±3 min)
        accurate_predictions = np.abs(y - y_pred) <= 3
        accuracy = np.mean(accurate_predictions) * 100
        
        # Calcular atrasos
        late_orders = np.sum(self.df['is_late'])
        late_percentage = (late_orders / len(self.df)) * 100
        
        return {
            'accuracy': round(accuracy, 1),
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'r2_score': round(r2, 3),
            'late_percentage': round(late_percentage, 1),
            'total_predictions': len(self.df),
            'model_name': self.model_name
        }
    
    def save_model(self, path: str = "eta_model.pkl"):
        """Salva o modelo treinado"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'model_name': self.model_name
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Modelo salvo em: {path}")
    
    def load_model(self, path: str = "eta_model.pkl"):
        """Carrega modelo salvo"""
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_names = model_data['feature_names']
            self.model_name = model_data['model_name']
            self.is_trained = True
            
            print(f"📁 Modelo carregado de: {path}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Modelo não encontrado: {path}")
            return False

# Singleton pattern
_predictor_instance = None

def get_eta_predictor() -> ETAPredictor:
    """Retorna instância singleton do preditor"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ETAPredictor()
    return _predictor_instance

if __name__ == "__main__":
    # Teste do modelo
    predictor = get_eta_predictor()
    
    # Exemplo de predição
    test_input = {
        'distance_km': 2.5,
        'day_of_week': 1,  # Segunda
        'hour_of_day': 19,  # 19h
        'weather': 'rainy',
        'traffic_level': 3,
        'preparation_time_min': 15
    }
    
    result = predictor.predict_eta(test_input)
    print("\n🎯 Teste de Predição:")
    print(f"ETA: {result['eta_minutes']} minutos")
    print(f"Confiança: {result['confidence']}%")
    print(f"Fatores de risco: {result['risk_factors']}")
    
    # Métricas do modelo
    metrics = predictor.get_model_metrics()
    print("\n📊 Métricas do Modelo:")
    for key, value in metrics.items():
        print(f"{key}: {value}")