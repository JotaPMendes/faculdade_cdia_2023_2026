"""
Sistema de retreinamento do modelo ML com dados reais coletados
"""

import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import os
from datetime import datetime

def retrain_model_with_data(ml_logs):
    """
    Retreina o modelo com novos dados coletados
    
    Args:
        ml_logs: Lista de logs ML do sistema
        
    Returns:
        float: Acurácia do modelo retreinado (R²)
    """
    
    print(f"🔄 Iniciando retreinamento com {len(ml_logs)} amostras...")
    
    # Converte logs em DataFrame
    df = pd.DataFrame(ml_logs)
    
    # Verifica se temos dados suficientes
    if len(df) < 5:
        raise ValueError(f"Dados insuficientes para treinamento: {len(df)} < 5")
    
    # Remove valores nulos ou inválidos
    df = df.dropna()
    df = df[df['actual_delivery_min'] > 0]  # Remove tempos inválidos
    df = df[df['distance_km'] > 0]         # Remove distâncias inválidas
    
    if len(df) < 3:
        raise ValueError("Dados válidos insuficientes após limpeza")
    
    print(f"📊 Dados limpos: {len(df)} amostras válidas")
    
    # Features básicas para o modelo
    features = [
        'distance_km',
        'hour_of_day', 
        'day_of_week',
        'item_count'
    ]
    
    # Verifica se todas as features estão presentes
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Features faltando: {missing_features}")
    
    # Prepara dados
    X = df[features].copy()
    y = df['actual_delivery_min']
    
    # Feature Engineering
    X['is_weekend'] = (X['day_of_week'] >= 5).astype(int)
    X['is_peak_hour'] = (
        ((X['hour_of_day'] >= 11) & (X['hour_of_day'] <= 14)) | 
        ((X['hour_of_day'] >= 18) & (X['hour_of_day'] <= 21))
    ).astype(int)
    
    # Categoriza distâncias
    X['distance_category'] = pd.cut(
        X['distance_km'], 
        bins=[0, 1, 3, 5, float('inf')], 
        labels=[0, 1, 2, 3]
    ).astype(int)
    
    # Interações entre features
    X['distance_x_items'] = X['distance_km'] * X['item_count']
    X['peak_x_distance'] = X['is_peak_hour'] * X['distance_km']
    
    print(f"🧪 Features preparadas: {list(X.columns)}")
    
    # Split dos dados (se temos poucos dados, usar menos para teste)
    test_size = min(0.3, max(0.1, len(X) * 0.2 / len(X)))
    
    if len(X) < 8:
        # Para datasets muito pequenos, usar validação simples
        X_train, X_test = X, X
        y_train, y_test = y, y
        print("⚠️ Dataset pequeno - usando validação in-sample")
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
    
    print(f"📈 Treinamento: {len(X_train)} amostras, Teste: {len(X_test)} amostras")
    
    # Configuração do modelo - adaptada para datasets pequenos
    n_estimators = min(100, max(10, len(X_train) * 2))
    max_depth = min(10, max(3, int(np.log2(len(X_train)))))
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=max(2, len(X_train) // 10),
        min_samples_leaf=max(1, len(X_train) // 20),
        random_state=42,
        n_jobs=-1
    )
    
    print(f"🌳 Modelo: {n_estimators} árvores, profundidade max: {max_depth}")
    
    # Treina modelo
    model.fit(X_train, y_train)
    
    # Avalia modelo
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Métricas
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    print(f"📊 Métricas de Treinamento:")
    print(f"   R² Train: {train_r2:.3f}, Test: {test_r2:.3f}")
    print(f"   MAE Train: {train_mae:.2f}min, Test: {test_mae:.2f}min") 
    print(f"   RMSE Train: {train_rmse:.2f}min, Test: {test_rmse:.2f}min")
    
    # Importância das features
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"🎯 Top 5 Features mais importantes:")
    for idx, row in feature_importance.head().iterrows():
        print(f"   {row['feature']}: {row['importance']:.3f}")
    
    # Cria pasta models se não existir
    os.makedirs("models", exist_ok=True)
    
    # Salva modelo atualizado
    model_path = "models/eta_model_retrained.pkl"
    joblib.dump(model, model_path)
    print(f"💾 Modelo salvo em: {model_path}")
    
    # Salva métricas detalhadas
    metrics = {
        'model_type': 'RandomForestRegressor',
        'train_r2': float(train_r2),
        'test_r2': float(test_r2),
        'train_mae': float(train_mae),
        'test_mae': float(test_mae),
        'train_rmse': float(train_rmse),
        'test_rmse': float(test_rmse),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'features_used': list(X.columns),
        'feature_importance': feature_importance.to_dict('records'),
        'model_params': {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
        },
        'trained_at': datetime.now().isoformat(),
        'data_quality': {
            'original_samples': len(ml_logs),
            'cleaned_samples': len(df),
            'avg_delivery_time': float(y.mean()),
            'std_delivery_time': float(y.std()),
            'min_delivery_time': float(y.min()),
            'max_delivery_time': float(y.max())
        }
    }
    
    metrics_path = "models/model_metrics.json"
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"📈 Métricas salvas em: {metrics_path}")
    
    # Salva também as features engineered para usar na predição
    feature_config = {
        'features': list(X.columns),
        'feature_engineering': {
            'is_weekend': 'day_of_week >= 5',
            'is_peak_hour': '(hour_of_day >= 11 & <= 14) | (hour_of_day >= 18 & <= 21)',
            'distance_category': 'cut(distance_km, bins=[0,1,3,5,inf])',
            'distance_x_items': 'distance_km * item_count', 
            'peak_x_distance': 'is_peak_hour * distance_km'
        }
    }
    
    with open("models/feature_config.json", 'w', encoding='utf-8') as f:
        json.dump(feature_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Retreinamento concluído com sucesso!")
    print(f"🎯 Acurácia final: {test_r2:.3f} (R²)")
    
    return test_r2

def load_retrained_model():
    """
    Carrega o modelo retreinado se existir, senão retorna None
    
    Returns:
        sklearn model ou None
    """
    retrained_path = "models/eta_model_retrained.pkl"
    
    if os.path.exists(retrained_path):
        print("🔄 Carregando modelo retreinado...")
        return joblib.load(retrained_path)
    else:
        print("⚠️ Modelo retreinado não encontrado, usando modelo padrão")
        return None

def predict_with_retrained_model(distance_km, day_of_week, hour_of_day, item_count):
    """
    Faz predição usando o modelo retreinado se disponível
    
    Args:
        distance_km: Distância em km
        day_of_week: Dia da semana (0-6)
        hour_of_day: Hora do dia (0-23)  
        item_count: Número de itens
        
    Returns:
        float: Tempo estimado em minutos
    """
    model = load_retrained_model()
    
    if model is None:
        # Fallback para algoritmo simples
        base_time = 15 + (distance_km * 8) + (item_count * 2)
        
        if hour_of_day in [11, 12, 13, 14, 18, 19, 20, 21]:
            base_time *= 1.3
            
        if day_of_week >= 5:
            base_time *= 1.1
            
        return max(5, int(base_time))
    
    # Carrega configuração das features
    feature_config_path = "models/feature_config.json"
    if os.path.exists(feature_config_path):
        with open(feature_config_path, 'r', encoding='utf-8') as f:
            feature_config = json.load(f)
        features = feature_config['features']
    else:
        # Features padrão se config não existir
        features = ['distance_km', 'hour_of_day', 'day_of_week', 'item_count',
                   'is_weekend', 'is_peak_hour', 'distance_category', 
                   'distance_x_items', 'peak_x_distance']
    
    # Prepara dados de entrada
    data = {
        'distance_km': distance_km,
        'hour_of_day': hour_of_day,
        'day_of_week': day_of_week, 
        'item_count': item_count
    }
    
    # Feature engineering
    data['is_weekend'] = 1 if day_of_week >= 5 else 0
    data['is_peak_hour'] = 1 if hour_of_day in [11,12,13,14,18,19,20,21] else 0
    
    if distance_km <= 1:
        data['distance_category'] = 0
    elif distance_km <= 3:
        data['distance_category'] = 1  
    elif distance_km <= 5:
        data['distance_category'] = 2
    else:
        data['distance_category'] = 3
        
    data['distance_x_items'] = distance_km * item_count
    data['peak_x_distance'] = data['is_peak_hour'] * distance_km
    
    # Converte para DataFrame com ordem das features
    X = pd.DataFrame([data])[features]
    
    # Predição
    prediction = model.predict(X)[0]
    
    return max(5, int(prediction))

if __name__ == "__main__":
    # Teste básico
    print("🧪 Testando sistema de retreinamento...")
    
    # Dados de exemplo para teste
    sample_logs = [
        {
            'distance_km': 2.5,
            'hour_of_day': 12,
            'day_of_week': 1,
            'item_count': 2,
            'actual_delivery_min': 25
        },
        {
            'distance_km': 1.2,
            'hour_of_day': 19,
            'day_of_week': 5,
            'item_count': 1,
            'actual_delivery_min': 18
        },
        {
            'distance_km': 4.8,
            'hour_of_day': 14,
            'day_of_week': 2,
            'item_count': 3,
            'actual_delivery_min': 45
        },
        {
            'distance_km': 3.1,
            'hour_of_day': 20,
            'day_of_week': 6,
            'item_count': 2,
            'actual_delivery_min': 35
        },
        {
            'distance_km': 1.8,
            'hour_of_day': 13,
            'day_of_week': 3,
            'item_count': 1,
            'actual_delivery_min': 22
        }
    ]
    
    try:
        accuracy = retrain_model_with_data(sample_logs)
        print(f"✅ Teste concluído! Acurácia: {accuracy:.3f}")
        
        # Teste de predição
        eta = predict_with_retrained_model(2.5, 1, 12, 2)
        print(f"🎯 Predição teste (2.5km, segunda, 12h, 2 itens): {eta} min")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")