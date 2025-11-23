from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def get_regressors():
    return [
        ("RF", RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)),
        ("XGB", GradientBoostingRegressor(n_estimators=200, random_state=42)),
        ("KNN", Pipeline([("s", StandardScaler()), ("k", KNeighborsRegressor(n_neighbors=10))])),
        # MLP: Rede Neural Clássica (Data-driven baseline para PINN)
        ("MLP", Pipeline([
            ("s", StandardScaler()), 
            ("net", MLPRegressor(hidden_layer_sizes=(64, 64, 64), activation="tanh", max_iter=2000, random_state=42))
        ])),
        # SVR: Support Vector Regression (Bom para funções suaves)
        ("SVR", Pipeline([("s", StandardScaler()), ("svm", SVR(kernel="rbf"))]))
    ]