from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def get_regressors():
    return [
        ("RF", RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)),
        ("XGB", GradientBoostingRegressor(n_estimators=200, random_state=42)),
        ("KNN", Pipeline([("s", StandardScaler()), ("k", KNeighborsRegressor(n_neighbors=10))]))
    ]