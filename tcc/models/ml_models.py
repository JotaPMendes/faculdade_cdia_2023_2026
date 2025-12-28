import numpy as np
from sklearn.metrics import mean_absolute_error
from .regressors import get_regressors

def train_ml_models(X_train, y_train, X_test, y_test):
    """
    Treina vários modelos de ML clássico e retorna métricas e previsões.
    """
    regressors = get_regressors()
    metrics = {}
    preds = {}
    
    # Flatten y if needed (sklearn expects 1D array for regression usually)
    if y_train.ndim > 1 and y_train.shape[1] == 1:
        y_train = y_train.ravel()
    if y_test.ndim > 1 and y_test.shape[1] == 1:
        y_test = y_test.ravel()

    for name, model in regressors:
        print(f"  > Treinando {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        metrics[name] = mae
        preds[name] = y_pred
        print(f"    {name} MAE: {mae:.6f}")
        
    return metrics, preds
